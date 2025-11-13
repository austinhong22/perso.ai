"use client";

import { useState, useRef, useEffect } from "react";
import styles from "./ChatContainer.module.css";
import MessageList from "./MessageList";
import ChatInput from "./ChatInput";
import { ask } from "../lib/api";

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  score?: number;
  timestamp: Date;
};

export default function ChatContainer() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Reset handler: 로고 클릭 시 초기 화면으로 복귀
  useEffect(() => {
    const handleReset = () => {
      setMessages([]);
      setError(null);
      if (typeof window !== "undefined") {
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    };
    window.addEventListener("perso:reset-chat", handleReset);
    return () => window.removeEventListener("perso:reset-chat", handleReset);
  }, []);

  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: content.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await ask(content.trim());

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.answer,
        sources: response.sources,
        score: response.score,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "요청 중 오류가 발생했습니다. 다시 시도해주세요."
      );

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div id="chat" className={styles.chatContainer}>
      <div className={styles.messagesWrapper}>
        {messages.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>
              <svg
                width="96"
                height="96"
                viewBox="0 0 120 120"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                {/* 외곽 링 - 희미한 배경 */}
                <circle cx="60" cy="60" r="52" stroke="url(#bgRingEmpty)" strokeWidth="0.5" opacity="0.08" fill="none" />
                <circle cx="60" cy="60" r="46" stroke="url(#bgRingEmpty)" strokeWidth="0.5" opacity="0.05" fill="none" />
                
                {/* 불완전한 원 - 글로우 레이어 */}
                <path
                  d="M 95 45 A 35 35 0 1 1 45 25"
                  stroke="url(#glowGradientEmpty)"
                  strokeWidth="12"
                  strokeLinecap="round"
                  fill="none"
                  opacity="0.25"
                  filter="url(#blurEmpty)"
                >
                  <animateTransform
                    attributeName="transform"
                    attributeType="XML"
                    type="rotate"
                    from="0 60 60"
                    to="360 60 60"
                    dur="8s"
                    repeatCount="indefinite"
                  />
                </path>
                
                {/* 불완전한 원 - 메인 */}
                <path
                  d="M 95 45 A 35 35 0 1 1 45 25"
                  stroke="url(#mainGradientEmpty)"
                  strokeWidth="7"
                  strokeLinecap="round"
                  fill="none"
                >
                  <animateTransform
                    attributeName="transform"
                    attributeType="XML"
                    type="rotate"
                    from="0 60 60"
                    to="360 60 60"
                    dur="8s"
                    repeatCount="indefinite"
                  />
                </path>
                
                <defs>
                  {/* 배경 링 그라데이션 */}
                  <linearGradient id="bgRingEmpty" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#6366f1" />
                    <stop offset="100%" stopColor="#d946ef" />
                  </linearGradient>
                  
                  {/* 메인 그라데이션 */}
                  <linearGradient id="mainGradientEmpty" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#6366f1" />
                    <stop offset="50%" stopColor="#8b5cf6" />
                    <stop offset="100%" stopColor="#d946ef" />
                  </linearGradient>
                  
                  {/* 글로우 그라데이션 */}
                  <linearGradient id="glowGradientEmpty" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#6366f1" />
                    <stop offset="100%" stopColor="#d946ef" />
                  </linearGradient>
                  
                  {/* 블러 필터 */}
                  <filter id="blurEmpty">
                    <feGaussianBlur in="SourceGraphic" stdDeviation="3" />
                  </filter>
                </defs>
              </svg>
            </div>
            <h2 className={styles.emptyTitle}>
              무엇을 도와드릴까요?
            </h2>
            <p className={styles.emptyDescription}>
              궁금하신 내용을 질문해주세요. Perso AI가 정확한 답변을 드리겠습니다.
            </p>
            
            {/* 추천 질문 카드 */}
            <div className={styles.suggestedQuestions}>
              <button
                className={styles.questionCard}
                onClick={() => handleSendMessage("Perso.ai는 어떤 서비스인가요?")}
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M10 2a8 8 0 100 16 8 8 0 000-16zm1 11H9v-2h2v2zm0-4H9V5h2v4z"/>
                </svg>
                <span>Perso.ai는 어떤 서비스인가요?</span>
              </button>
              <button
                className={styles.questionCard}
                onClick={() => handleSendMessage("Perso.ai의 주요 기능은 무엇인가요?")}
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"/>
                </svg>
                <span>주요 기능이 궁금해요</span>
              </button>
              <button
                className={styles.questionCard}
                onClick={() => handleSendMessage("어떤 언어를 지원하나요?")}
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M10 2a8 8 0 100 16 8 8 0 000-16zM8 14H6v-1.5A1.5 1.5 0 017.5 11H8v3zm4 0h-2v-3h.5A1.5 1.5 0 0112 12.5V14zm2-7H6V5h8v2z"/>
                </svg>
                <span>지원 언어는 어떻게 되나요?</span>
              </button>
            </div>
          </div>
        ) : (
          <>
            <MessageList messages={messages} isLoading={isLoading} />
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {error && (
        <div className={styles.errorBanner} role="alert">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 0a8 8 0 1 0 0 16A8 8 0 0 0 8 0zM7 4h2v5H7V4zm0 6h2v2H7v-2z" />
          </svg>
          <span>{error}</span>
          <button
            onClick={() => setError(null)}
            className={styles.errorClose}
            aria-label="오류 메시지 닫기"
          >
            ×
          </button>
        </div>
      )}

      <ChatInput onSend={handleSendMessage} disabled={isLoading} />
    </div>
  );
}

