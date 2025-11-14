"""Infrastructure repositories - concrete implementations."""
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from app.domain.entities import QAPair
from app.domain.repositories import Retriever, Embedder


class QdrantRetriever(Retriever):
    """Qdrant 기반 벡터 검색 구현체."""
    
    def __init__(self, client: QdrantClient, embedder: Embedder, collection: str):
        self.client = client
        self.embedder = embedder
        self.collection = collection
    
    def search(self, query: str, top_k: int = 3) -> List[QAPair]:
        """쿼리에 대한 상위 K개 QA 쌍 검색."""
        qv = self.embedder.embed([query])[0]
        results = self.client.search(
            collection_name=self.collection,
            query_vector=qv,
            limit=top_k,
        )
        
        pairs = []
        for r in results:
            payload = r.payload or {}
            pairs.append(QAPair(
                question=payload.get("question", ""),
                answer=payload.get("answer", ""),
                score=float(r.score)
            ))
        return pairs


class SentenceTransformerEmbedder(Embedder):
    """SentenceTransformer 기반 임베딩 구현체."""
    
    def __init__(self, model_name: str = "snunlp/KR-SBERT-V40K-klueNLI-augSTS"):
        self._model: Optional[SentenceTransformer] = None
        self.model_name = model_name
    
    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            # 메모리 절약: device 명시, 모델 로딩 최적화
            import os
            os.environ["TOKENIZERS_PARALLELISM"] = "false"  # 경고 방지
            self._model = SentenceTransformer(
                self.model_name,
                device="cpu",  # CPU 명시 (GPU 없음)
            )
        return self._model
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """텍스트를 벡터로 임베딩."""
        # 메모리 절약: batch_size를 1로 줄임 (Render Free 플랜 대응)
        vecs = self.model.encode(
            texts,
            batch_size=1,  # 64 → 1 (메모리 절약)
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,  # 로그 줄이기
        )
        return vecs.tolist()


