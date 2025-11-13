"use client";

import type { Message } from "./ChatContainer";
import styles from "./MessageBubble.module.css";
import MarkdownContent from "./MarkdownContent";
import SourcesPanel from "./SourcesPanel";

type MessageBubbleProps = {
  message: Message;
};

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`${styles.bubble} ${isUser ? styles.user : styles.assistant}`}
    >
      {!isUser && (
        <div className={styles.avatar}>
          <svg
            width="24"
            height="24"
            viewBox="0 0 100 100"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <circle
              cx="50"
              cy="50"
              r="45"
              stroke="url(#gradient)"
              strokeWidth="8"
              fill="none"
            />
            <defs>
              <linearGradient
                id="gradient"
                x1="0%"
                y1="0%"
                x2="100%"
                y2="100%"
              >
                <stop offset="0%" stopColor="#6366f1" />
                <stop offset="100%" stopColor="#a855f7" />
              </linearGradient>
            </defs>
          </svg>
        </div>
      )}

      <div className={styles.content}>
        <div className={styles.message}>
          {isUser ? (
            <p className={styles.text}>{message.content}</p>
          ) : (
            <MarkdownContent content={message.content} />
          )}
        </div>

        {!isUser && message.sources && message.sources.length > 0 && (
          <SourcesPanel sources={message.sources} score={message.score} />
        )}

        <time className={styles.timestamp} dateTime={message.timestamp.toISOString()}>
          {message.timestamp.toLocaleTimeString("ko-KR", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </time>
      </div>

      {isUser && (
        <div className={styles.avatarUser}>
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
          </svg>
        </div>
      )}
    </div>
  );
}

