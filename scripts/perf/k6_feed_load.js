import http from 'k6/http';
import { check, sleep } from 'k6';

// k6 Load Test Script for FashX Discovery Feed (GET /api/v1/feed)
// Target: Concurrency ramp to 100 VUs, 50 req/sec, P95 < 350ms, Error rate < 1%

export const options = {
  stages: [
    { duration: '30s', target: 20 },  // Warm up
    { duration: '1m', target: 50 },   // Sustained pilot load (50 RPS)
    { duration: '30s', target: 100 },  // Peak concurrent stress test
    { duration: '30s', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<350', 'p(99)<600'], // P95 latency SLA < 350ms, P99 < 600ms
    http_req_failed: ['rate<0.01'],                  // < 1% error rate
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const TEST_TOKEN = __ENV.TEST_TOKEN || 'test-bearer-token';

export default function () {
  const params = {
    headers: {
      'Authorization': `Bearer ${TEST_TOKEN}`,
      'Content-Type': 'application/json',
      'X-Request-ID': `k6-${__VU}-${__ITER}`,
    },
    timeout: '5s',
  };

  const res = http.get(`${BASE_URL}/api/v1/feed?limit=20`, params);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response body has items': (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body.items) && body.items.length > 0;
      } catch (e) {
        return false;
      }
    },
    'latency under 350ms': (r) => r.timings.duration < 350,
  });

  sleep(1);
}
