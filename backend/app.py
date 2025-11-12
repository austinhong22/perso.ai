import os, json, time
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# ====== 설정 로드 ======
load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "qa_collection")
SIM_THRESHOLD = float(os.getenv("SIM_THRESHOLD", "0.83"))
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

# ====== 싱글톤 리소스 ======
_model: Optional[SentenceTransformer] = None
_qc: Optional[QdrantClient] = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        # 한국어 의미검색 특화 모델 (ingest.py와 동일 모델 사용)
        _model = SentenceTransformer("jhgan/ko-sroberta-multitask")
    return _model

def get_qdrant() -> QdrantClient:
    global _qc
    if _qc is None:
        _qc = QdrantClient(url=QDRANT_URL)
    return _qc

def embed(texts: List[str]) -> List[List[float]]:
    model = get_model()
    vecs = model.encode(
        texts,
        batch_size=64,
        convert_to_numpy=True,
        normalize_embeddings=True,  # 코사인 거리 안정화
    )
    return vecs.tolist()

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
    topk: List[TopKItem] = []

# ====== 유틸 ======
def search_topk(query: str, k: int = TOP_K):
    qc = get_qdrant()
    qv = embed([query])[0]
    res = qc.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=qv,
        limit=k,
    )
    return res

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
    _ = embed(["ping"])
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
        res = search_topk(q, TOP_K)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    if not res:
        raise HTTPException(status_code=404, detail="No result")

    # Top-k 정리
    topk_list = []
    for r in res:
        payload = r.payload or {}
        topk_list.append(TopKItem(
            question=payload.get("question", ""),
            score=float(r.score),
        ))

    top = res[0]
    top_payload = top.payload or {}
    top_score = float(top.score)
    top_q = top_payload.get("question", "")
    top_a = top_payload.get("answer", "")

    # 임계값 가드: 낮은 점수는 "데이터셋에 없음"
    if top_score < SIM_THRESHOLD:
        answer = "죄송해요, 제가 가지고 있는 데이터셋에는 해당 내용이 없어요. 비슷한 질문으로 다시 시도해보세요."
        matched_question = ""
    else:
        answer = top_a
        matched_question = top_q

    # 로깅
    write_log({
        "ts": int(time.time()),
        "query": q,
        "score": top_score,
        "matched_question": matched_question,
        "verdict": "ok" if matched_question else "fallback",
        "topk": [{"q": t.question, "score": t.score} for t in topk_list],
    })

    return AskRes(
        answer=answer,
        score=top_score,
        matched_question=matched_question,
        topk=topk_list
    )
