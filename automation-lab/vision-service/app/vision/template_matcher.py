"""
Template Matching detector using OpenCV.
"""
import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional
from ..core.config import VisionConfig


def normalize_template_score(score: float) -> float:
    """Normalize template matching score to [0, 1]."""
    return np.clip(float(score), 0.0, 1.0)


def match_template(
    image: np.ndarray,
    template: np.ndarray,
    method: int = cv2.TM_CCOEFF_NORMED,
    threshold: float = None,
) -> List[Tuple[int, int, int, int, float]]:
    """
    Match a template in an image using OpenCV.
    
    Args:
        image: input image (BGR or grayscale)
        template: template to search for
        method: cv2 template matching method (default: TM_CCOEFF_NORMED)
        threshold: confidence threshold (default: from config)
    
    Returns:
        List of (x, y, width, height, confidence) tuples
    """
    if threshold is None:
        threshold = VisionConfig.TEMPLATE_MATCH_THRESHOLD
    
    # Ensure single channel for matching
    if len(image.shape) == 3:
        image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        image_gray = image
    
    if len(template.shape) == 3:
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    else:
        template_gray = template
    
    # Check that template is smaller than image
    if template_gray.shape[0] > image_gray.shape[0] or template_gray.shape[1] > image_gray.shape[1]:
        return []
    
    # Match template
    result = cv2.matchTemplate(image_gray, template_gray, method)
    
    # Extract local maxima (peaks) instead of only global minMaxLoc
    # Kernel size corresponds to template window to eliminate immediately adjacent pixels
    k_w = max(3, template_gray.shape[1] // 2)
    k_h = max(3, template_gray.shape[0] // 2)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k_w, k_h))
    dilated = cv2.dilate(result, kernel)
    
    peaks = (result == dilated) & (result >= threshold)
    locs = np.where(peaks)
    
    w, h = template_gray.shape[1], template_gray.shape[0]
    matches = []
    for pt in zip(*locs[::-1]):  # (x, y)
        raw_score = result[pt[1], pt[0]]
        score = normalize_template_score(raw_score)
        matches.append((int(pt[0]), int(pt[1]), int(w), int(h), float(score)))
    
    # Sort matches by confidence descending
    matches.sort(key=lambda m: m[4], reverse=True)
    return matches


def match_multiple_templates(
    image: np.ndarray,
    templates: Dict[str, np.ndarray],
    threshold: float = None,
) -> List[Dict]:
    """
    Match multiple templates in an image.
    
    Args:
        image: input image
        templates: dictionary of {template_id: template_image}
        threshold: confidence threshold
    
    Returns:
        List of {bbox, confidence, template_id} dicts
    """
    results = []
    for template_id, template in templates.items():
        matches = match_template(image, template, threshold=threshold)
        for x, y, w, h, score in matches:
            results.append({
                "x": int(x),
                "y": int(y),
                "width": int(w),
                "height": int(h),
                "confidence": float(score),
                "template_id": template_id,
            })
    return results
