import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '1m', target: 5 },
  ],
};

export default function () {
  const token = __ENV.BEARER;
  const res = http.get(`${__ENV.BASE_URL}/dev/system-health?userId=${__ENV.USER}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  check(res, { 'status < 500': (r) => r.status < 500 });
  sleep(1);
}
