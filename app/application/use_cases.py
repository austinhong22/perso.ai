"""Application use cases - business logic orchestration."""
from typing import List
from app.domain.entities import SearchResult, QAPair
from app.domain.repositories import Retriever
from app.infrastructure.guards import HallucinationGuard


class QASearchUseCase:
    """Q&A 검색 유스케이스 (OCP 준수 - 리트리버/가드 교체 가능)."""
    
    def __init__(self, retriever: Retriever, guard: HallucinationGuard, top_k: int = 3):
        self.retriever = retriever
        self.guard = guard
        self.top_k = top_k
    
    def search(self, query: str) -> SearchResult:
        """
        사용자 쿼리에 대한 답변 검색 및 가드 적용.
        
        Args:
            query: 사용자 질문
            
        Returns:
            SearchResult (answer, score, matched_question, sources, is_valid)
        """
        # 1) 벡터 검색
        results: List[QAPair] = self.retriever.search(query, top_k=self.top_k)
        
        if not results:
            # 검색 결과 없음
            return SearchResult(
                answer=self.guard.get_fallback_message(),
                score=0.0,
                matched_question="",
                sources=[],
                is_valid=False
            )
        
        # 2) Top-1 결과
        top = results[0]
        
        # 3) 임계값 가드 적용
        is_valid = self.guard.is_valid(top.score or 0.0)
        
        if not is_valid:
            return SearchResult(
                answer=self.guard.get_fallback_message(),
                score=top.score or 0.0,
                matched_question="",
                sources=[],
                is_valid=False
            )
        
        # 4) 유효한 결과 반환
        return SearchResult(
            answer=top.answer,
            score=top.score or 0.0,
            matched_question=top.question,
            sources=[f"Q: {top.question}", f"A: {top.answer}"],
            is_valid=True
        )


