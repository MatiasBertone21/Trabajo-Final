"""
PerceptionEngine: Main orchestrator for vision-based UI element detection.
Combines template matching, contour detection, and OCR.
"""
from typing import List, Dict, Optional
import cv2
import numpy as np
from .models import ElementCandidate
from .utils import create_element_candidate
from .template_matcher import match_multiple_templates
from .contour_detector import detect_ui_elements
from .ocr import extract_text_from_roi
from ..core.config import VisionConfig


def compute_iou(box1: Dict, box2: Dict) -> float:
    """
    Compute Intersection over Union (IoU) between two boxes.

    Args:
        box1, box2: {x, y, width, height} dicts

    Returns:
        IoU score [0, 1]
    """
    x1_1, y1_1 = box1["x"], box1["y"]
    x2_1 = x1_1 + box1["width"]
    y2_1 = y1_1 + box1["height"]

    x1_2, y1_2 = box2["x"], box2["y"]
    x2_2 = x1_2 + box2["width"]
    y2_2 = y1_2 + box2["height"]

    xi1 = max(x1_1, x1_2)
    yi1 = max(y1_1, y1_2)
    xi2 = min(x2_1, x2_2)
    yi2 = min(y2_1, y2_2)

    inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
    box1_area = box1["width"] * box1["height"]
    box2_area = box2["width"] * box2["height"]
    union_area = box1_area + box2_area - inter_area

    return inter_area / union_area if union_area > 0 else 0.0


def apply_nms(candidates: List[Dict], iou_threshold: float = None) -> List[Dict]:
    """
    Apply Non-Maximum Suppression to filter overlapping candidates.

    Args:
        candidates: list of candidate dicts with 'bbox' and 'confidence'
        iou_threshold: IoU threshold for suppression (default: from config)

    Returns:
        Filtered candidates sorted by confidence (descending)
    """
    if iou_threshold is None:
        iou_threshold = VisionConfig.NMS_IOU_THRESHOLD

    if not candidates:
        return []

    sorted_candidates = sorted(candidates, key=lambda x: x.get("confidence", 0.0), reverse=True)
    kept = []

    for candidate in sorted_candidates:
        suppress = False
        for kept_candidate in kept:
            iou = compute_iou(candidate["bbox"], kept_candidate["bbox"])
            if iou > iou_threshold:
                suppress = True
                break

        if not suppress:
            kept.append(candidate)

    return kept


def compute_confidence_score(
    template_score: Optional[float] = None,
    ocr_confidence: Optional[float] = None,
    visual_score: Optional[float] = None,
    area_ratio: float = 1.0,
    source: str = "template",
) -> float:
    """
    Compute combined confidence score for a detection.

    Args:
        template_score: similarity score from template matching [0, 1]
        ocr_confidence: confidence from OCR [0, 1]
        visual_score: score from contour analysis [0, 1]
        area_ratio: area as ratio of image area
        source: detection source ('template', 'contour', etc.)

    Returns:
        Combined confidence score [0, 1]
    """
    # Apply area penalty (exempt template matching since ROI is pattern-grounded)
    if source == "template":
        area_factor = 1.0
    else:
        area_factor = min(1.0, area_ratio / VisionConfig.AREA_FACTOR_MIN)

    if source == "template":
        template_score = template_score or 0.0
        if ocr_confidence is not None and ocr_confidence > 0:
            w_template = VisionConfig.CONFIDENCE_FORMULA_TEMPLATE_OCR["w_template"]
            w_ocr = VisionConfig.CONFIDENCE_FORMULA_TEMPLATE_OCR["w_ocr"]
            score = (
                w_template * template_score
                + w_ocr * ocr_confidence * (0.6 + 0.4 * template_score)
            )
        else:
            score = template_score

    elif source == "contour":
        visual_score = visual_score or 0.0
        if ocr_confidence is not None and ocr_confidence > 0:
            w_contour = VisionConfig.CONFIDENCE_FORMULA_CONTOUR_OCR["w_contour"]
            w_ocr = VisionConfig.CONFIDENCE_FORMULA_CONTOUR_OCR["w_ocr"]
            score = w_contour * visual_score + w_ocr * ocr_confidence
        else:
            score = visual_score

    else:
        score = 0.0

    final_score = np.clip(score * area_factor, 0.0, 1.0)
    return float(final_score)


class PerceptionEngine:
    """Main vision perception engine for UI element detection."""

    def __init__(self, config: Optional[VisionConfig] = None):
        self.config = config or VisionConfig()
        self.templates: Dict[str, np.ndarray] = {}

    def register_template(self, template_id: str, template_image: np.ndarray) -> None:
        """Register a template for template matching."""
        self.templates[template_id] = template_image

    def clear_templates(self) -> int:
        """Clear all registered templates from memory and return the count cleared."""
        count = len(self.templates)
        self.templates.clear()
        return count

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image: resize, denoise, enhance contrast."""
        h, w = image.shape[:2]

        if w > self.config.PREPROCESS_MAX_WIDTH or h > self.config.PREPROCESS_MAX_HEIGHT:
            scale = min(
                self.config.PREPROCESS_MAX_WIDTH / w,
                self.config.PREPROCESS_MAX_HEIGHT / h,
            )
            new_w, new_h = int(w * scale), int(h * scale)
            image = cv2.resize(image, (new_w, new_h))

        image = cv2.GaussianBlur(image, self.config.BLUR_KERNEL_SIZE, 0)

        if len(image.shape) == 3:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l_channel = lab[:, :, 0]
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l_channel = clahe.apply(l_channel)
            lab[:, :, 0] = l_channel
            image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        return image

    def detect(
        self,
        image: np.ndarray,
        strategies: Optional[List[str]] = None,
        enable_ocr: bool = True,
        visual_threshold: Optional[float] = None,
    ) -> List[ElementCandidate]:
        """
        Detect UI elements in an image using the perception pipeline.

        Args:
            image: input image (BGR)
            strategies: list of detection strategies ('template', 'contour')
                        (default: ['template'])
            enable_ocr: whether to run the OCR pipeline and return ocr_details (default: True)
            visual_threshold: optional confidence threshold for template matching (0.0 to 1.0)

        Returns:
            List of ElementCandidate objects sorted by confidence (descending)
        """
        if strategies is None:
            strategies = ["template"]

        processed_image = self.preprocess_image(image)
        h, w = processed_image.shape[:2]
        image_area = h * w

        raw_candidates = []

        # Template Matching strategy
        if "template" in strategies and self.templates:
            template_matches = match_multiple_templates(
                processed_image, self.templates, threshold=visual_threshold
            )
            for match in template_matches:
                area_ratio = (match["width"] * match["height"]) / image_area

                if enable_ocr:
                    text, ocr_conf = extract_text_from_roi(image, match)
                    ocr_details = {
                        "engine": self.config.OCR_ENGINE,
                        "text": text if text else "",
                        "confidence": float(ocr_conf) if ocr_conf is not None else 0.0,
                    }
                else:
                    text, ocr_conf = None, None
                    ocr_details = None

                confidence = compute_confidence_score(
                    template_score=match["confidence"],
                    ocr_confidence=ocr_conf,
                    area_ratio=area_ratio,
                    source="template",
                )

                raw_candidates.append({
                    "bbox": {
                        "x": match["x"],
                        "y": match["y"],
                        "width": match["width"],
                        "height": match["height"],
                    },
                    "confidence": confidence,
                    "template_score": match["confidence"],
                    "ocr_confidence": ocr_conf,
                    "text": text,
                    "source": "template",
                    "meta": {"template_id": match.get("template_id")},
                    "ocr_details": ocr_details,
                })

        # Contour Detection strategy
        if "contour" in strategies:
            contours = detect_ui_elements(processed_image)
            for contour in contours:
                area_ratio = (contour["width"] * contour["height"]) / image_area

                if enable_ocr:
                    text, ocr_conf = extract_text_from_roi(image, contour)
                    ocr_details = {
                        "engine": self.config.OCR_ENGINE,
                        "text": text if text else "",
                        "confidence": float(ocr_conf) if ocr_conf is not None else 0.0,
                    }
                else:
                    text, ocr_conf = None, None
                    ocr_details = None

                confidence = compute_confidence_score(
                    visual_score=contour["visual_score"],
                    ocr_confidence=ocr_conf,
                    area_ratio=area_ratio,
                    source="contour",
                )

                raw_candidates.append({
                    "bbox": {
                        "x": contour["x"],
                        "y": contour["y"],
                        "width": contour["width"],
                        "height": contour["height"],
                    },
                    "confidence": confidence,
                    "visual_score": contour["visual_score"],
                    "ocr_confidence": ocr_conf,
                    "text": text,
                    "source": "contour",
                    "meta": {},
                    "ocr_details": ocr_details,
                })

        filtered = apply_nms(raw_candidates)
        filtered = [c for c in filtered if c["confidence"] >= self.config.CONFIDENCE_MIN_THRESHOLD]

        candidates = []
        for candidate in filtered:
            element_candidate = create_element_candidate(
                source_strategy=candidate["source"],
                bbox=candidate["bbox"],
                confidence_score=candidate["confidence"],
                element_type="unknown",
                semantic_text=candidate.get("text") if candidate.get("text") else None,
                reasoning=f"Detected via {candidate['source']} strategy",
                meta={
                    "template_id": candidate.get("meta", {}).get("template_id"),
                    "template_score": candidate.get("template_score"),
                    "visual_score": candidate.get("visual_score"),
                    "ocr_confidence": candidate.get("ocr_confidence"),
                    "area_pixels": candidate["bbox"]["width"] * candidate["bbox"]["height"],
                },
                ocr_details=candidate.get("ocr_details"),
            )
            candidates.append(element_candidate)

        return candidates
