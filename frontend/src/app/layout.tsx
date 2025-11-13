import type { Metadata } from "next";
import "../styles/globals.css";

export const metadata: Metadata = {
  title: "Perso AI - 지식기반 챗봇",
  description: "정확한 답변을 제공하는 Perso AI 챗봇 시스템. 할루시네이션 없이 신뢰할 수 있는 답변을 제공합니다.",
  keywords: ["AI", "챗봇", "RAG", "Perso", "지식 기반", "벡터 검색"],
  authors: [{ name: "Perso AI Team" }],
  icons: {
    icon: "/favicon.svg",
  },
  openGraph: {
    title: "Perso AI - 지식기반 챗봇",
    description: "정확한 답변을 제공하는 Perso AI 챗봇 시스템",
    type: "website",
    locale: "ko_KR",
    siteName: "Perso AI",
  },
  twitter: {
    card: "summary_large_image",
    title: "Perso AI - 지식기반 챗봇",
    description: "정확한 답변을 제공하는 Perso AI 챗봇 시스템",
  },
  viewport: {
    width: "device-width",
    initialScale: 1,
    maximumScale: 5,
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}

