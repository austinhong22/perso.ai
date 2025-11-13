"""Application use cases - business logic orchestration."""
from typing import List, Optional
from app.domain.entities import SearchResult, QAPair
from app.domain.repositories import Retriever
from app.infrastructure.guards import HallucinationGuard
from app.application.query_expander import QueryExpander
from app.application.reranker import HybridReranker


class QASearchUseCase:
    """Q&A 검색 유스케이스 (OCP 준수 - 리트리버/가드 교체 가능)."""
    
    def __init__(
        self, 
        retriever: Retriever, 
        guard: HallucinationGuard, 
        top_k: int = 5,
        expander: Optional[QueryExpander] = None,
        reranker: Optional[HybridReranker] = None,
        use_reranking: bool = True
    ):
        self.retriever = retriever
        self.guard = guard
        self.top_k = top_k
        self.expander = expander or QueryExpander()
        self.reranker = reranker or HybridReranker()
        self.use_reranking = use_reranking
    
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
        query_variants = self.expander.expand(query, max_variants=5)
        
        # 2) 각 변형에 대해 벡터 검색 후 Top-k 수집
        all_candidates: List[QAPair] = []
        seen_questions = set()
        
        for variant in query_variants:
            results: List[QAPair] = self.retriever.search(variant, top_k=self.top_k)
            for r in results:
                # 중복 제거 (같은 질문이 여러 변형에서 검색될 수 있음)
                if r.question not in seen_questions:
                    all_candidates.append(r)
                    seen_questions.add(r.question)
        
        # 3) Reranking: 벡터 + 문자열 유사도 하이브리드 점수로 재정렬
        if self.use_reranking and all_candidates:
            all_candidates = self.reranker.rerank(query, all_candidates)
        
        # 4) 최고 점수 결과 선택
        best_result: Optional[QAPair] = all_candidates[0] if all_candidates else None
        best_score = best_result.score or 0.0 if best_result else 0.0
        
        # 5) 결과 없음 처리
        if not best_result:
            return SearchResult(
                answer=self.guard.get_fallback_message(),
                score=0.0,
                matched_question="",
                sources=[],
                is_valid=False
            )
        
        # 6) 동적 임계값 가드 적용
        is_valid = self.guard.is_valid(best_score, query=query)
        
        if not is_valid:
            return SearchResult(
                answer=self.guard.get_fallback_message(),
                score=best_score,
                matched_question="",
                sources=[],
                is_valid=False
            )
        
        # 7) 유효한 결과 반환
        return SearchResult(
            answer=best_result.answer,
            score=best_score,
            matched_question=best_result.question,
            sources=[
                f"Q: {best_result.question}",
                f"A: {best_result.answer}",
                f"Hybrid Score: {best_score:.3f}"
            ],
            is_valid=True
        )


