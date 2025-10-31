import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '5m', target: 8 },
    { duration: '5m', target: 20 },
    { duration: '5m', target: 8 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<1500'],
  },
};

export default function () {
  const token = __ENV.BEARER;
  const res = http.get(`${__ENV.BASE_URL}/dev/system-health?userId=${__ENV.USER}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}
