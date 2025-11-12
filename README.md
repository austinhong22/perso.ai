# Perso.ai 챗봇 시스템

## 사용 기술 스택
- Backend: [작성 예정]
- Frontend: [작성 예정]
- 인프라/배포: [작성 예정]
- 아키텍처 원칙: [작성 예정]

## 벡터 DB 및 임베딩 방식
- Vector DB 선택/사유: [작성 예정]
- 컬렉션/스키마(차원, payload): [작성 예정]
- 임베딩 모델/프로바이더: [작성 예정]
- 인덱싱(ingest) 파이프라인: [작성 예정]
- 검색(쿼리 → Top-K) 및 랭킹: [작성 예정]
- 응답 생성과 출처 표기 방식: [작성 예정]

## 정확도 향상 전략
- 유사도 임계값/가드 메시지: [작성 예정]
- 청크 기준/오버랩 정책: [작성 예정]
- 리트리벌/재순위화 전략: [작성 예정]
- 출처 표기/근거 기반 응답: [작성 예정]
- 캐싱/QA 페어 보강: [작성 예정]
- 테스트 전략(TDD-lite): [작성 예정]

## 구조
```
backend/
  app.py
  ingest.py
  requirements.txt
  config.py
  tests/
    test_search.py
frontend/
  package.json
  next.config.mjs
  src/
    app/page.tsx
    components/Chat.tsx
    lib/api.ts
scripts/
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


