"""Domain entities - core business objects."""
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class QAPair:
    """Q&A 쌍 엔티티."""
    question: str
    answer: str
    score: Optional[float] = None


@dataclass
class SearchResult:
    """검색 결과 엔티티."""
    answer: str
    score: float
    matched_question: str
    sources: List[str]
    is_valid: bool  # 임계값 통과 여부


