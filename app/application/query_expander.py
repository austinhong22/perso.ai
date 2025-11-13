"""Query Expansion - 구어체/반말을 존댓말/완전형으로 확장."""
import re
from typing import List


class QueryExpander:
    """질문을 정규화하고 다양한 변형을 생성하여 검색 정확도를 높입니다."""
    
    # 반말 → 존댓말 매핑
    INFORMAL_TO_FORMAL = {
        r"뭐야\??": "무엇인가요?",
        r"뭐임\??": "무엇인가요?",
        r"뭐예요\??": "무엇인가요?",
        r"뭐하는거야\??": "어떤 서비스인가요?",
        r"뭐하는거예요\??": "어떤 서비스인가요?",
        r"뭐하는건데\??": "어떤 서비스인가요?",
        r"알려줘": "알려주세요",
        r"설명해줘": "설명해주세요",
        r"말해줘": "말해주세요",
        r"어떻게\s*해\??": "어떻게 하나요?",
        r"어떻게\s*문의해\??": "어떻게 문의하나요?",
        r"얼마야\??": "얼마인가요?",
        r"있어\??": "있나요?",
        r"있어요\??": "있나요?",
        r"되\??$": "되나요?",
        r"필요해\??": "필요한가요?",
        r"지원해\??": "지원하나요?",
        r"가능해\??": "가능한가요?",
    }
    
    # 브랜드명 정규화
    BRAND_VARIATIONS = {
        r"persoai|퍼소ai|퍼소|perso": "Perso.ai",
    }
    
    def normalize_brand(self, text: str) -> str:
        """브랜드명을 표준 형태로 정규화."""
        result = text
        for pattern, replacement in self.BRAND_VARIATIONS.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result
    
    def formalize_tone(self, text: str) -> str:
        """반말을 존댓말로 변환."""
        result = text
        for pattern, replacement in self.INFORMAL_TO_FORMAL.items():
            result = re.sub(pattern, replacement, result)
        return result
    
    def expand(self, query: str, max_variants: int = 3) -> List[str]:
        """
        쿼리를 확장하여 여러 변형 생성.
        
        Args:
            query: 원본 질문
            max_variants: 최대 변형 개수
            
        Returns:
            [원본, 브랜드 정규화, 존댓말 변환, 둘 다 적용] 리스트
        """
        variants = [query]  # 항상 원본 포함
        
        # 변형 1: 브랜드명 정규화
        normalized = self.normalize_brand(query)
        if normalized != query and normalized not in variants:
            variants.append(normalized)
        
        # 변형 2: 존댓말 변환
        formal = self.formalize_tone(query)
        if formal != query and formal not in variants:
            variants.append(formal)
        
        # 변형 3: 브랜드 정규화 + 존댓말
        both = self.formalize_tone(self.normalize_brand(query))
        if both != query and both not in variants:
            variants.append(both)
        
        return variants[:max_variants]
    
    def explain(self, query: str) -> str:
        """디버깅용: 쿼리 확장 과정 설명."""
        variants = self.expand(query)
        return f"Original: '{query}'\nExpanded to {len(variants)} variants:\n" + "\n".join(
            f"  {i+1}. {v}" for i, v in enumerate(variants)
        )

