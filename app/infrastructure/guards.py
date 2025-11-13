"""Hallucination guard - similarity threshold and source reference."""
import re
from typing import Optional
from app.infrastructure.config import settings


class HallucinationGuard:
    """Guard against hallucinations using similarity threshold and source reference."""
    
    def __init__(self, threshold: Optional[float] = None, use_dynamic: bool = True):
        self.base_threshold = threshold or settings.similarity_threshold
        self.use_dynamic = use_dynamic
        self.fallback_message = "죄송해요, 제가 가지고 있는 데이터셋에는 해당 내용이 없어요. 비슷한 질문으로 다시 시도해보세요."
    
    def get_dynamic_threshold(self, query: str) -> float:
        """
        질문 유형에 따라 동적 임계값 조정.
        
        - 매우 짧은 질문(< 5자): 엄격 (0.85) - 모호함 방지
        - 구어체/반말: 관대 (0.55)
        - 의문사 있는 질문: 기본 (0.75)
        - 명사형/짧은 질문: 중간 (0.65)
        """
        if not self.use_dynamic:
            return self.base_threshold
        
        # 매우 짧은 질문(< 5자): 엄격하게 처리 (모호함 방지)
        if len(query.strip()) < 5:
            return 0.85  # 엄격
        
        # 구어체/반말 패턴 감지: 관대하게 처리 (5자 이상)
        informal_patterns = r"뭐야|뭐임|뭐예요|얼마야|있어\?|해\?|필요해|지원해|알려줘|설명해줘|가르쳐줘|말해줘|뭐하는|무슨|어떤|이거"
        if re.search(informal_patterns, query, flags=re.IGNORECASE):
            return 0.35  # 매우 관대 (Gemini가 의미 필터링 수행)
        
        # 의문사 있는 정식 질문: 기본
        if re.search(r"무엇인가요|어떻게|얼마인가요|누구|언제|어디|왜", query):
            return self.base_threshold
        
        # 명사형/키워드 질문: 중간
        if len(query.split()) <= 3:
            return 0.65
        
        return self.base_threshold
    
    def is_valid(self, similarity_score: float, query: str = "") -> bool:
        """
        유사도 점수가 임계값 이상인지 확인 (동적 임계값 적용).
        
        Args:
            similarity_score: 유사도 점수 (0.0 to 1.0)
            query: 사용자 질문 (동적 임계값 계산용)
            
        Returns:
            임계값 통과 여부
        """
        threshold = self.get_dynamic_threshold(query) if query else self.base_threshold
        return similarity_score >= threshold
        
    def get_fallback_message(self) -> str:
        """임계값 미달 시 반환할 메시지."""
        return self.fallback_message


