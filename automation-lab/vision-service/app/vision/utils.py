from typing import Dict, Optional
from .models import ElementCandidate
import uuid


def bbox_center(bbox: Dict[str, int]) -> Dict[str, int]:
    x = int(bbox.get('x', 0))
    y = int(bbox.get('y', 0))
    w = int(bbox.get('width', 0))
    h = int(bbox.get('height', 0))
    return {"x": x + w // 2, "y": y + h // 2}


def create_element_candidate(
    source_strategy: str,
    bbox: Dict[str, int],
    confidence_score: float,
    element_type: Optional[str] = None,
    semantic_text: Optional[str] = None,
    role: Optional[str] = None,
    reasoning: Optional[str] = None,
    meta: Optional[Dict] = None,
    candidate_id: Optional[str] = None,
    ocr_details: Optional[Dict] = None,
) -> ElementCandidate:
    if candidate_id is None:
        candidate_id = f"c_{uuid.uuid4().hex[:8]}"
    if meta is None:
        meta = {}
    center = bbox_center(bbox)
    return ElementCandidate(
        candidate_id=candidate_id,
        source_strategy=source_strategy,
        element_type=element_type,
        semantic_text=semantic_text,
        role=role,
        center_point=center,
        bbox={"x": int(bbox.get("x", 0)), "y": int(bbox.get("y", 0)), "width": int(bbox.get("width", 0)), "height": int(bbox.get("height", 0))},
        confidence_score=float(confidence_score),
        reasoning=reasoning,
        meta=meta,
        ocr_details=ocr_details,
    )
