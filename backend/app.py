import os, json, time, sys
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient
from dotenv import load_dotenv

# app 패키지 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.application.use_cases import QASearchUseCase
from app.infrastructure.repositories import QdrantRetriever, SentenceTransformerEmbedder
from app.infrastructure.guards import HallucinationGuard

# ====== 설정 로드 ======
load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "qa_collection")
EMBED_MODEL = os.getenv("EMBED_MODEL", "snunlp/KR-SBERT-V40K-klueNLI-augSTS")
SIM_THRESHOLD = float(os.getenv("SIM_THRESHOLD", "0.75"))
TOP_K = int(os.getenv("TOP_K", "3"))

# ====== FastAPI ======
app = FastAPI(title="Vibe QA Bot API", version="1.0.0")

# 프론트 도메인 허용 (필요 시 도메인 제한)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에선 도메인 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== 싱글톤 리소스 (클린 아키텍처 적용) ======
_embedder: Optional[SentenceTransformerEmbedder] = None
_retriever: Optional[QdrantRetriever] = None
_use_case: Optional[QASearchUseCase] = None
_qc: Optional[QdrantClient] = None

def get_qdrant() -> QdrantClient:
    global _qc
    if _qc is None:
        _qc = QdrantClient(url=QDRANT_URL)
    return _qc

def get_embedder() -> SentenceTransformerEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformerEmbedder(EMBED_MODEL)
    return _embedder

def get_retriever() -> QdrantRetriever:
    global _retriever
    if _retriever is None:
        _retriever = QdrantRetriever(
            client=get_qdrant(),
            embedder=get_embedder(),
            collection=QDRANT_COLLECTION
        )
    return _retriever

def get_use_case() -> QASearchUseCase:
    global _use_case
    if _use_case is None:
        from app.application.gemini_rewriter import GeminiQueryRewriter
        
        guard = HallucinationGuard(threshold=SIM_THRESHOLD)
        rewriter = GeminiQueryRewriter()  # Gemini API 연결
        
        _use_case = QASearchUseCase(
            retriever=get_retriever(),
            guard=guard,
            top_k=TOP_K,
            rewriter=rewriter  # Gemini Rewriter 주입
        )
    return _use_case

# ====== 스키마 ======
class AskReq(BaseModel):
    query: str

class TopKItem(BaseModel):
    question: str
    score: float

class AskRes(BaseModel):
    answer: str
    score: float
    matched_question: str
    sources: List[str] = []  # 프론트엔드 계약에 맞춤
    topk: List[TopKItem] = []

# ====== 유틸 ======
def write_log(record: dict):
    try:
        os.makedirs("logs", exist_ok=True)
        with open("logs/queries.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass

# ====== 라우팅 ======
@app.get("/healthz")
def healthz():
    # 모델/DB 핑
    _ = get_embedder().embed(["ping"])
    _ = get_qdrant().get_collections()
    return {"ok": True}

@app.on_event("startup")
def on_startup():
    # 워밍업: 콜드스타트 비용 최소화
    try:
        _ = healthz()
    except Exception:
        pass

@app.post("/ask", response_model=AskRes)
def ask(req: AskReq):
    q = req.query.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Empty query")

    try:
        # UseCase를 통한 검색 (클린 아키텍처 적용)
        use_case = get_use_case()
        result = use_case.search(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    # 로깅
    write_log({
        "ts": int(time.time()),
        "query": q,
        "score": result.score,
        "matched_question": result.matched_question,
        "verdict": "ok" if result.is_valid else "fallback",
    })

    return AskRes(
        answer=result.answer,
        score=result.score,
        matched_question=result.matched_question,
        sources=result.sources,
        topk=[]  # 필요시 UseCase에서 topk도 반환하도록 확장 가능
    )
