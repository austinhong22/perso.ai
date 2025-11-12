# backend/smoke_check.py
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
import os

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("QDRANT_COLLECTION", "qa_collection")

_model = None

def embed_one(text: str):
    global _model
    if _model is None:
        _model = SentenceTransformer("jhgan/ko-sroberta-multitask")
    vec = _model.encode([text], convert_to_numpy=True, normalize_embeddings=True)[0]
    return vec.tolist()

def search(query: str, limit: int = 3):
    qc = QdrantClient(url=QDRANT_URL)
    res = qc.search(collection_name=COLLECTION, query_vector=embed_one(query), limit=limit)
    return [(r.payload.get("question",""), r.payload.get("answer",""), float(r.score)) for r in res]

if __name__ == "__main__":
    print("=== SAME (데이터에 실제 있는 질문) ===")
    results = search("Perso.ai는 어떤 서비스인가요?")
    for q, a, score in results:
        print(f"Score: {score:.4f}")
        print(f"Q: {q}")
        print(f"A: {a[:80]}...")
        print()
    
    print("\n=== SIMILAR (말만 바꾼 질문) ===")
    results = search("Perso.ai가 뭐예요?")
    for q, a, score in results:
        print(f"Score: {score:.4f}")
        print(f"Q: {q}")
        print(f"A: {a[:80]}...")
        print()
    
    print("\n=== OUT-OF-DOMAIN (무관 질문) ===")
    results = search("오늘 날씨가 어때요?")
    for q, a, score in results:
        print(f"Score: {score:.4f}")
        print(f"Q: {q}")
        print(f"A: {a[:80]}...")
        print()

