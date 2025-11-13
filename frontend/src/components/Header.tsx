"use client";

import Link from "next/link";
import styles from "./Header.module.css";

export default function Header() {
  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <Link href="/" className={styles.logo}>
          <div className={styles.logoIcon}>
            <svg
              width="32"
              height="32"
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
          <span className={styles.logoText}>
            <span className="gradient-text">Perso</span> AI
          </span>
        </Link>

        <nav className={styles.nav}>
          <button className="btn btn-primary" aria-label="지금 시작하기">
            지금 시작하기
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="currentColor"
              style={{ marginLeft: "0.5rem" }}
            >
              <path d="M8 0L6.59 1.41 12.17 7H0v2h12.17l-5.58 5.59L8 16l8-8z" />
            </svg>
          </button>
        </nav>
      </div>
    </header>
  );
}

