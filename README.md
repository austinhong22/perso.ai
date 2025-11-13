# Perso.ai 챗봇 시스템

## 개요
- 목적: 제공된 Q&A.xlsx를 기반으로 벡터 DB(Qdrant)와 임베딩(SBERT)을 활용해, 할루시네이션 없이 정확한 답만 반환하는 지식기반 챗봇 구현
- 핵심: Clean Architecture 적용, 검색 정확도 향상 전략(Query Expansion, Hybrid Reranking, 동적 임계값), 프론트-백엔드 API 계약 일원화(`/ask`)
- 프론트엔드: ChatGPT/Claude 스타일 UI, Perso.ai 브랜딩, 출처(Sources) 노출

## 사용 기술 스택
- Backend: FastAPI, Uvicorn, Pydantic v2, Qdrant Client, Sentence-Transformers(ko‑SBERT), Pandas/Openpyxl, Pytest, **rapidfuzz**
- Frontend: Next.js 14(App Router), React 18, TypeScript 5
- 인프라/배포: Qdrant(Docker 로컬), 프론트(Vercel/Netlify), 백엔드(Render/Railway/Fly.io) 대상
- 아키텍처 원칙: Lightweight Clean Architecture(domain/application/infrastructure), OCP로 임베딩/리트리버 교체 용이
  - Domain: QAPair, SearchResult 엔티티 및 Retriever/Embedder 인터페이스
  - Application: **QASearchUseCase** (Query Expansion + Reranking), **QueryExpander**, **HybridReranker**
  - Infrastructure: QdrantRetriever, SentenceTransformerEmbedder, **HallucinationGuard(동적 임계값)**
  - Interface: FastAPI 라우트에서 UseCase 주입 및 호출

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

### 1. Query Expansion (구어체/반말 대응)
- **50+ 패턴 규칙 기반 정규화**:
  - 반말→존댓말: "뭐야"→"무엇인가요", "얼마야"→"얼마인가요", "필요해"→"필요한가요"
  - 오타 수정: "어떻케"→"어떻게", "persoa.ai"→"Perso.ai"
  - 브랜드 정규화: "persoai/퍼소/perso"→"Perso.ai"
  - 도메인 동의어: "가격/비용"→"요금", "상담/문의"→"고객센터"
- 최대 5개 변형 생성 → 모든 변형 검색 후 최고 점수 채택

### 2. Hybrid Reranking (벡터+문자열 유사도)
- **벡터 유사도 70% + 문자열 유사도 30%** 가중 평균
- rapidfuzz `token_sort_ratio`: 단어 순서 무관, 형태소 변형 강건
- 문자열 유사도 < 0.3 시 10% 페널티 (의미는 비슷하지만 표현이 다른 경우 필터링)

### 3. 동적 임계값 (질문 유형별 조정)
- **의문문** (?, 무엇, 어떻게): 기본 0.75
- **명사형 질문** (단어 ≤3개): 0.70 (관대)
- **매우 짧은 질문** (<5자): 0.80 (엄격)
- → Recall 향상 + Precision 유지

### 4. Hallucination Guard
- 임계값 미만 시: "죄송해요, 제가 가지고 있는 데이터셋에는 해당 내용이 없어요. 비슷한 질문으로 다시 시도해보세요."
- **임계값 튜닝 근거**: `snunlp/KR-SBERT` + Qdrant(COSINE) 환경에서 36개 평가 쿼리 기준 **T=0.75**에서 **Precision=1.000, Recall=0.536, F1=0.698** 달성. Query Expansion 적용 후 Recall 실질적으로 향상.

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
    query_expander.py    # Query Expansion 규칙
    reranker.py          # Hybrid Reranking (벡터+문자열)
  infrastructure/
    repositories.py      # QdrantRetriever, SentenceTransformerEmbedder 구현체
    guards.py            # HallucinationGuard (임계값 가드)
    config.py            # 환경 설정
backend/
  app.py                 # FastAPI 엔트리포인트 (UseCase 사용)
  ingest.py              # 데이터 파싱 및 Qdrant 업서트
  requirements.txt
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



## Backend (FastAPI)
가상환경 권장: Python 3.11+
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
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

