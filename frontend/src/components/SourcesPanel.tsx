"use client";

import { useState } from "react";
import styles from "./SourcesPanel.module.css";

type SourcesPanelProps = {
  sources: string[];
  score?: number;
};

export default function SourcesPanel({ sources, score }: SourcesPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!sources || sources.length === 0) return null;

  const hasScore = typeof score === "number";
  const isHighConfidence = hasScore && score >= 0.9;
  const isMediumConfidence = hasScore && score >= 0.83 && score < 0.9;

  return (
    <div className={styles.sourcesPanel}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={styles.toggle}
        aria-expanded={isExpanded}
        aria-label={isExpanded ? "출처 접기" : "출처 펼치기"}
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="currentColor"
          className={styles.icon}
        >
          <path d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0zM6.5 5L5 6.5 7.5 9 5 11.5 6.5 13l4-4-4-4z" />
        </svg>
        <span className={styles.label}>
          {sources.length}개 출처
          {hasScore && (
            <span
              className={`${styles.badge} ${
                isHighConfidence
                  ? styles.badgeHigh
                  : isMediumConfidence
                  ? styles.badgeMedium
                  : styles.badgeLow
              }`}
            >
              {isHighConfidence
                ? "높은 신뢰도"
                : isMediumConfidence
                ? "중간 신뢰도"
                : "낮은 신뢰도"}
            </span>
          )}
        </span>
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="currentColor"
          className={`${styles.chevron} ${isExpanded ? styles.chevronOpen : ""}`}
        >
          <path d="M4.427 7.427l3.396 3.396a.25.25 0 00.354 0l3.396-3.396A.25.25 0 0011.396 7H4.604a.25.25 0 00-.177.427z" />
        </svg>
      </button>

      {isExpanded && (
        <div className={styles.content}>
          {hasScore && (
            <div className={styles.score}>
              <span className={styles.scoreLabel}>유사도:</span>
              <span className={styles.scoreValue}>{(score * 100).toFixed(1)}%</span>
            </div>
          )}
          <ul className={styles.list}>
            {sources.map((source, idx) => (
              <li key={idx} className={styles.source}>
                {source}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

