"""Domain repository interfaces - define contracts for data access."""
from abc import ABC, abstractmethod
from typing import List
from app.domain.entities import QAPair


class Retriever(ABC):
    """벡터 검색 리트리버 인터페이스 (OCP 준수)."""
    
    @abstractmethod
    def search(self, query: str, top_k: int = 3) -> List[QAPair]:
        """
        쿼리에 대한 상위 K개 QA 쌍 검색.
        
        Args:
            query: 사용자 질문
            top_k: 상위 K개 결과
            
        Returns:
            QAPair 리스트 (score 포함)
        """
        pass
    

class Embedder(ABC):
    """임베딩 생성 인터페이스 (OCP 준수)."""
    
    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        텍스트를 벡터로 임베딩.
        
        Args:
            texts: 임베딩할 텍스트 리스트
            
        Returns:
            벡터 리스트
        """
        pass


