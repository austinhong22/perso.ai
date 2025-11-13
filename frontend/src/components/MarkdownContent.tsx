"use client";

import styles from "./MarkdownContent.module.css";

type MarkdownContentProps = {
  content: string;
};

export default function MarkdownContent({ content }: MarkdownContentProps) {
  // 간단한 Markdown 파싱 (코드, 볼드, 리스트, 링크 지원)
  const renderContent = () => {
    const lines = content.split("\n");
    const elements: JSX.Element[] = [];
    let codeBlock = "";
    let inCodeBlock = false;
    let listItems: string[] = [];

    const flushList = () => {
      if (listItems.length > 0) {
        elements.push(
          <ul key={`list-${elements.length}`} className={styles.list}>
            {listItems.map((item, i) => (
              <li key={i}>{parseInline(item)}</li>
            ))}
          </ul>
        );
        listItems = [];
      }
    };

    lines.forEach((line, idx) => {
      // 코드 블록
      if (line.trim().startsWith("```")) {
        if (inCodeBlock) {
          elements.push(
            <pre key={`code-${elements.length}`} className={styles.codeBlock}>
              <code>{codeBlock}</code>
            </pre>
          );
          codeBlock = "";
          inCodeBlock = false;
        } else {
          flushList();
          inCodeBlock = true;
        }
        return;
      }

      if (inCodeBlock) {
        codeBlock += line + "\n";
        return;
      }

      // 리스트
      if (line.trim().match(/^[-*]\s/)) {
        listItems.push(line.trim().replace(/^[-*]\s/, ""));
        return;
      }

      flushList();

      // 빈 줄
      if (line.trim() === "") {
        return;
      }

      // 일반 텍스트
      elements.push(
        <p key={`p-${idx}`} className={styles.paragraph}>
          {parseInline(line)}
        </p>
      );
    });

    flushList();

    return elements;
  };

  const parseInline = (text: string): React.ReactNode => {
    const parts: React.ReactNode[] = [];
    let remaining = text;
    let key = 0;

    while (remaining.length > 0) {
      // 인라인 코드 `code`
      const codeMatch = remaining.match(/`([^`]+)`/);
      if (codeMatch && codeMatch.index !== undefined) {
        if (codeMatch.index > 0) {
          parts.push(remaining.substring(0, codeMatch.index));
        }
        parts.push(
          <code key={`code-${key++}`} className={styles.inlineCode}>
            {codeMatch[1]}
          </code>
        );
        remaining = remaining.substring(codeMatch.index + codeMatch[0].length);
        continue;
      }

      // 볼드 **bold**
      const boldMatch = remaining.match(/\*\*([^*]+)\*\*/);
      if (boldMatch && boldMatch.index !== undefined) {
        if (boldMatch.index > 0) {
          parts.push(remaining.substring(0, boldMatch.index));
        }
        parts.push(
          <strong key={`bold-${key++}`} className={styles.bold}>
            {boldMatch[1]}
          </strong>
        );
        remaining = remaining.substring(boldMatch.index + boldMatch[0].length);
        continue;
      }

      // 링크 [text](url)
      const linkMatch = remaining.match(/\[([^\]]+)\]\(([^)]+)\)/);
      if (linkMatch && linkMatch.index !== undefined) {
        if (linkMatch.index > 0) {
          parts.push(remaining.substring(0, linkMatch.index));
        }
        parts.push(
          <a
            key={`link-${key++}`}
            href={linkMatch[2]}
            className={styles.link}
            target="_blank"
            rel="noopener noreferrer"
          >
            {linkMatch[1]}
          </a>
        );
        remaining = remaining.substring(linkMatch.index + linkMatch[0].length);
        continue;
      }

      // 나머지 텍스트
      parts.push(remaining);
      break;
    }

    return parts;
  };

  return <div className={styles.markdown}>{renderContent()}</div>;
}

