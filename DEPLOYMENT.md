# 배포 가이드 (Vercel + Render + Qdrant Cloud)

## 📋 배포 개요

이 문서는 **완전 무료**로 Perso.ai 챗봇을 배포하는 방법을 안내합니다.

**배포 아키텍처:**
```
Frontend (Vercel - 무료)
    ↓ HTTPS
Backend (Render - 무료 750시간/월)
    ↓ API
Qdrant Cloud (무료 1GB)
```

**예상 소요 시간:** 30분

---

## 🎯 사전 준비

### 1. 필요한 계정
- [ ] GitHub 계정
- [ ] Vercel 계정 (GitHub 로그인 가능)
- [ ] Render 계정 (GitHub 로그인 가능)
- [ ] Qdrant Cloud 계정 (이메일 가입)

### 2. 환경변수 준비
- [ ] Gemini API Key (`GEMINI_API_KEY`)
- [ ] GitHub 저장소 (Public/Private)

---

## 🚀 배포 단계

### Step 1: Qdrant Cloud 설정 (10분)

#### 1-1. Qdrant Cloud 가입
1. https://cloud.qdrant.io 접속
2. 이메일로 회원가입
3. 로그인

#### 1-2. Free Cluster 생성
1. "Create Cluster" 클릭
2. 설정:
   - **Cluster Name**: `perso-ai-qdrant`
   - **Region**: `asia-southeast1` (Singapore)
   - **Plan**: `Free` (1GB)
3. "Create" 클릭 (약 2-3분 소요)

#### 1-3. API Key 생성
1. Cluster 생성 완료 후 "API Keys" 탭
2. "Create API Key" 클릭
3. **API Key 복사** (한 번만 표시됨!)
4. Cluster URL 복사 (예: `https://xxxxx.cloud.qdrant.io`)

#### 1-4. 로컬에서 데이터 마이그레이션

**1. 환경변수 설정**
```bash
# .env 파일에 추가
QDRANT_CLOUD_URL=https://xxxxx.cloud.qdrant.io
QDRANT_CLOUD_API_KEY=your_api_key_here
```

**2. 마이그레이션 실행**
```bash
# 연결 테스트
python scripts/migrate_to_qdrant_cloud.py --test

# 데이터 마이그레이션
python scripts/migrate_to_qdrant_cloud.py
```

**3. 성공 확인**
```
🎉 마이그레이션 완료!
✅ 검증 성공: 13 개 포인트
```

---

### Step 2: Backend 배포 (Render) (10분)

#### 2-1. GitHub 저장소 푸시
```bash
git add .
git commit -m "feat: 배포 설정 추가"
git push origin main
```

#### 2-2. Render 배포
1. https://render.com 접속 (GitHub 로그인)
2. "New" → "Web Service" 클릭
3. GitHub 저장소 연결
4. 설정:
   - **Name**: `perso-ai-backend`
   - **Region**: `Singapore`
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && gunicorn app:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
   - **Plan**: `Free`

#### 2-3. 환경변수 설정
"Environment" 탭에서 추가:

| Key | Value | 비고 |
|-----|-------|------|
| `GEMINI_API_KEY` | `your_gemini_key` | Google AI Studio에서 발급 |
| `QDRANT_URL` | `https://xxxxx.cloud.qdrant.io` | Qdrant Cloud URL |
| `QDRANT_API_KEY` | `your_qdrant_key` | Qdrant Cloud API Key |
| `QDRANT_COLLECTION` | `qa_collection` | 고정값 |
| `EMBED_MODEL` | `snunlp/KR-SBERT-V40K-klueNLI-augSTS` | 고정값 |
| `EMBED_DIM` | `768` | 고정값 |
| `SIM_THRESHOLD` | `0.75` | 고정값 |
| `TOP_K` | `5` | 고정값 |

#### 2-4. 배포 시작
1. "Create Web Service" 클릭
2. 빌드 로그 확인 (약 5-10분)
3. 배포 완료 후 URL 복사 (예: `https://perso-ai-backend.onrender.com`)

#### 2-5. Health Check
```bash
curl https://your-backend.onrender.com/healthz
```

**예상 응답:**
```json
{"status": "ok", "qdrant": "connected"}
```

⚠️ **Cold Start 주의:**
- 첫 요청은 ~30초 소요 (무료 플랜)
- 이후 정상 속도로 작동

---

### Step 3: Frontend 배포 (Vercel) (5분)

#### 3-1. Vercel 배포
1. https://vercel.com 접속 (GitHub 로그인)
2. "New Project" 클릭
3. GitHub 저장소 선택
4. 설정:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: `frontend`
   - **Build Command**: (자동 감지)
   - **Output Directory**: (자동 감지)

#### 3-2. 환경변수 설정
"Environment Variables" 섹션에서:

| Key | Value | 비고 |
|-----|-------|------|
| `NEXT_PUBLIC_API_BASE_URL` | `https://perso-ai-backend.onrender.com` | Render Backend URL |

#### 3-3. 배포 시작
1. "Deploy" 클릭
2. 빌드 완료 대기 (약 2-3분)
3. 배포 완료 후 URL 확인 (예: `https://perso-ai.vercel.app`)

---

## ✅ 배포 검증

### 1. Frontend 접속
1. Vercel URL 접속 (`https://your-app.vercel.app`)
2. 초기 화면 확인 ("무엇을 도와드릴까요?")

### 2. 챗봇 테스트
```
질문: "Perso.ai는 어떤 서비스인가요?"
예상 답변: "Perso.ai는 이스트소프트가 개발한..."
```

### 3. Cold Start 테스트
- 첫 질문: ~30초 소요 (정상)
- 이후 질문: 2-3초 (정상)

---

## 🔧 문제 해결

### Backend Cold Start가 너무 느려요
**원인:** Render 무료 플랜은 15분 비활동 후 슬립 모드

**해결책:**
1. **옵션 A**: Railway로 마이그레이션 ($5 크레딧, Cold Start 없음)
2. **옵션 B**: Cron Job으로 5분마다 Health Check
3. **옵션 C**: 유료 플랜 전환 ($7/월)

### Qdrant 연결 오류
```
qdrant_client.http.exceptions.UnexpectedResponse: ...
```

**체크리스트:**
- [ ] `QDRANT_URL` 형식 확인 (`https://` 포함)
- [ ] `QDRANT_API_KEY` 정확성 확인
- [ ] Qdrant Cloud에 데이터 업로드 완료 확인

**확인 방법:**
```bash
python scripts/migrate_to_qdrant_cloud.py --test
```

### Frontend → Backend CORS 오류
```
Access to fetch at '...' has been blocked by CORS policy
```

**해결:** `backend/app.py`에 CORS 설정 확인
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션: Vercel URL만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Gemini API 오류
```
ValueError: GEMINI_API_KEY가 설정되지 않았습니다.
```

**해결:**
1. Render 대시보드 → Environment 탭
2. `GEMINI_API_KEY` 추가
3. "Manual Deploy" → "Deploy latest commit"

---

## 📊 무료 티어 제한

| 서비스 | 제한 | 초과 시 |
|--------|------|---------|
| **Vercel** | 100GB 대역폭/월 | 자동 일시정지 |
| **Render** | 750시간/월 | 계정당 제한 |
| **Qdrant Cloud** | 1GB 저장소 | 업그레이드 필요 |
| **Gemini API** | 1500 req/day | 다음날 초기화 |

**예상 사용량 (월 1000명 방문 시):**
- Vercel: ~5GB (여유)
- Render: ~720시간 (여유)
- Qdrant: ~50MB (여유)
- Gemini: ~300 req/day (여유)

→ **충분히 무료로 운영 가능!**

---

## 🔄 업데이트 배포

### 코드 변경 시
```bash
git add .
git commit -m "feat: 새 기능 추가"
git push origin main
```

**자동 배포:**
- Frontend (Vercel): 자동 빌드 & 배포 (~2분)
- Backend (Render): 자동 빌드 & 배포 (~5분)

### 데이터 업데이트 (Q&A.xlsx 수정)
1. 로컬에서 `python backend/ingest.py` 실행
2. `python scripts/migrate_to_qdrant_cloud.py` 실행
3. Qdrant Cloud에 자동 반영

---

## 💰 비용 절감 팁

### 1. Render Cold Start 최소화
**방법:** UptimeRobot으로 5분마다 Ping
```
URL: https://your-backend.onrender.com/healthz
Interval: 5분
```

**효과:**
- Cold Start 방지
- 사용자 경험 개선

**주의:**
- 월 750시간 제한 주의
- 약 720시간 사용 (여유 30시간)

### 2. Vercel 대역폭 절감
- 이미지 최적화: Next.js Image 사용
- 정적 리소스 캐싱
- Gzip 압축 (자동 적용)

### 3. Gemini API 절약
- 응답 캐싱 (동일 질문)
- 배치 처리
- Rate Limiting

---

## 🎓 배포 후 체크리스트

- [ ] Frontend 정상 접속 확인
- [ ] Backend Health Check 통과
- [ ] 챗봇 질문/응답 정상 작동
- [ ] Qdrant 데이터 조회 성공
- [ ] 출처(Sources) 정상 표시
- [ ] 모바일 반응형 확인
- [ ] Cold Start 시간 측정 (< 40초)

---

## 📚 참고 문서

- [Render 공식 문서](https://render.com/docs)
- [Vercel 공식 문서](https://vercel.com/docs)
- [Qdrant Cloud 문서](https://qdrant.tech/documentation/cloud/)
- [Next.js 배포 가이드](https://nextjs.org/docs/deployment)

---

## 🆘 도움이 필요하신가요?

**일반적인 질문:**
1. Render 배포 로그 확인
2. Vercel 빌드 로그 확인
3. 브라우저 개발자 도구 Console 확인

**여전히 문제가 해결되지 않는다면:**
- GitHub Issues에 질문 남기기
- Render/Vercel 커뮤니티 포럼 활용
- Qdrant Discord 채널

---

**축하합니다! 🎉 이제 전 세계 어디서나 Perso.ai 챗봇에 접속할 수 있습니다!**

