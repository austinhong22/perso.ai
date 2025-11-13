"""Application use cases - business logic orchestration."""
from typing import Optional
from app.domain.entities import SearchResult, QAPair
from app.domain.repositories import Retriever
from app.infrastructure.guards import HallucinationGuard
from app.application.gemini_rewriter import GeminiQueryRewriter


class QASearchUseCase:
    """Q&A 검색 유스케이스 (Gemini API 기반 Query Rewriting)."""
    
    def __init__(
        self, 
        retriever: Retriever, 
        guard: HallucinationGuard, 
        top_k: int = 5,
        rewriter: Optional[GeminiQueryRewriter] = None
    ):
        self.retriever = retriever
        self.guard = guard
        self.top_k = top_k
        self.rewriter = rewriter or GeminiQueryRewriter()
    
    def search(self, query: str) -> SearchResult:
        """
        사용자 쿼리에 대한 답변 검색 및 가드 적용.
        Gemini API로 구어체 → 정식 질문 변환 후 벡터 검색.
        
        Args:
            query: 사용자 질문
            
        Returns:
            SearchResult (answer, score, matched_question, sources, is_valid)
        """
        # 1) Gemini API로 구어체 → 정식 질문 변환
        rewritten_query = self.rewriter.rewrite(query)
        
        # 1-1) Perso.ai와 관련 없는 질문 필터링
        if rewritten_query == "[NO_MATCH]":
            return SearchResult(
                answer=self.guard.get_fallback_message(),
                score=0.0,
                matched_question="",
                sources=[],
                is_valid=False
            )
        
        # 2) 변환된 질문으로 벡터 검색
        candidates = self.retriever.search(rewritten_query, top_k=self.top_k)
        
        # 3) 최고 점수 결과 선택
        best_result: Optional[QAPair] = candidates[0] if candidates else None
        best_score = best_result.score or 0.0 if best_result else 0.0
        
        # 4) 결과 없음 처리
        if not best_result:
            return SearchResult(
                answer=self.guard.get_fallback_message(),
                score=0.0,
                matched_question="",
                sources=[],
                is_valid=False
            )
        
        # 5) 동적 임계값 가드 적용
        is_valid = self.guard.is_valid(best_score, query=query)
        
        if not is_valid:
            return SearchResult(
                answer=self.guard.get_fallback_message(),
                score=best_score,
                matched_question="",
                sources=[],
                is_valid=False
            )
        
        # 6) 유효한 결과 반환
        return SearchResult(
            answer=best_result.answer,
            score=best_score,
            matched_question=best_result.question,
            sources=[
                f"Q: {best_result.question}",
                f"A: {best_result.answer}",
                f"Score: {best_score:.3f}"
            ],
            is_valid=True
        )


