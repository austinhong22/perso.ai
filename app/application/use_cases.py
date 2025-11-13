"""Application use cases - business logic orchestration."""
from typing import Optional
import re
from app.domain.entities import SearchResult, QAPair
from app.domain.repositories import Retriever
from app.infrastructure.guards import HallucinationGuard
from app.application.gemini_rewriter import GeminiQueryRewriter


class QASearchUseCase:
    """Q&A 검색 유스케이스 (Gemini Query Rewriting + 동적 Ensemble)."""
    
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
    
    def _get_ensemble_weights(self, query: str) -> tuple[float, float]:
        """
        질문 유형에 따라 Ensemble 가중치를 동적으로 결정.
        
        Args:
            query: 사용자 질문
            
        Returns:
            (original_weight, rewritten_weight) 튜플
        """
        # 1) 정형 질문 패턴 (존댓말, 의문사)
        formal_patterns = r"무엇인가요|어떻게|어떤.{1,5}인가요|얼마인가요|누구|언제|어디|입니까"
        if re.search(formal_patterns, query):
            return (0.95, 0.05)  # 원본 신뢰 (이미 정형화됨)
        
        # 2) 매우 짧은 질문 (< 5자)
        if len(query.strip()) < 5:
            return (0.4, 0.6)  # Gemini 약간 신뢰
        
        # 3) 구어체/반말 패턴
        informal_patterns = r"뭐야|뭐임|뭐예요|얼마야|있어\?|해\?|필요해|지원해|알려줘|설명해줘|가르쳐줘|말해줘|뭐하는|무슨|어떤|이거|그거|프로젝트"
        if re.search(informal_patterns, query, flags=re.IGNORECASE):
            return (0.1, 0.9)  # Gemini 강력 신뢰 (비정형 → 정형화 필수)
        
        # 4) 기본값
        return (0.5, 0.5)  # 균형
    
    def search(self, query: str) -> SearchResult:
        """
        사용자 쿼리에 대한 답변 검색 및 가드 적용.
        Ensemble 방식: 원본 질문 + Gemini 정규화 질문의 검색 결과를 결합.
        
        Args:
            query: 사용자 질문
            
        Returns:
            SearchResult (answer, score, matched_question, sources, is_valid)
        """
        # 1) Gemini API로 관련성 체크 및 정규화
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
        
        # 2) Ensemble 검색: 원본 + 정규화 질문 모두 검색 (동적 가중치)
        # 2-1) 동적 가중치 결정
        original_weight, rewritten_weight = self._get_ensemble_weights(query)
        
        # 2-2) 원본 질문으로 검색 (실제 벡터 유사도)
        original_candidates = self.retriever.search(query, top_k=self.top_k)
        
        # 2-3) 정규화된 질문으로 검색 (보완적 검색)
        rewritten_candidates = self.retriever.search(rewritten_query, top_k=self.top_k)
        
        # 2-4) 두 검색 결과를 결합 (동적 가중치 적용)
        from typing import Dict
        combined_scores: Dict[str, float] = {}
        candidate_map: Dict[str, QAPair] = {}
        
        # 원본 검색 결과 (동적 가중치)
        for candidate in original_candidates:
            combined_scores[candidate.question] = (candidate.score or 0.0) * original_weight
            candidate_map[candidate.question] = candidate
        
        # 정규화 검색 결과 (동적 가중치, 기존 점수에 추가)
        for candidate in rewritten_candidates:
            if candidate.question in combined_scores:
                combined_scores[candidate.question] += (candidate.score or 0.0) * rewritten_weight
            else:
                combined_scores[candidate.question] = (candidate.score or 0.0) * rewritten_weight
                candidate_map[candidate.question] = candidate
        
        # 2-5) Top-K 후보 선택 (Cross-Encoder 입력용)
        if not combined_scores:
            ensemble_candidates = []
        else:
            # Ensemble 점수 상위 Top-K 선택
            sorted_questions = sorted(
                combined_scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:self.top_k]
            
            ensemble_candidates = [
                QAPair(
                    question=q,
                    answer=candidate_map[q].answer,
                    score=score
                )
                for q, score in sorted_questions
            ]
        
        # 3) 최종 후보 선택 (Ensemble 결과 사용)
        candidates = ensemble_candidates
        
        # 4) 최고 점수 결과 선택
        best_result: Optional[QAPair] = candidates[0] if candidates else None
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
                f"Score: {best_score:.3f}"
            ],
            is_valid=True
        )


