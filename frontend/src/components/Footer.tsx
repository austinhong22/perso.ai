import styles from "./Footer.module.css";

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.container}>
        <p className={styles.copyright}>
          © {new Date().getFullYear()} Perso AI. All rights reserved.
        </p>
        <div className={styles.links}>
          <a href="#" className={styles.link}>
            서비스 소개
          </a>
          <a href="#" className={styles.link}>
            개인정보처리방침
          </a>
          <a href="#" className={styles.link}>
            이용약관
          </a>
        </div>
      </div>
    </footer>
  );
}

