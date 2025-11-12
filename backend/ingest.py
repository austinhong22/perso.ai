# backend/ingest.py
import re
import hashlib
from typing import List
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
import os

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("QDRANT_COLLECTION", "qa_collection")
EMBED_DIM = int(os.getenv("EMBED_DIM", 768))  # ko-SBERT 계열 보통 768

# ---------- 1) 파싱 & 클린업 ----------

def _clean_text(s: str) -> str:
    s = re.sub(r"\s+", " ", s or "").strip()
    # 맨 앞의 'Q.' / 'A.' 제거
    s = re.sub(r"^[QA]\.\s*", "", s)
    return s

def parse_qa_from_excel(path: str, text_col: str = "Unnamed: 2") -> pd.DataFrame:
    df = pd.read_excel(path)
    if text_col not in df.columns:
        raise ValueError(f"엑셀에 '{text_col}' 컬럼이 없습니다. 실제 컬럼: {df.columns.tolist()}")
    
    series = df[text_col].astype(str).fillna("")
    pairs = []
    pending_q = None
    
    for raw in series:
        if raw.startswith("Q."):
            pending_q = _clean_text(raw)
        elif raw.startswith("A.") and pending_q:
            ans = _clean_text(raw)
            if pending_q and ans:
                pairs.append({"question": pending_q, "answer": ans})
            pending_q = None
        else:
            # 빈 줄/기타 텍스트는 무시
            continue
    
    qa_df = pd.DataFrame(pairs)
    # 결측/중복 제거 + 재정규화
    qa_df = qa_df.dropna(subset=["question", "answer"])
    qa_df["question"] = qa_df["question"].map(_clean_text)
    qa_df["answer"] = qa_df["answer"].map(_clean_text)
    qa_df = qa_df.drop_duplicates(subset=["question"]).reset_index(drop=True)
    
    if len(qa_df) == 0:
        raise ValueError("파싱 결과가 비어 있습니다. 엑셀 구조/컬럼을 확인하세요.")
    
    return qa_df

# ---------- 2) 임베딩 ----------

_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        # 한국어 특화 모델. 필요에 따라 다른 ko-SBERT로 교체 가능
        # e.g., "jhgan/ko-sbert-sts", "snunlp/KR-SBERT-V40K-klueNLI-augSTS"
        _model = SentenceTransformer("jhgan/ko-sroberta-multitask")
    return _model

def embed_batch(texts: List[str], batch_size: int = 64) -> np.ndarray:
    model = get_model()
    # normalize_embeddings=True -> 코사인 거리 계산 시 안정적
    # return (N, D) ndarray
    return model.encode(
        texts,
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

# ---------- 3) Qdrant 업서트 ----------

def ensure_collection(client: QdrantClient, name: str, size: int):
    try:
        client.get_collection(name)
    except Exception:
        client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(
                size=size,
                distance=models.Distance.COSINE
            ),
        )

def make_id(s: str) -> int:
    # 질문 해시를 id로 사용 (idempotent upsert)
    h = hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]
    return int(h, 16)  # Qdrant는 int id 허용

def upsert_qa(
    client: QdrantClient,
    name: str,
    vectors: np.ndarray,
    rows: List[dict],
):
    points = []
    for vec, row in zip(vectors, rows):
        points.append(
            models.PointStruct(
                id=make_id(row["question"]),
                vector=vec.tolist(),
                payload={"question": row["question"], "answer": row["answer"]},
            )
        )
    client.upsert(collection_name=name, points=points)

# ---------- 4) 엔트리 포인트 ----------

def main():
    # 1) 파싱
    qa_df = parse_qa_from_excel("Q&A.xlsx", text_col="Unnamed: 2")
    print(f"[PARSE] {len(qa_df)} QA pairs")
    
    # 2) 임베딩
    vectors = embed_batch(qa_df["question"].tolist())
    if vectors.shape[1] != EMBED_DIM:
        # 환경 변수/컬렉션 차원 불일치 체크
        raise ValueError(f"임베딩 차원({vectors.shape[1]})과 EMBED_DIM({EMBED_DIM})이 다릅니다. .env를 수정하세요.")
    
    # 3) Qdrant 업서트
    qc = QdrantClient(url=QDRANT_URL)
    ensure_collection(qc, COLLECTION, size=EMBED_DIM)
    upsert_qa(qc, COLLECTION, vectors, qa_df.to_dict(orient="records"))
    print(f"[OK] upsert {len(qa_df)} points → {COLLECTION}")

if __name__ == "__main__":
    main()


