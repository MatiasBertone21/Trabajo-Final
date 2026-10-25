import logging
from typing import List, Optional
import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import JSONResponse
from ..core.config import VisionConfig
from ..vision.perception import PerceptionEngine
from ..vision.ranker import rank_by_description

logger = logging.getLogger(__name__)
router = APIRouter()
engine = PerceptionEngine()  # Singleton instance - templates loaded on demand


def _parse_csv_query(values: Optional[List[str]]) -> Optional[List[str]]:
    """Normalize repeated (?k=a&k=b) or comma-separated (?k=a,b) query parameters."""
    if not values:
        return None
    parsed: List[str] = []
    for item in values:
        parsed.extend([s.strip() for s in item.split(",") if s.strip()])
    return parsed if parsed else None


@router.post("/templates/register")
async def register_template(
    template_name: str = Query(...),
    file: UploadFile = File(...),
):
    """
    Register a template in memory for subsequent detections.

    Args:
        template_name: identifier for the template (e.g., "add_to_cart")
        file: template image file (PNG/JPG)

    Returns:
        {"status": "registered", "template_name": str, "templates_count": int}
    """
    try:
        content = await file.read()
        image_array = np.frombuffer(content, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image is None:
            return JSONResponse(
                {"error": "Failed to decode template image"},
                status_code=400,
            )

        engine.register_template(template_name, image)

        return JSONResponse({
            "status": "registered",
            "template_name": template_name,
            "templates_count": len(engine.templates),
        })

    except Exception:
        logger.exception("Error registering template '%s'", template_name)
        return JSONResponse(
            {"error": "Internal error while registering template"},
            status_code=500,
        )


@router.post("/templates/clear")
async def clear_templates():
    """
    Clear all registered templates from memory.

    Returns:
        {"status": "cleared", "templates_cleared": int}
    """
    try:
        count = engine.clear_templates()

        return JSONResponse({
            "status": "cleared",
            "templates_cleared": count,
        })

    except Exception:
        logger.exception("Error clearing registered templates")
        return JSONResponse(
            {"error": "Internal error while clearing templates"},
            status_code=500,
        )


@router.post("/detect")
async def detect(
    file: UploadFile = File(...),
    target_description: Optional[str] = Query(None),
    element_type: Optional[str] = Query(None),
    synonyms: Optional[List[str]] = Query(None),
    strategies: Optional[List[str]] = Query(None),
    enable_ocr: bool = Query(True),
    visual_threshold: Optional[float] = Query(None, ge=0.0, le=1.0),
    top_k: Optional[int] = Query(None),
):
    """
    Detect UI elements in an image.

    Args:
        file: image file (required)
        target_description: optional description for ranking (e.g., "Add to cart")
        element_type: optional filter (e.g., "button")
        synonyms: optional domain synonyms for text matching (e.g., ["bag", "carrito"])
        strategies: optional detection strategies (e.g., ["template"], ["template", "contour"])
        enable_ocr: whether to execute OCR text extraction and semantic ranking (default: True)
        visual_threshold: optional confidence threshold for template matching (0.0 to 1.0)
        top_k: return top k candidates

    Returns:
        JSON payload with detected ElementCandidate list
    """
    try:
        content = await file.read()
        image_array = np.frombuffer(content, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image is None:
            return JSONResponse(
                {"error": "Failed to decode image"},
                status_code=400,
            )

        parsed_strategies = _parse_csv_query(strategies)

        candidates = engine.detect(
            image,
            strategies=parsed_strategies,
            enable_ocr=enable_ocr,
            visual_threshold=visual_threshold,
        )

        if enable_ocr and target_description:
            parsed_synonyms = _parse_csv_query(synonyms)

            candidates = rank_by_description(
                candidates,
                target_description=target_description,
                element_type=element_type,
                synonyms=parsed_synonyms,
                top_k=top_k,
                confidence_threshold=VisionConfig.RANKING_MIN_RELEVANCE,
            )
        elif top_k is not None:
            candidates = candidates[:top_k]

        result = {
            "status": "success",
            "candidates_count": len(candidates),
            "candidates": [c.to_dict() for c in candidates],
        }

        return JSONResponse(result)

    except Exception:
        logger.exception("Error during vision detection")
        return JSONResponse(
            {"error": "Internal error during vision detection"},
            status_code=500,
        )
