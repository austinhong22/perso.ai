"""Query Expansion - 구어체/반말을 존댓말/완전형으로 확장."""
import re
from typing import List


class QueryExpander:
    """질문을 정규화하고 다양한 변형을 생성하여 검색 정확도를 높입니다."""
    
    # 반말 → 존댓말 매핑
    INFORMAL_TO_FORMAL = {
        # 기본 의문사
        r"뭐야\??": "무엇인가요?",
        r"뭐임\??": "무엇인가요?",
        r"뭐예요\??": "무엇인가요?",
        r"뭔데\??": "무엇인가요?",
        r"뭐하는거야\??": "어떤 서비스인가요?",
        r"뭐하는거예요\??": "어떤 서비스인가요?",
        r"뭐하는건데\??": "어떤 서비스인가요?",
        
        # 요청/설명
        r"알려줘": "알려주세요",
        r"설명해줘": "설명해주세요",
        r"말해줘": "말해주세요",
        r"가르쳐줘": "가르쳐주세요",
        
        # 방법/절차
        r"어떻게\s*해\??": "어떻게 하나요?",
        r"어떻게\s*문의해\??": "어떻게 문의하나요?",
        r"어디서\s*해\??": "어디서 하나요?",
        
        # 가격/수량
        r"얼마야\??": "얼마인가요?",
        r"얼마예요\??": "얼마인가요?",
        r"가격이?\s*얼마": "가격은 얼마인가요",
        r"몇\s*개": "몇 개인가요",
        r"몇\s*명": "몇 명인가요",
        
        # 존재/가능
        r"있어\??": "있나요?",
        r"있어요\??": "있나요?",
        r"있니\??": "있나요?",
        r"되\??$": "되나요?",
        r"되요\??": "되나요?",
        r"돼\??": "되나요?",
        r"가능해\??": "가능한가요?",
        r"가능해요\??": "가능한가요?",
        
        # 필요/요구
        r"필요해\??": "필요한가요?",
        r"필요해요\??": "필요한가요?",
        r"해야\s*해\??": "해야 하나요?",
        
        # 지원/제공
        r"지원해\??": "지원하나요?",
        r"지원해요\??": "지원하나요?",
        r"제공해\??": "제공하나요?",
        r"쓸\s*수\s*있어\??": "사용할 수 있나요?",
        
        # 문의/연락
        r"문의해\??": "문의하나요?",
        r"연락해\??": "연락하나요?",
        r"물어봐\??": "물어보나요?",
    }
    
    # 도메인 특화 동의어 (Perso.ai 과제 전용)
    DOMAIN_SYNONYMS = {
        r"요금(?!제)": "요금제",  # "요금" → "요금제" (단, "요금제"는 그대로)
        r"가격": "요금제",
        r"비용": "요금제",
        r"몇\s*개": "몇 개",
        r"회원가입": "가입",
        r"고객센터": "문의",
        r"상담": "문의",
        r"기능": "주요 기능",
        r"특징": "주요 기능",
    }
    
    # 브랜드명 정규화
    BRAND_VARIATIONS = {
        r"persoai": "Perso.ai",
        r"퍼소\s*ai": "Perso.ai",
        r"퍼소": "Perso.ai",
        r"perso(?!\.ai)": "Perso.ai",  # perso만 매칭 (perso.ai는 제외)
        r"이스트(?!소프트)": "이스트소프트",
    }
    
    def normalize_brand(self, text: str) -> str:
        """브랜드명을 표준 형태로 정규화."""
        result = text
        for pattern, replacement in self.BRAND_VARIATIONS.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result
    
    def normalize_domain(self, text: str) -> str:
        """도메인 특화 동의어를 정규화."""
        result = text
        for pattern, replacement in self.DOMAIN_SYNONYMS.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result
    
    def formalize_tone(self, text: str) -> str:
        """반말을 존댓말로 변환."""
        result = text
        for pattern, replacement in self.INFORMAL_TO_FORMAL.items():
            result = re.sub(pattern, replacement, result)
        return result
    
    def fix_typos(self, text: str) -> str:
        """흔한 오타 패턴 수정 (one-edit distance 기반)."""
        # 자주 발생하는 오타 패턴
        typo_patterns = {
            r"무엇이나요": "무엇인가요",
            r"어떻케": "어떻게",
            r"어떻헤": "어떻게",
            r"뭐에요": "뭐예요",
            r"얼마에요": "얼마예요",
            r"필요하나요": "필요한가요",
            r"perso\.ai": "Perso.ai",  # 소문자 수정
            r"persoa\.ai": "Perso.ai",  # 오타
        }
        result = text
        for pattern, replacement in typo_patterns.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result
    
    def expand(self, query: str, max_variants: int = 5) -> List[str]:
        """
        쿼리를 확장하여 여러 변형 생성.
        
        Args:
            query: 원본 질문
            max_variants: 최대 변형 개수
            
        Returns:
            [원본, 오타수정, 브랜드정규화, 도메인정규화, 존댓말, 전체적용] 리스트
        """
        variants = [query]  # 항상 원본 포함
        
        # 변형 1: 오타 수정
        typo_fixed = self.fix_typos(query)
        if typo_fixed != query and typo_fixed not in variants:
            variants.append(typo_fixed)
        
        # 변형 2: 브랜드명 정규화
        normalized = self.normalize_brand(typo_fixed)
        if normalized != typo_fixed and normalized not in variants:
            variants.append(normalized)
        
        # 변형 3: 도메인 동의어 정규화
        domain = self.normalize_domain(normalized)
        if domain != normalized and domain not in variants:
            variants.append(domain)
        
        # 변형 4: 존댓말 변환
        formal = self.formalize_tone(domain)
        if formal != domain and formal not in variants:
            variants.append(formal)
        
        # 변형 5: 전체 적용 (오타→브랜드→도메인→존댓말)
        full = self.formalize_tone(
            self.normalize_domain(
                self.normalize_brand(
                    self.fix_typos(query)
                )
            )
        )
        if full not in variants:
            variants.append(full)
        
        return variants[:max_variants]
    
    def explain(self, query: str) -> str:
        """디버깅용: 쿼리 확장 과정 설명."""
        variants = self.expand(query)
        return f"Original: '{query}'\nExpanded to {len(variants)} variants:\n" + "\n".join(
            f"  {i+1}. {v}" for i, v in enumerate(variants)
        )

