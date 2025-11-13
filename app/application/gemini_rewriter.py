"""Gemini API 기반 Query Rewriting (구어체 → 정식 질문 변환)"""
import os
from typing import Optional
import google.generativeai as genai


class GeminiQueryRewriter:
    """Gemini API를 사용한 구어체 → 정식 질문 변환"""
    
    # 13개 표준 질문 (Q&A 데이터셋)
    STANDARD_QUESTIONS = [
        "Perso.ai는 어떤 서비스인가요?",
        "Perso.ai의 주요 기능은 무엇인가요?",
        "Perso.ai는 어떤 기술을 사용하나요?",
        "Perso.ai의 사용자는 어느 정도인가요?",
        "Perso.ai를 사용하는 주요 고객층은 누구인가요?",
        "Perso.ai에서 지원하는 언어는 몇 개인가요?",
        "Perso.ai의 요금제는 어떻게 구성되어 있나요?",
        "Perso.ai는 어떤 기업이 개발했나요?",
        "이스트소프트는 어떤 회사인가요?",
        "Perso.ai의 기술적 강점은 무엇인가요?",
        "Perso.ai를 사용하려면 회원가입이 필요한가요?",
        "Perso.ai를 이용하려면 영상 편집 지식이 필요한가요?",
        "Perso.ai 고객센터는 어떻게 문의하나요?",
    ]
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash"):
        """
        Args:
            api_key: Gemini API 키 (없으면 환경변수에서 로드)
            model_name: Gemini 모델명 (기본: gemini-1.5-flash)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Few-shot 프롬프트 생성 (의도 분류 기반)"""
        questions_list = "\n".join([f"{i+1}. {q}" for i, q in enumerate(self.STANDARD_QUESTIONS)])
        
        return f"""당신은 Perso.ai 챗봇의 질문 변환 전문가입니다.
사용자의 구어체/반말 질문을 아래 13개 표준 질문 중 **의미적으로 관련된** 형태로 변환하세요.

[표준 질문 목록] (Perso.ai 서비스 관련 질문만 해당)
{questions_list}

[질문 의도 카테고리]
1. 서비스 소개: "뭐야", "뭐하는거야", "무슨 서비스", "어떤 프로젝트", "설명해줘" 
   → "Perso.ai는 어떤 서비스인가요?"

2. 주요 기능: "기능", "할 수 있어", "제공해", "뭐가 있어"
   → "Perso.ai의 주요 기능은 무엇인가요?"

3. 기술/강점: "기술", "어떻게 작동", "강점", "장점"
   → "Perso.ai는 어떤 기술을 사용하나요?" or "기술적 강점은 무엇인가요?"

4. 사용자/고객: "사용자", "고객", "누가 써", "어떤 사람"
   → "사용자는 어느 정도인가요?" or "주요 고객층은 누구인가요?"

5. 언어 지원: "언어", "몇 개", "어떤 언어"
   → "Perso.ai에서 지원하는 언어는 몇 개인가요?"

6. 가격/요금: "가격", "요금", "비용", "얼마"
   → "Perso.ai의 요금제는 어떻게 구성되어 있나요?"

7. 개발사/회사: "어느 회사", "누가 만들", "개발"
   → "Perso.ai는 어떤 기업이 개발했나요?" or "이스트소프트는 어떤 회사인가요?"

8. 사용 방법: "회원가입", "가입", "지식 필요", "어떻게 사용"
   → "회원가입이 필요한가요?" or "영상 편집 지식이 필요한가요?"

9. 고객센터/문의: "문의", "연락", "고객센터", "도움"
   → "Perso.ai 고객센터는 어떻게 문의하나요?"

[변환 규칙]
1. **먼저 질문이 Perso.ai 서비스와 관련이 있는지 판단하세요**
   - 관련 없는 질문(날씨, 일반 지식, 다른 주제 등): "[NO_MATCH]" 출력
   - Perso.ai 관련 질문: 아래 단계 진행

2. **질문 의도 파악 (Chain-of-Thought)**
   - 질문의 핵심 키워드 추출
   - 위 카테고리 중 가장 관련 있는 의도 선택
   - 해당 카테고리의 표준 질문으로 변환

3. **변환 실행**
   - 구어체 → 존댓말 변환
   - 브랜드명 정규화 (persoai/퍼소/perso/프로젝트 → Perso.ai)
   - "프로젝트", "이거", "그거" → "서비스"로 매핑
   - 변환된 질문만 출력 (설명 없이)

4. **관련 없는 질문 예시:**
   - 날씨, 시간, 뉴스 등 일반 정보
   - 코딩, 수학, 과학 등 일반 지식
   - 타 서비스/제품 관련 질문

[Few-shot 예시 - 서비스 소개 (카테고리 1)]
입력: "persoai가 뭐야?"
출력: Perso.ai는 어떤 서비스인가요?

입력: "이게 뭐하는거야"
출력: Perso.ai는 어떤 서비스인가요?

입력: "이게 뭐하는 프로젝트야"
출력: Perso.ai는 어떤 서비스인가요?

입력: "무슨 서비스야"
출력: Perso.ai는 어떤 서비스인가요?

입력: "어떤 서비스야"
출력: Perso.ai는 어떤 서비스인가요?

입력: "perso 설명해줘"
출력: Perso.ai는 어떤 서비스인가요?

[Few-shot 예시 - 주요 기능 (카테고리 2)]
입력: "주요 기능이 뭐야"
출력: Perso.ai의 주요 기능은 무엇인가요?

입력: "기능 뭐야?"
출력: Perso.ai의 주요 기능은 무엇인가요?

입력: "뭐 할 수 있어?"
출력: Perso.ai의 주요 기능은 무엇인가요?

입력: "어떤 기능 제공해?"
출력: Perso.ai의 주요 기능은 무엇인가요?

[Few-shot 예시 - 기술/강점 (카테고리 3)]
입력: "어떤 기술 써?"
출력: Perso.ai는 어떤 기술을 사용하나요?

입력: "기술적 강점이 뭐야"
출력: Perso.ai의 기술적 강점은 무엇인가요?

[Few-shot 예시 - 사용자/고객 (카테고리 4)]
입력: "사용자 얼마나 돼?"
출력: Perso.ai의 사용자는 어느 정도인가요?

입력: "주요 고객층은?"
출력: Perso.ai를 사용하는 주요 고객층은 누구인가요?

입력: "누가 주로 써?"
출력: Perso.ai를 사용하는 주요 고객층은 누구인가요?

[Few-shot 예시 - 언어 지원 (카테고리 5)]
입력: "언어 지원해?"
출력: Perso.ai에서 지원하는 언어는 몇 개인가요?

입력: "몇 개 언어 되는데?"
출력: Perso.ai에서 지원하는 언어는 몇 개인가요?

[Few-shot 예시 - 가격/요금 (카테고리 6)]
입력: "요금 얼마야?"
출력: Perso.ai의 요금제는 어떻게 구성되어 있나요?

입력: "가격이 얼마야"
출력: Perso.ai의 요금제는 어떻게 구성되어 있나요?

입력: "비용 얼마나 들어?"
출력: Perso.ai의 요금제는 어떻게 구성되어 있나요?

[Few-shot 예시 - 개발사/회사 (카테고리 7)]
입력: "어떤 회사가 만들었어?"
출력: Perso.ai는 어떤 기업이 개발했나요?

입력: "누가 개발했어?"
출력: Perso.ai는 어떤 기업이 개발했나요?

입력: "이스트소프트는 뭐하는 회사야?"
출력: 이스트소프트는 어떤 회사인가요?

[Few-shot 예시 - 사용 방법 (카테고리 8)]
입력: "회원가입 필요해?"
출력: Perso.ai를 사용하려면 회원가입이 필요한가요?

입력: "영상 편집 지식 필요해?"
출력: Perso.ai를 이용하려면 영상 편집 지식이 필요한가요?

[Few-shot 예시 - 고객센터/문의 (카테고리 9)]
입력: "문의하려면?"
출력: Perso.ai 고객센터는 어떻게 문의하나요?

입력: "고객센터 어디야?"
출력: Perso.ai 고객센터는 어떻게 문의하나요?

[관련 없는 질문 예시]
입력: "날씨가 어떤가요?"
출력: [NO_MATCH]

입력: "파이썬으로 크롤링하는 방법 알려줘"
출력: [NO_MATCH]

입력: "너 이름이 뭐야?"
출력: [NO_MATCH]

입력: "오늘 점심 뭐 먹지?"
출력: [NO_MATCH]

[중요]
- Perso.ai와 관련 없는 질문은 반드시 "[NO_MATCH]"로 응답하세요.
- Perso.ai 관련 질문은 위 13개 표준 질문 중 하나로만 변환하세요.
- 추가 설명이나 서술형은 제외하고 질문 형태로만 출력하세요.
"""
    
    def rewrite(self, query: str) -> str:
        """
        구어체 질문을 정식 질문으로 변환.
        
        Args:
            query: 사용자의 구어체 질문
            
        Returns:
            변환된 정식 질문 (관련 없는 질문은 "[NO_MATCH]" 반환)
        """
        if not query or not query.strip():
            return query
        
        try:
            prompt = f"{self.system_prompt}\n\n입력: \"{query}\"\n출력:"
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # 낮은 temperature로 일관성 유지
                    max_output_tokens=50,  # 짧은 질문만 생성
                )
            )
            
            rewritten = response.text.strip()
            
            # 후처리: 불필요한 따옴표 제거
            rewritten = rewritten.strip('"\'')
            
            # 빈 응답 시 NO_MATCH 처리
            if not rewritten:
                print(f"[Gemini] 빈 응답, NO_MATCH 반환: {query}")
                return "[NO_MATCH]"
            
            # NO_MATCH 감지
            if "[NO_MATCH]" in rewritten or "NO_MATCH" in rewritten:
                print(f"[Gemini] 관련 없는 질문: '{query}' → [NO_MATCH]")
                return "[NO_MATCH]"
            
            print(f"[Gemini] 변환: '{query}' → '{rewritten}'")
            return rewritten
            
        except Exception as e:
            # Gemini API 실패 시 원본 반환 (fallback)
            print(f"[Gemini] API 오류, 원본 사용: {e}")
            return query
    
    def rewrite_batch(self, queries: list[str]) -> list[str]:
        """
        여러 질문을 일괄 변환 (비동기 처리 시 유용).
        
        Args:
            queries: 질문 리스트
            
        Returns:
            변환된 질문 리스트
        """
        return [self.rewrite(q) for q in queries]

