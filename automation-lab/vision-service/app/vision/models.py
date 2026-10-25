from dataclasses import dataclass, asdict
from typing import Optional, Dict


@dataclass
class ElementCandidate:
    candidate_id: str
    source_strategy: str  # e.g. 'opencv', 'vision'
    element_type: Optional[str]  # 'button' | 'input' | 'link' | 'text' | 'icon' | 'unknown'
    semantic_text: Optional[str]
    role: Optional[str]
    center_point: Dict[str, int]  # {x:int, y:int}
    bbox: Dict[str, int]  # {x:int, y:int, width:int, height:int}
    confidence_score: float
    reasoning: Optional[str]
    meta: Dict[str, object]
    ocr_details: Optional[Dict[str, object]] = None

    def to_dict(self) -> Dict:
        return asdict(self)
