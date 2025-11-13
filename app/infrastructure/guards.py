"""Hallucination guard - similarity threshold and source reference."""
from typing import Optional
from app.infrastructure.config import settings


class HallucinationGuard:
    """Guard against hallucinations using similarity threshold and source reference."""
    
    def __init__(self, threshold: Optional[float] = None):
        self.threshold = threshold or settings.similarity_threshold
        self.fallback_message = "죄송해요, 제가 가지고 있는 데이터셋에는 해당 내용이 없어요. 비슷한 질문으로 다시 시도해보세요."
    
    def is_valid(self, similarity_score: float) -> bool:
        """
        유사도 점수가 임계값 이상인지 확인.
        
        Args:
            similarity_score: 유사도 점수 (0.0 to 1.0)
            
        Returns:
            임계값 통과 여부
        """
        return similarity_score >= self.threshold
    
    def get_fallback_message(self) -> str:
        """임계값 미달 시 반환할 메시지."""
        return self.fallback_message


