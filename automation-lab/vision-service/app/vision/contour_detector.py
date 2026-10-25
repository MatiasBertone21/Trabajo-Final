"""
Contour Detection for UI element identification.
"""
import cv2
import numpy as np
from typing import List, Tuple, Dict
from ..core.config import VisionConfig


def preprocess_for_contours(image: np.ndarray) -> np.ndarray:
    """
    Preprocess image for contour detection.
    
    Args:
        image: input image (BGR or grayscale)
    
    Returns:
        Binary image ready for contour detection
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, VisionConfig.BLUR_KERNEL_SIZE, 0)
    
    # Apply CLAHE for contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(blurred)
    
    # Apply adaptive threshold for binarization
    binary = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    
    # Apply morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)
    
    return processed


def extract_contours(image: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
    """
    Extract contours from an image and return bounding boxes with quality scores.
    
    Args:
        image: input image (BGR or grayscale)
    
    Returns:
        List of (x, y, width, height, quality_score) tuples
    """
    preprocessed = preprocess_for_contours(image)
    
    # Find contours
    contours, _ = cv2.findContours(
        preprocessed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    
    h, w = image.shape[:2]
    image_area = h * w
    
    results = []
    
    for contour in contours:
        # Calculate bounding rectangle
        x, y, cw, ch = cv2.boundingRect(contour)
        area = cw * ch
        
        # Filter by area constraints
        area_ratio = area / image_area
        if area_ratio < VisionConfig.CONTOUR_AREA_MIN_RATIO or area_ratio > VisionConfig.CONTOUR_AREA_MAX_RATIO:
            continue
        
        # Calculate solidity (area / convex hull area)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        if hull_area == 0:
            continue
        solidity = area / hull_area
        
        if solidity < VisionConfig.CONTOUR_SOLIDITY_MIN:
            continue
        
        # Quality score based on solidity and area
        quality = min(1.0, solidity * (area_ratio / VisionConfig.CONTOUR_AREA_MIN_RATIO) ** 0.5)
        results.append((x, y, cw, ch, quality))
    
    return results


def detect_ui_elements(image: np.ndarray) -> List[Dict]:
    """
    Detect potential UI elements via contour detection.
    
    Args:
        image: input image
    
    Returns:
        List of {bbox, visual_score} dicts
    """
    contours = extract_contours(image)
    results = []
    
    for x, y, w, h, quality in contours:
        results.append({
            "x": int(x),
            "y": int(y),
            "width": int(w),
            "height": int(h),
            "visual_score": float(quality),
        })
    
    return results
