/**
 * k6 yük testi — AI sohbeti ve vektör arama (hedef: 50 eşzamanlı).
 *
 * Çalıştırma:
 *   k6 run -e BASE_URL=http://localhost:8000 infra/loadtest/chat.js
 */
import { check, sleep } from "k6";
import http from "k6/http";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const PASSWORD = "Tr0ub4dour&3xample!";
const QUESTIONS = [
  "Bu dokümanda toplam tutar nedir?",
  "Teslim süresi kaç gündür?",
  "Sorumlu kişi kimdir?",
];

export const options = {
  scenarios: {
    chat: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "30s", target: 20 },
        { duration: "1m", target: 50 },
        { duration: "1m", target: 50 },
        { duration: "30s", target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.02"],
    "http_req_duration{name:chat}": ["p(95)<5000"],
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
  const email = `chat-${data.runId}-${__VU}-${__ITER}@example.com`;

  const registered = jsonPost("/api/v1/auth/register", {
    email,
    password: PASSWORD,
  });
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
        "Sozlesme 01.03.2025 tarihinde imzalandi. Toplam tutar 250000 TL. " +
          "Teslim suresi 90 gundur. Sorumlu Ahmet Demir.",
        "sozlesme.txt",
        "text/plain",
      ),
    },
    { headers: { Authorization: `Bearer ${token}` } },
  );
  if (upload.status !== 201) return;

  const documentId = upload.json("id");
  const question = QUESTIONS[__ITER % QUESTIONS.length];

  const answer = http.post(
    `${BASE_URL}/api/v1/ai/${orgId}/chat`,
    JSON.stringify({ document_id: documentId, question }),
    {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      tags: { name: "chat" },
    },
  );

  check(answer, {
    "chat 200": (r) => r.status === 200,
    "cevap uretildi": (r) => r.status === 200 && r.json("answer") !== "",
  });

  sleep(1);
}
