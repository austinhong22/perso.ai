export type AskResponse = {
  answer: string;
  score: number;
  matched_question: string;
  sources: string[];
  topk?: Array<{ question: string; score: number }>;
};

export async function ask(
  query: string,
  signal?: AbortSignal
): Promise<AskResponse> {
  const base =
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000); // 30초 타임아웃

  try {
    const resp = await fetch(`${base}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query }),
      signal: signal || controller.signal,
    });

    clearTimeout(timeoutId);

    if (!resp.ok) {
      if (resp.status === 400) {
        throw new Error("잘못된 요청입니다. 질문을 확인해주세요.");
      }
      if (resp.status === 500) {
        throw new Error("서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.");
      }
      throw new Error(`요청 실패 (${resp.status})`);
    }

    const data: AskResponse = await resp.json();
    return data;
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof Error) {
      if (error.name === "AbortError") {
        throw new Error("요청 시간이 초과되었습니다. 다시 시도해주세요.");
      }
      throw error;
    }

    throw new Error("알 수 없는 오류가 발생했습니다.");
  }
}



