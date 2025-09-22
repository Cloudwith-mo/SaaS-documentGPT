import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

// ---- CONFIG (override with env vars) ----
const API_BASE = __ENV.API_BASE || (() => { throw new Error('API_BASE env var required (e.g. https://api.example.com)'); })();
const CHAT_PATH = __ENV.CHAT_PATH || '/chat';
const AUTH_TYPE = __ENV.AUTH_TYPE || 'bearer'; // 'bearer' or 'x-api-key' or 'none'
const API_KEY = __ENV.API_KEY || '';
const DOC_IDS = (__ENV.DOC_IDS && JSON.parse(__ENV.DOC_IDS)) || ['test-doc-1']; // JSON array string
const RPS = Number(__ENV.RPS || 20); // requests per second during steady state
const DURATION = __ENV.DURATION || '5m'; // steady duration
const RAMP_DURATION = __ENV.RAMP_DURATION || '30s'; // ramp-up time
const MAX_VUS = Number(__ENV.MAX_VUS || 200);
const PREALLOC_VUS = Number(__ENV.PREALLOC_VUS || 50);
const ASK_TEMPLATES = (__ENV.ASK_TEMPLATES && JSON.parse(__ENV.ASK_TEMPLATES)) || [
  'Give a one-sentence summary of the document.',
  'What is the main point of the document?',
  'List 3 key facts from the document.',
  'Is there an action item mentioned? If so, what is it?',
  'Provide a short FAQ-style answer for a common user question about the document.'
];

// Custom metric for response size (optional)
const respSizeTrend = new Trend('response_size_bytes');

// ---- k6 OPTIONS ----
export let options = {
  scenarios: {
    ramp_up: {
      executor: 'ramping-arrival-rate',
      startRate: Math.max(1, Math.round(RPS * 0.1)),
      timeUnit: '1s',
      preAllocatedVUs: PREALLOC_VUS,
      maxVUs: MAX_VUS,
      stages: [
        { target: Math.max(1, Math.round(RPS * 0.25)), duration: RAMP_DURATION },
      ],
      exec: 'steady_runner',
    },
    steady: {
      executor: 'constant-arrival-rate',
      rate: RPS,
      timeUnit: '1s',
      duration: DURATION,
      preAllocatedVUs: PREALLOC_VUS,
      maxVUs: MAX_VUS,
      exec: 'steady_runner',
    },
  },
  thresholds: {
    // Fail the test if too many failed requests or high latency
    'http_req_failed': ['rate<0.01'],        // <1% errors
    'http_req_duration': ['p(95)<1200'],     // 95th percentile < 1200 ms (customize)
    'checks': ['rate>0.99'],                 // >99% checks passing
  },
  // optional: increase default DNS/timeout settings here if needed
};

// ---- helper functions ----
function pickQuestion() {
  // pick a random template and occasionally append doc-specific ask
  const t = ASK_TEMPLATES[Math.floor(Math.random() * ASK_TEMPLATES.length)];
  // 20% chance to ask an explicit "quote the source" style prompt to test citations
  if (Math.random() < 0.2) {
    return `${t} Please quote the source file name and page if available.`;
  }
  return t;
}

function pickDocId() {
  // uniform random doc selection
  return DOC_IDS[Math.floor(Math.random() * DOC_IDS.length)];
}

function buildHeaders() {
  const h = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
  if (AUTH_TYPE === 'bearer' && API_KEY) {
    h['Authorization'] = `Bearer ${API_KEY}`;
  } else if (AUTH_TYPE === 'x-api-key' && API_KEY) {
    h['x-api-key'] = API_KEY;
  }
  return h;
}

// ---- main execution function used by scenarios ----
export function steady_runner() {
  const docId = pickDocId();
  const question = pickQuestion();
  const url = `${API_BASE}${CHAT_PATH}`;

  const payload = JSON.stringify({ question, docId });

  const res = http.post(url, payload, { headers: buildHeaders(), tags: { endpoint: 'chat', docId } });

  // basic checks and metrics
  const ok = check(res, {
    'status is 200': (r) => r.status === 200,
    'response is json': (r) => {
      try { return typeof r.json() === 'object'; } catch (e) { return false; }
    },
    'answer exists': (r) => {
      try {
        const j = r.json();
        return j && j.answer && j.answer.length > 5;
      } catch (e) { return false; }
    }
  });

  // record response size and optionally log occasional failures
  respSizeTrend.add(res.body ? res.body.length : 0);

  if (!ok) {
    // lightweight logging for triage in k6 output
    console.error(`FAIL: status=${res.status} doc=${docId} q="${question.substring(0,60)}..."`);
  }

  // small randomized think time to emulate users (0.2–1.5s)
  sleep(0.2 + Math.random() * 1.3);
}