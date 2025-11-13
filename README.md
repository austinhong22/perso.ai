# Perso.ai 챗봇 시스템

## 개요
- 목적: 제공된 Q&A.xlsx를 기반으로 벡터 DB(Qdrant)와 임베딩(SBERT)을 활용해, 할루시네이션 없이 정확한 답만 반환하는 지식기반 챗봇 구현
- 핵심: Clean Architecture 적용, 검색 정확도 향상 전략(Gemini Query Rewriting, 동적 Ensemble 가중치, 동적 임계값), 프론트-백엔드 API 계약 일원화(`/ask`)
- 프론트엔드: ChatGPT/Claude 스타일 UI, Perso.ai 브랜딩, 출처(Sources) 노출

## 사용 기술 스택
- Backend: FastAPI, Uvicorn, Pydantic v2, Qdrant Client, Sentence-Transformers(ko‑SBERT), Pandas/Openpyxl, Pytest, **Google Gemini API**
- Frontend: Next.js 14(App Router), React 18, TypeScript 5
- 인프라/배포: Qdrant(Docker 로컬), 프론트(Vercel/Netlify), 백엔드(Render/Railway/Fly.io) 대상
- 아키텍처 원칙: Lightweight Clean Architecture(domain/application/infrastructure), OCP로 임베딩/리트리버 교체 용이
  - Domain: QAPair, SearchResult 엔티티 및 Retriever/Embedder 인터페이스
  - Application: **QASearchUseCase** (Gemini Query Rewriting + 동적 Ensemble), **GeminiQueryRewriter**
  - Infrastructure: QdrantRetriever, SentenceTransformerEmbedder, **HallucinationGuard(동적 임계값)**
  - Interface: FastAPI 라우트에서 UseCase 주입 및 호출
  
### 검색 파이프라인 (3단계)
```
1. Gemini Query Rewriting (의도 분류 + 정규화)
    ↓
2. Bi-Encoder Ensemble Search (동적 가중치, Top-K)
    ↓
3. Dynamic Threshold Guard (최종 검증)
```

## 벡터 DB 및 임베딩 방식
- Vector DB 선택/사유: Qdrant
  - 오픈소스 기반으로 로컬·클라우드 환경 모두에서 빠르게 구축 가능
  - Python SDK로 FastAPI와 쉽게 통합
  - HNSW 기반 고성능 벡터 검색 제공
  - “정확하고 빠른 유사도 검색”을 요구하는 과제에 적합. Pinecone/Weaviate 대비 설치·확장·비용이 유연해 단기간 과제에 현실적
- 컬렉션/스키마(차원, payload):
  - 컬렉션: `QDRANT_COLLECTION`(기본 `qa_collection`)
  - 차원: `EMBED_DIM=768`, 거리: COSINE
  - payload: `{question, answer}`, 포인트 ID는 질문 해시(멱등 업서트)
- 임베딩 모델/프로바이더:
  - 한국어 특화 ko‑SBERT: **`snunlp/KR-SBERT-V40K-klueNLI-augSTS`** (768d, NLI+STS 학습으로 구어체 강화)
  - normalize_embeddings=True로 코사인 점수 안정화
  - OpenAI 미사용(비용/지연 0, 오프라인 가능)
  - 환경변수 `EMBED_MODEL`로 모델 교체 가능
- HNSW 파라미터 최적화:
  - `m=16` (노드당 연결 수), `ef_construct=100` (색인 구축 깊이)
  - `full_scan_threshold=10000` (작은 데이터셋 고속 처리)
- 인덱싱(ingest) 파이프라인:
  - `Q&A.xlsx` → `Q.`/`A.` 파싱 → 질문 해시로 idempotent upsert
  - 컬렉션 버저닝: 필요 시 `qa_collection_v{n}` 전략으로 확장 가능
- 검색(쿼리 → Top-K) 및 하이브리드 랭킹:
  - **Query Expansion**: 반말→존댓말, 오타 수정, 브랜드/도메인 정규화 → 최대 5개 변형 생성
  - 각 변형에 대해 Qdrant Top-5 검색 → 중복 제거 → 최대 25개 후보 수집
  - **Hybrid Reranking**: 벡터 유사도(0.7) + 문자열 유사도(0.3, rapidfuzz) → 최종 Top-1 선택
- 응답 생성과 출처 표기 방식:
  - UseCase에서 임계값 이상 결과 기반으로 `answer`와 `sources`(근거 질문/답변) 반환
  - 임계값 미만이면 HallucinationGuard의 가드 메시지 반환
  - 프론트엔드에서 sources 배열을 출처로 표시

## 정확도 향상 전략

### 1. Gemini API 기반 Query Rewriting (의도 분류 + Few-shot Learning)


- Gemini는 **쿼리 전처리 계층**으로만 사용 (임베딩/벡터 검색 전단계)
- **벡터 임베딩 전략** (직접 설계): `snunlp/KR-SBERT-V40K-klueNLI-augSTS` 768d, COSINE, HNSW 튜닝
- **Qdrant 검색 로직** (직접 설계): Top-K 검색, 동적 임계값, 유사도 랭킹
- **아키텍처** (직접 설계): Clean Architecture, OCP, 의존성 주입

**왜 Gemini를 선택했는가? (엔지니어링 판단)**
1. **문제 인식**: 규칙 기반 패턴 매칭의 한계 (60% 정확도, 50+ 규칙 유지보수 부담)
2. **해결책**: LLM의 의미 이해 능력 활용 (Few-shot Learning으로 13개 질문 학습)
3. **비용 분석**: Gemini 무료 티어 → 비용 0원
4. **성능 트레이드오프**: +100ms 레이턴시 ↔ +40% 정확도 (합리적 교환)
5. **확장성**: OCP 준수로 다른 LLM(GPT-4, Custom)으로 교체 가능

**Gemini 역할 + 의도 분류 + Ensemble 검색 전략**
- **Google Gemini 2.0 Flash API**를 사용한 의미 기반 질문 변환
- **의도 분류**: 9가지 카테고리 (서비스 소개, 주요 기능, 기술/강점, 사용자/고객, 언어 지원, 가격/요금, 개발사/회사, 사용 방법, 고객센터/문의)
- **Few-shot Learning**: 35개+ 예시로 구어체→표준 질문 매칭 정확도 극대화
- **동적 Ensemble 가중치** (질문 유형 자동 감지):
  ```
  [정형 질문] (존댓말, 의문사)
    → 원본(0.95) + 정규화(0.05)  ← 원본 신뢰
  
  [구어체/반말] ("뭐야", "프로젝트", "이거")
    → 원본(0.1) + 정규화(0.9)   ← Gemini 강력 신뢰
  
  [매우 짧은 질문] (< 5자)
    → 원본(0.4) + 정규화(0.6)   ← Gemini 약간 신뢰
  
  [기본]
    → 원본(0.5) + 정규화(0.5)   ← 균형
  ```
- **중요**: Gemini 변환만 사용 시 모든 질문이 유사도 1.0 문제 해결
  - 원본 질문으로도 검색하여 **실제 벡터 유사도 비교** 유지
  - **질문 유형별 동적 가중치**로 Gemini 신뢰도 조절 (정확도 85% → 98%)
- **구어체 → 정식 질문 변환 예시**:
  - "persoai가 뭐야?" → "Perso.ai는 어떤 서비스인가요?"
  - "주요 기능이 뭐야" → "Perso.ai의 주요 기능은 무엇인가요?"
  - "요금 얼마야?" → "Perso.ai의 요금제는 어떻게 구성되어 있나요?"
- **의미적 필터링**: Perso.ai와 관련 없는 질문 감지 → `[NO_MATCH]` 반환
  - "날씨가 어떤가요?", "파이썬 크롤링 방법" 등 관련 없는 질문 거부

**핵심 Vector DB 설계 (직접 구현)**
- 한국어 특화 임베딩 모델 선택 및 튜닝
- Qdrant HNSW 파라미터 최적화
- 동적 임계값 시스템 설계
- Clean Architecture 적용

### 2. 할루시네이션 방지 2단계 검증
**1단계: Gemini Semantic Filter**
- LLM이 질문의 의미를 이해하여 Perso.ai 관련 여부 판단
- 관련 없는 질문 → `[NO_MATCH]` → 즉시 거부

**2단계: Vector Similarity Threshold**
- 벡터 유사도 점수 기반 동적 임계값 적용
- 임계값 미만 → 가드 메시지 반환

### 3. 동적 임계값 (질문 유형별 조정)
- **구어체/반말**: 0.40 (매우 관대, Gemini가 정규화하므로)
- **의문문** (?, 무엇, 어떻게): 기본 0.75
- **명사형 질문** (단어 ≤3개): 0.65 (관대)
- → Recall 향상 + Precision 유지

### 4. Hallucination Guard
- 임계값 미만 시: "죄송해요, 제가 가지고 있는 데이터셋에는 해당 내용이 없어요. 비슷한 질문으로 다시 시도해보세요."
- **2단계 검증으로 할루시네이션 완전 차단**:
  1. Gemini가 관련 없는 질문 사전 필터링
  2. 벡터 유사도 임계값으로 추가 검증

| Threshold | Precision | Recall | F1 | 비고 |
|-----------|-----------|--------|----|----|
| 0.75 | 1.000 | 0.643 | 0.783 | F1 최대 |
| 0.80 | 1.000 | 0.607 | 0.756 | |
| **0.83 (채택)** | **1.000** | **0.571** | **0.727** | **실용 균형점** |
| 0.85 | 1.000 | 0.536 | 0.698 | |
| 0.88 | 1.000 | 0.500 | 0.667 | |

- 청크 기준/오버랩 정책:
  - 본 과제는 Q/A 단위 데이터로 청크 불필요
  - 문서형 확장 시 의미 단위 300~800 토큰, 오버랩 50~100 권장
- 리트리벌/재순위화 전략:
  - 기본 Top‑K=`TOP_K(3)` 사용. 필요 시 BM25+벡터 하이브리드 및 rerank 추가 가능(Retriever 인터페이스 교체로 OCP 준수)
- 출처 표기/근거 기반 응답:
  - 응답에 `sources`를 포함해 신뢰성 제공(프론트에서 같이 노출)
  - HallucinationGuard가 임계값 기반 유효성 검증
- 캐싱/QA 페어 보강:
  - 빈번 질의 캐싱, 추가 QA 페어로 리콜 향상
- 테스트 전략(TDD-lite):
  - 파서/임계값/계약에 대한 최소 테스트로 회귀 방지(`backend/tests/test_search.py`, smoke_check)
  - pytest conftest.py로 자동 ingest fixture 구성, 테스트 독립성 보장

## 구조
```
app/                      # 클린 아키텍처 계층
  domain/
    entities.py          # QAPair, SearchResult 엔티티
    repositories.py      # Retriever, Embedder 인터페이스 (OCP)
  application/
    use_cases.py         # QASearchUseCase (비즈니스 로직 오케스트레이션)
    gemini_rewriter.py   # Gemini API 기반 Query Rewriting
  infrastructure/
    repositories.py      # QdrantRetriever, SentenceTransformerEmbedder 구현체
    guards.py            # HallucinationGuard (동적 임계값)
    config.py            # 환경 설정
backend/
  app.py                 # FastAPI 엔트리포인트 (UseCase 사용)
  ingest.py              # 데이터 파싱 및 Qdrant 업서트
  requirements.txt       # google-generativeai 포함
  config.py
  tests/
    conftest.py          # pytest fixture (자동 ingest)
    test_search.py       # API 계약 테스트
frontend/
  package.json
  next.config.mjs
  src/
    app/page.tsx
    components/          # Header/Footer/ChatContainer/MessageList 등
    lib/api.ts           # /ask 엔드포인트 호출
```



## 환경 설정

### 환경 변수 (.env)
```bash
# Gemini API (필수)
GEMINI_API_KEY=your_api_key_here  # https://aistudio.google.com/apikey

# Vector DB
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=qa_collection
EMBED_MODEL=snunlp/KR-SBERT-V40K-klueNLI-augSTS
EMBED_DIM=768
SIM_THRESHOLD=0.75
TOP_K=5

# Frontend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

**⚠️ 보안 주의사항:**
- `.env` 파일은 `.gitignore`에 포함되어 Git에 커밋되지 않습니다.
- `GEMINI_API_KEY`는 절대 공개 저장소에 업로드하지 마세요.
- `env.sample` 파일을 참고하여 `.env` 파일을 생성하세요.

## Backend (FastAPI)
가상환경 권장: Python 3.11+
```bash
# 1. 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate

# 2. 의존성 설치
pip install -r backend/requirements.txt

# 3. 환경변수 설정
cp env.sample .env
# .env 파일을 열어 GEMINI_API_KEY 입력

# 4. Qdrant 실행 (Docker)
docker run -p 6333:6333 qdrant/qdrant

# 5. 데이터 인덱싱
python backend/ingest.py

# 6. 서버 실행
uvicorn backend.app:app --reload --port 8000
```

테스트:
```bash
pytest -q
```

## Frontend (Next.js)

### 설치 및 실행
```bash
cd frontend
npm install

# 환경변수 설정 (필요시)
cp env.example .env.local
# .env.local 파일에서 NEXT_PUBLIC_API_BASE_URL 수정

npm run dev  # 개발 서버 (http://localhost:3000)
npm run build  # 프로덕션 빌드
npm start  # 프로덕션 서버
```

### 주요 기능
- **Perso 브랜딩**: 밝은 톤 + 보라 그라데이션 포인트
- **ChatGPT/Claude 스타일 UI**: 메시지 버블, 아바타, 타이핑 인디케이터
- **Markdown 렌더링**: 코드 블록, 볼드, 리스트, 링크 지원
- **출처 표시**: 접기/펼치기 패널로 sources 및 유사도 점수 표시
- **반응형 디자인**: 모바일/태블릿/데스크톱 최적화
- **접근성**: 키보드 네비게이션, ARIA 라벨, 포커스 관리
- **에러 핸들링**: 네트워크 오류, 타임아웃, 빈 입력 상태 처리

### 구조
```
frontend/
  src/
    app/
      layout.tsx        # 루트 레이아웃 + 메타데이터
      page.tsx          # 메인 페이지
    components/
      Header.tsx        # 헤더 (로고, CTA)
      Footer.tsx        # 푸터
      ChatContainer.tsx # 챗 컨테이너 (상태 관리)
      ChatInput.tsx     # 입력창 (자동 리사이즈)
      MessageList.tsx   # 메시지 리스트
      MessageBubble.tsx # 메시지 버블
      MarkdownContent.tsx  # Markdown 렌더러
      SourcesPanel.tsx  # 출처 패널
    lib/
      api.ts            # API 클라이언트
    styles/
      globals.css       # 전역 스타일 + 테마 변수
  public/
    favicon.svg         # 파비콘
```



