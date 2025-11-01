#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
fi

pytest lambda/tests/test_temporal_analytics.py lambda/tests/test_knowledge_graph_entities.py lambda/tests/test_wiki.py

echo "✅ Phase 3 analytics, knowledge graph, and wiki verification complete."
