# Perso.ai 챗봇 시스템

## 사용 기술 스택
- Backend: FastAPI, Uvicorn, Pydantic v2, Qdrant Client, Sentence-Transformers(ko‑SBERT), Pandas/Openpyxl, Pytest
- Frontend: Next.js 14(App Router), React 18, TypeScript 5
- 인프라/배포: Qdrant(Docker 로컬), 프론트(Vercel/Netlify), 백엔드(Render/Railway/Fly.io) 대상
- 아키텍처 원칙: Lightweight Clean Architecture(domain/application/infrastructure), OCP로 임베딩/리트리버 교체 용이
  - Domain: QAPair, SearchResult 엔티티 및 Retriever/Embedder 인터페이스
  - Application: QASearchUseCase로 비즈니스 로직 오케스트레이션
  - Infrastructure: QdrantRetriever, SentenceTransformerEmbedder, HallucinationGuard 구현체
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
  - 한국어 특화 ko‑SBERT 계열 로컬 임베딩(현재 `jhgan/ko-sroberta-multitask`)
  - normalize_embeddings=True로 코사인 점수 안정화
  - OpenAI 미사용(비용/지연 0, 오프라인 가능)
- 인덱싱(ingest) 파이프라인:
  - `Q&A.xlsx`의 `Unnamed: 2` 열에서 `Q.`/`A.` 교차 라인 파싱 → 접두사/공백 정리 → 질문 중복 제거
  - 질문 임베딩 생성 후 벡터+payload 업서트
- 검색(쿼리 → Top-K) 및 랭킹:
  - 쿼리 임베딩 → Qdrant Top‑K=`TOP_K` 검색 → 코사인 점수 기준 정렬
- 응답 생성과 출처 표기 방식:
  - UseCase에서 임계값 이상 결과 기반으로 `answer`와 `sources`(근거 질문/답변) 반환
  - 임계값 미만이면 HallucinationGuard의 가드 메시지 반환
  - 프론트엔드에서 sources 배열을 출처로 표시

## 정확도 향상 전략
- 유사도 임계값/가드 메시지:
  - "모델이 근거 없는 답변을 생성하지 않도록" 유사도 임계값(`SIM_THRESHOLD=0.83`) 기반 Hallucination Guard 적용
  - 임계값 미만 시: "죄송해요, 제가 가지고 있는 데이터셋에는 해당 내용이 없어요. 비슷한 질문으로 다시 시도해보세요."처럼 정직하고 친절한 UX 문구로 응답
  - **임계값 선정 근거**: ko‑SBERT(`jhgan/ko-sroberta-multitask`) + Qdrant(COSINE) 환경에서 T ∈ [0.75, 0.90]을 0.01 간격으로 스윕하여 Precision/Recall/F1을 계산. 36개 평가 쿼리(exact/para 28개, noise 8개) 기준 **T=0.83**에서 **Precision=1.000(완벽한 무관 질문 차단), Recall=0.571, F1=0.727**로 실용적 균형점 확보. 최고 F1(0.783)은 T=0.75였으나, Recall 0.57 수준에서도 실제 사용자 질의는 충분히 커버하며 False Positive 0을 유지하는 0.83을 채택.

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
    components/Chat.tsx  # sources 출처 표시 포함
    lib/api.ts           # /ask 엔드포인트 호출
scripts/
  tune_threshold.py      # 임계값 튜닝 스크립트
  export_examples.py
.env
```

## 환경변수(.env)
```
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=qa_collection
EMBED_DIM=768
SIM_THRESHOLD=0.83
TOP_K=3
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
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
```bash
cd frontend
npm install
npm run dev
```

## Qdrant (Docker)
```bash
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant:latest
```
