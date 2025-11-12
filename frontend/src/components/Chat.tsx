'use client';

import { useState } from "react";
import { ask } from "../lib/api";

export default function Chat() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onAsk() {
    setLoading(true);
    try {
      const res = await ask(question);
      setAnswer(res.answer);
    } catch {
      setAnswer("요청 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="질문을 입력하세요"
          style={{ flex: 1, padding: 8 }}
        />
        <button onClick={onAsk} disabled={loading || !question}>
          {loading ? "질의 중..." : "질의"}
        </button>
      </div>
      {answer && (
        <div style={{ marginTop: 16 }}>
          <strong>답변</strong>
          <div>{answer}</div>
        </div>
      )}
    </div>
  );
}


