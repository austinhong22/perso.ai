# ESTSOFT RAG Monorepo

백엔드(FastAPI)와 프론트엔드(Next.js)를 한 리포 안에서 관리/배포하기 위한 기본 템플릿입니다.

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
OPENAI_API_KEY=your_key
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=qa_collection
EMBED_DIM=1536
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


