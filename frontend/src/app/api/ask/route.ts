import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    
    // Vercel 서버 측에서만 접근 가능한 환경변수
    const backendBaseUrl = process.env.BACKEND_BASE_URL || "http://3.36.62.184:8000";
    
    // EC2 백엔드로 요청 전달 (서버→서버이므로 HTTP 허용)
    const backendRes = await fetch(`${backendBaseUrl}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!backendRes.ok) {
      // 백엔드 오류를 그대로 전달
      const errorData = await backendRes.json().catch(() => ({}));
      return NextResponse.json(
        errorData,
        { status: backendRes.status }
      );
    }

    const data = await backendRes.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("API Route Error:", error);
    return NextResponse.json(
      { error: "서버 오류가 발생했습니다." },
      { status: 500 }
    );
  }
}

