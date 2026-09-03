/**
 * k6 yük testi — doküman yükleme (hedef: 100 eşzamanlı).
 *
 * Çalıştırma:
 *   k6 run -e BASE_URL=http://localhost:8000 infra/loadtest/upload.js
 */
import { check, sleep } from "k6";
import http from "k6/http";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const PASSWORD = "Tr0ub4dour&3xample!";

export const options = {
  scenarios: {
    upload: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "30s", target: 25 },
        { duration: "1m", target: 100 },
        { duration: "1m", target: 100 },
        { duration: "30s", target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.02"],
    "http_req_duration{scenario:upload}": ["p(95)<3000"],
  },
};

function jsonPost(path, body, token) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  return http.post(`${BASE_URL}${path}`, JSON.stringify(body), { headers });
}

export function setup() {
  return { runId: `${Date.now()}` };
}

export default function (data) {
  const email = `load-${data.runId}-${__VU}-${__ITER}@example.com`;

  const registered = jsonPost("/api/v1/auth/register", {
    email,
    password: PASSWORD,
  });
  check(registered, { "register 201": (r) => r.status === 201 });
  if (registered.status !== 201) return;

  const orgId = registered.json("organization_id");
  const token = jsonPost("/api/v1/auth/login", {
    email,
    password: PASSWORD,
  }).json("access_token");

  const upload = http.post(
    `${BASE_URL}/api/v1/documents/${orgId}/upload`,
    {
      file: http.file(
        `Yuk testi dokumani ${__VU}-${__ITER}. Toplam tutar 100000 TL.`,
        "yuk.txt",
        "text/plain",
      ),
    },
    { headers: { Authorization: `Bearer ${token}` } },
  );

  check(upload, {
    "upload 201": (r) => r.status === 201,
    "processed": (r) => r.status === 201 && r.json("status") === "ready",
  });

  sleep(1);
}
