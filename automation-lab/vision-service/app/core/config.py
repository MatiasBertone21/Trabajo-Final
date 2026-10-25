"""
Configuration and parameters for the vision perception engine.
"""
import os


class VisionConfig:
    """Central configuration for vision processing pipeline."""

    # Template Matching parameters
    TEMPLATE_MATCH_THRESHOLD = 0.6

    # Contour Detection parameters
    CONTOUR_AREA_MIN_RATIO = 0.0001  # min area as ratio of image area
    CONTOUR_AREA_MAX_RATIO = 0.9     # max area as ratio of image area
    CONTOUR_SOLIDITY_MIN = 0.05      # solidity threshold

    # OCR parameters (configurable via environment variables)
    OCR_ENGINE = os.getenv("VISION_OCR_ENGINE", "easyocr").strip().lower()
    OCR_LANGUAGES = [
        lang.strip()
        for lang in os.getenv("VISION_OCR_LANGUAGES", "en,es").split(",")
        if lang.strip()
    ]
    OCR_CONFIDENCE_THRESHOLD = 0.3

    # NMS (Non-Maximum Suppression) parameters
    NMS_IOU_THRESHOLD = 0.5

    # Image preprocessing parameters
    PREPROCESS_MAX_WIDTH = 1920
    PREPROCESS_MAX_HEIGHT = 1080
    BLUR_KERNEL_SIZE = (5, 5)

    # ROI extraction padding (relative to bbox dimensions)
    ROI_PADDING_RATIO = 0.1

    # Confidence & ranking thresholds
    CONFIDENCE_MIN_THRESHOLD = 0.01
    RANKING_MIN_RELEVANCE = 0.5
    AREA_FACTOR_MIN = 0.001  # min area as ratio of image area (calibrated for UI elements)

    # Confidence score formula weights
    CONFIDENCE_FORMULA_TEMPLATE_OCR = {
        "w_template": 0.6,
        "w_ocr": 0.4,
    }

    CONFIDENCE_FORMULA_CONTOUR_OCR = {
        "w_contour": 0.7,
        "w_ocr": 0.3,
    }
