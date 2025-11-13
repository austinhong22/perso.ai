'use client';

import { useState } from "react";
import { ask } from "../lib/api";

export default function Chat() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [sources, setSources] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  async function onAsk() {
    setLoading(true);
    try {
      const res = await ask(question);
      setAnswer(res.answer);
      setSources(res.sources || []);
    } catch {
      setAnswer("요청 중 오류가 발생했습니다.");
      setSources([]);
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
          {sources.length > 0 && (
            <div style={{ marginTop: 12, fontSize: "0.9em", color: "#666" }}>
              <strong>출처:</strong>
              {sources.map((src, idx) => (
                <div key={idx} style={{ marginTop: 4 }}>{src}</div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}



