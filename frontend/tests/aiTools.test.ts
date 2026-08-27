import { describe, expect, it } from "vitest";

import { jobResultText, quizQuestions } from "@/features/ai/tools-api";
import type { AIJob } from "@/types/api";

function makeJob(overrides: Partial<AIJob>): AIJob {
  return {
    id: "1",
    document_id: "d1",
    type: "summary",
    status: "done",
    params: null,
    result: null,
    error: null,
    tokens_used: 0,
    cache_hit: false,
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("jobResultText", () => {
  it("returns plain text results as-is", () => {
    expect(jobResultText(makeJob({ result: { text: "Özet" } }))).toBe("Özet");
  });

  it("stringifies structured results", () => {
    const out = jobResultText(makeJob({ result: { dates: ["2025"] } }));
    expect(out).toContain("dates");
  });

  it("returns empty string when there is no result", () => {
    expect(jobResultText(makeJob({ result: null }))).toBe("");
  });
});

describe("quizQuestions", () => {
  it("extracts the questions array", () => {
    const job = makeJob({
      type: "quiz",
      result: {
        questions: [
          {
            type: "true_false",
            question: "Doğru mu?",
            options: ["Doğru", "Yanlış"],
            answer: "Doğru",
          },
        ],
      },
    });
    expect(quizQuestions(job)).toHaveLength(1);
  });

  it("returns an empty array for malformed results", () => {
    expect(quizQuestions(makeJob({ type: "quiz", result: {} }))).toEqual([]);
  });
});
