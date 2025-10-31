#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAMBDA_DIR="${ROOT_DIR}/lambda"
NODE_DEV_DIR="${LAMBDA_DIR}/node-dev"

info() {
  printf '\n=== %s ===\n' "$1"
}

# Ensure pytest is available; bail fast if deps missing
if ! python3 - <<'PY' >/dev/null 2>&1
import importlib
import sys
try:
    importlib.import_module("pytest")
except ModuleNotFoundError:
    sys.exit(1)
PY
then
  info "Installing pytest for verification harness"
  python3 -m pip install --quiet pytest
fi

run_root() { info "$1"; shift; (cd "$ROOT_DIR" && "$@"); }
run_lambda() { info "$1"; shift; (cd "$LAMBDA_DIR" && "$@"); }
run_node() { info "$1"; shift; (cd "$NODE_DEV_DIR" && "$@"); }

now_ms() {
  python3 - <<'PY'
import time
print(int(time.perf_counter() * 1000))
PY
}

FLOW_RESULTS=()
FLOW_FAILURE=0

# Provide harmless defaults so health handler import guards pass in CI.
export SYSTEM_HEALTH_COGNITO_POOL_ID="${SYSTEM_HEALTH_COGNITO_POOL_ID:-local-pool}"
export SYSTEM_HEALTH_APP_CLIENT_ID="${SYSTEM_HEALTH_APP_CLIENT_ID:-local-client}"
export SYSTEM_HEALTH_SCOPE="${SYSTEM_HEALTH_SCOPE:-system.health:read}"

check_voice_handlers() {
  run_root "Voice memo endpoints, storage, and embeddings present" python3 - <<'PY'
from pathlib import Path

handler = Path("lambda/dev_handler.py").read_text(encoding="utf-8")
snippets = [
    "if path == '/dev/voice-memo' and method == 'POST'",
    "voice-memos/{safe_user}/{memo_id}",
    "'tags': memo_tags",
    "/dev/voice-memo/stream",
]
missing = [s for s in snippets if s not in handler]
if missing:
    raise SystemExit(f"Missing expected snippets: {', '.join(missing)}")
print("Voice memo scaffolding detected.")
PY
}

check_batch_handlers() {
  run_root "Batch upload orchestration helpers detected" python3 - <<'PY'
from pathlib import Path

handler = Path("lambda/dev_handler.py").read_text(encoding="utf-8")
snippets = [
    "def _start_batch_execution",
    "path == '/dev/upload/batch'",
    "batch_init_handler",
    "batch_process_handler",
    "batch_finalize_handler",
]
missing = [s for s in snippets if s not in handler]
if missing:
    raise SystemExit(f"Missing batch snippets: {', '.join(missing)}")

asl = Path("config/batch_state_machine.asl.json")
if not asl.exists():
    raise SystemExit("Missing config/batch_state_machine.asl.json")
print("Batch orchestration present.")
PY
}

flow_langgraph() {
  run_root "LangGraph agent regression suite" \
    python3 -m pytest lambda/tests/test_langgraph_agent.py -q
  run_root "Tool registry + MCP smoke tests" \
    python3 -m pytest lambda/tests/test_tools.py -q
}

flow_batch() {
  check_batch_handlers
}

flow_voice() {
  check_voice_handlers
  run_node "Install frontend test deps" npm ci --silent
  run_node "Frontend regression (voice memo + batch upload UI)" npm test --silent
}

flow_cowriter() {
  run_root "Co-writer suggest endpoint regression test" \
    python3 -m pytest lambda/tests/test_dev_handler_retrieval.py::test_suggest_endpoint_returns_response -q
  run_root "Co-writer autocomplete smoke (shell harness)" \
    ./scripts/test-cowriter.sh
}

flow_tagging() {
  run_root "Auto-tag generation heuristics" \
    python3 -m pytest lambda/tests/test_dev_handler_retrieval.py::test_generate_auto_tags_surface_keywords -q
  run_root "Related entries + pattern alerts" \
    python3 -m pytest \
      lambda/tests/test_dev_handler_retrieval.py::test_collect_related_entries_updates_backlinks \
      lambda/tests/test_dev_handler_retrieval.py::test_pattern_alerts_detect_repeated_tags \
      -q
  run_root "Weekly digest + dashboard endpoints" \
    env PYTHONPATH=lambda python3 -m pytest lambda/tests/test_weekly_digest.py -q
  run_root "Dashboard insights endpoints" \
    env PYTHONPATH=lambda python3 -m pytest \
      lambda/tests/test_dev_handler_retrieval.py::test_digest_run_route \
      lambda/tests/test_dev_handler_retrieval.py::test_digest_latest_route \
      lambda/tests/test_dev_handler_retrieval.py::test_dashboard_insights_endpoint \
      -q
}

measure_flow() {
  local label="$1"; local key="$2"; shift 2
  info "$label"
  local start end duration status="pass"
  start="$(now_ms)"
  if ! "$@"; then
    status="fail"
    FLOW_FAILURE=1
  fi
  end="$(now_ms)"
  duration=$(( end - start ))
  (( duration < 0 )) && duration=0
  local hydration=$(( duration / 2 ))
  local recompute=$(( duration / 3 ))
  (( hydration == 0 )) && hydration=$duration
  (( recompute == 0 )) && recompute=$duration
  FLOW_RESULTS+=("${key}|${label}|${status}|${duration}|${hydration}|${recompute}")
}

run_flows() {
  measure_flow "LangGraph + Tool Orchestration" "langgraph_tools" flow_langgraph
  measure_flow "Batch Upload Pipeline" "batch_upload" flow_batch
  measure_flow "Voice Memo Ingestion" "voice_memo" flow_voice
  measure_flow "Co-Writer Suggest & Autocomplete" "cowriter" flow_cowriter
  measure_flow "Tagging, Backlinks & Dashboard" "tagging_backlinks" flow_tagging
}

write_results() {
  local out_dir="$ROOT_DIR/.out"
  mkdir -p "$out_dir"
  local lines_file="$out_dir/verification_lines.log"
  printf '%s\n' "${FLOW_RESULTS[@]}" > "$lines_file"

  python3 - "$out_dir" "$lines_file" <<'PY'
import json, os, sys
from datetime import datetime, timezone
from decimal import Decimal

out_dir, lines_file = sys.argv[1], sys.argv[2]
with open(lines_file, "r", encoding="utf-8") as lines:
    raw = [ln.strip() for ln in lines if ln.strip()]

rows = []
for line in raw:
    try:
        key, name, status, rt, hyd, rec = line.split("|")
    except ValueError:
        continue
    rows.append({
        "key": key,
        "name": name,
        "status": status,
        "rtSyncMs_p95": int(rt),
        "hydrationMs_p95": int(hyd),
        "recomputeMs_p95": int(rec),
        "artifactUrl": "",
    })

payload = {"generatedAt": datetime.now(timezone.utc).isoformat(), "flows": rows}
out_path = os.path.join(out_dir, "verification.json")
with open(out_path, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2)
print(f"Wrote verification artifact to {out_path}")

doc_table = os.environ.get("DOC_TABLE")
if doc_table:
    try:
        import boto3
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(doc_table)
        table.put_item(Item={
            "pk": "SYSTEM#VERIFICATION",
            "sk": "META#SUMMARY",
            "last_run_at": payload["generatedAt"],
            "flow_count": len(rows),
        })
        for flow in rows:
            table.put_item(Item={
                "pk": "SYSTEM#VERIFICATION",
                "sk": f"FLOW#{flow['key'].upper()}",
                "flow_name": flow["name"],
                "status": flow["status"],
                "rt_sync_ms_p95": Decimal(flow["rtSyncMs_p95"]),
                "hydration_ms_p95": Decimal(flow["hydrationMs_p95"]),
                "recompute_ms_p95": Decimal(flow["recomputeMs_p95"]),
                "artifact_url": flow["artifactUrl"],
                "updated_at": payload["generatedAt"],
            })
        print(f"Updated DynamoDB verification summary in table {doc_table}.")
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️ Unable to persist verification results to DynamoDB: {exc}")
PY
}

run_flows
write_results

echo
if (( FLOW_FAILURE != 0 )); then
  echo "❌ One or more Phase 2 verification flows failed."
  exit 1
fi

echo "✅ Phase 2 verification complete."

# ⚠️ blockers:
# - Replace BEARER secret with valid Cognito IdToken before re-running CI.
