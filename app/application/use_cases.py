"""Application use cases - business logic orchestration."""
from typing import List, Optional
from app.domain.entities import SearchResult, QAPair
from app.domain.repositories import Retriever
from app.infrastructure.guards import HallucinationGuard
from app.application.query_expander import QueryExpander


class QASearchUseCase:
    """Q&A 검색 유스케이스 (OCP 준수 - 리트리버/가드 교체 가능)."""
    
    def __init__(
        self, 
        retriever: Retriever, 
        guard: HallucinationGuard, 
        top_k: int = 3,
        expander: Optional[QueryExpander] = None
    ):
        self.retriever = retriever
        self.guard = guard
        self.top_k = top_k
        self.expander = expander or QueryExpander()
    
    def search(self, query: str) -> SearchResult:
        """
        사용자 쿼리에 대한 답변 검색 및 가드 적용.
        Query Expansion을 통해 구어체/반말도 처리.
        
        Args:
            query: 사용자 질문
            
        Returns:
            SearchResult (answer, score, matched_question, sources, is_valid)
        """
        # 1) Query Expansion: 원본 + 정규화 변형 생성
        query_variants = self.expander.expand(query, max_variants=3)
        
        # 2) 각 변형에 대해 벡터 검색 후 최고 점수 선택
        best_result: Optional[QAPair] = None
        best_score = 0.0
        
        for variant in query_variants:
            results: List[QAPair] = self.retriever.search(variant, top_k=1)
            if results and (results[0].score or 0.0) > best_score:
                best_result = results[0]
                best_score = results[0].score or 0.0
        
        # 3) 결과 없음 처리
        if not best_result:
            return SearchResult(
                answer=self.guard.get_fallback_message(),
                score=0.0,
                matched_question="",
                sources=[],
                is_valid=False
            )
        
        # 4) 임계값 가드 적용
        is_valid = self.guard.is_valid(best_score)
        
        if not is_valid:
            return SearchResult(
                answer=self.guard.get_fallback_message(),
                score=best_score,
                matched_question="",
                sources=[],
                is_valid=False
            )
        
        # 5) 유효한 결과 반환
        return SearchResult(
            answer=best_result.answer,
            score=best_score,
            matched_question=best_result.question,
            sources=[f"Q: {best_result.question}", f"A: {best_result.answer}"],
            is_valid=True
        )


