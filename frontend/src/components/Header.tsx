"use client";

import styles from "./Header.module.css";

export default function Header() {
  const handleLogoClick: React.MouseEventHandler<HTMLAnchorElement> = (e) => {
    if (typeof window !== "undefined") {
      // 챗 리셋 이벤트 전파
      window.dispatchEvent(new CustomEvent("perso:reset-chat"));
    }

    if (typeof window !== "undefined" && window.location.pathname === "/") {
      e.preventDefault();
      window.scrollTo({ top: 0, behavior: "smooth" });
      if (window.location.hash) {
        history.replaceState(null, "", "/");
      }
    }
  };

  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <a href="/" className={styles.logo} onClick={handleLogoClick}>
          <div className={styles.logoIcon}>
            <svg
              width="36"
              height="36"
              viewBox="0 0 100 100"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              {/* 불완전한 원 - 메인 */}
              <path
                d="M 85 35 A 30 30 0 1 1 35 15"
                stroke="url(#mainGradientHeader)"
                strokeWidth="6"
                strokeLinecap="round"
                fill="none"
              >
                <animateTransform
                  attributeName="transform"
                  attributeType="XML"
                  type="rotate"
                  from="0 50 50"
                  to="360 50 50"
                  dur="8s"
                  repeatCount="indefinite"
                />
              </path>
              
              {/* 글로우 레이어 */}
              <path
                d="M 85 35 A 30 30 0 1 1 35 15"
                stroke="url(#glowGradientHeader)"
                strokeWidth="10"
                strokeLinecap="round"
                fill="none"
                opacity="0.25"
                filter="url(#blurHeader)"
              >
                <animateTransform
                  attributeName="transform"
                  attributeType="XML"
                  type="rotate"
                  from="0 50 50"
                  to="360 50 50"
                  dur="8s"
                  repeatCount="indefinite"
                />
              </path>
              
              <defs>
                {/* 메인 그라데이션 */}
                <linearGradient id="mainGradientHeader" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#6366f1" />
                  <stop offset="50%" stopColor="#8b5cf6" />
                  <stop offset="100%" stopColor="#d946ef" />
                </linearGradient>
                
                {/* 글로우 그라데이션 */}
                <linearGradient id="glowGradientHeader" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#6366f1" />
                  <stop offset="100%" stopColor="#d946ef" />
                </linearGradient>
                
                {/* 블러 필터 */}
                <filter id="blurHeader">
                  <feGaussianBlur in="SourceGraphic" stdDeviation="2" />
                </filter>
              </defs>
            </svg>
          </div>
          <span className={styles.logoText}>
            <span className="gradient-text">Perso</span> AI
          </span>
        </a>

        {/* 우측 CTA 제거 */}
        <nav className={styles.nav}></nav>
      </div>
    </header>
  );
}

