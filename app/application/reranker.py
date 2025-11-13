"""Reranker - 벡터 검색 결과를 문자열 유사도로 재정렬."""
from typing import List
from rapidfuzz import fuzz
from app.domain.entities import QAPair


class HybridReranker:
    """벡터 유사도 + 문자열 유사도 하이브리드 재랭킹."""
    
    def __init__(
        self,
        vector_weight: float = 0.7,
        string_weight: float = 0.3,
        string_threshold: float = 0.3
    ):
        """
        Args:
            vector_weight: 벡터 유사도 가중치 (기본 0.7)
            string_weight: 문자열 유사도 가중치 (기본 0.3)
            string_threshold: 문자열 유사도 최소 임계값
        """
        self.vector_weight = vector_weight
        self.string_weight = string_weight
        self.string_threshold = string_threshold
    
    def calculate_string_similarity(self, query: str, question: str) -> float:
        """
        문자열 유사도 계산 (token_sort_ratio 사용).
        단어 순서 무관, 형태소 변형에 강건.
        
        Returns:
            0.0 ~ 1.0 사이 유사도
        """
        similarity = fuzz.token_sort_ratio(query, question) / 100.0
        return similarity
    
    def rerank(self, query: str, candidates: List[QAPair]) -> List[QAPair]:
        """
        벡터 검색 결과를 하이브리드 점수로 재정렬.
        
        Args:
            query: 사용자 질문
            candidates: 벡터 검색 결과 (top-k)
            
        Returns:
            재랭킹된 QAPair 리스트 (hybrid_score 순)
        """
        if not candidates:
            return []
        
        reranked = []
        for candidate in candidates:
            # 벡터 유사도 (이미 계산됨)
            vector_score = candidate.score or 0.0
            
            # 문자열 유사도
            string_score = self.calculate_string_similarity(query, candidate.question)
            
            # 하이브리드 점수
            hybrid_score = (
                self.vector_weight * vector_score +
                self.string_weight * string_score
            )
            
            # 문자열 유사도가 너무 낮으면 페널티
            if string_score < self.string_threshold:
                hybrid_score *= 0.9  # 10% 감점
            
            # 기존 QAPair의 score를 hybrid_score로 업데이트
            reranked_pair = QAPair(
                question=candidate.question,
                answer=candidate.answer,
                score=hybrid_score
            )
            reranked.append(reranked_pair)
        
        # 하이브리드 점수 기준 내림차순 정렬
        reranked.sort(key=lambda x: x.score or 0.0, reverse=True)
        return reranked
    
    def explain(self, query: str, candidates: List[QAPair]) -> str:
        """디버깅용: 재랭킹 과정 설명."""
        lines = [f"Query: '{query}'", f"Reranking {len(candidates)} candidates:\n"]
        
        for i, candidate in enumerate(candidates, 1):
            vector_score = candidate.score or 0.0
            string_score = self.calculate_string_similarity(query, candidate.question)
            hybrid_score = (
                self.vector_weight * vector_score +
                self.string_weight * string_score
            )
            
            lines.append(
                f"{i}. Q: {candidate.question[:50]}...\n"
                f"   Vector: {vector_score:.3f}, String: {string_score:.3f}, "
                f"Hybrid: {hybrid_score:.3f}"
            )
        
        return "\n".join(lines)


