"""
OCR module: Tesseract and EasyOCR wrappers for text detection in ROIs.
"""
import logging
from typing import Tuple, Dict
import cv2
import numpy as np
from ..core.config import VisionConfig

logger = logging.getLogger(__name__)


def preprocess_for_ocr(roi: np.ndarray) -> np.ndarray:
    """
    Preprocess ROI for OCR (binarization, morphology).

    Args:
        roi: extracted region of interest

    Returns:
        Preprocessed binary image
    """
    if len(roi.shape) == 3:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    else:
        gray = roi

    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    _, binary = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)

    return morph


def extract_text_tesseract(roi: np.ndarray) -> Tuple[str, float]:
    """
    Extract text from ROI using Tesseract.

    Args:
        roi: extracted region of interest

    Returns:
        (text, confidence) tuple
    """
    preprocessed = preprocess_for_ocr(roi)

    try:
        import pytesseract

        data = pytesseract.image_to_data(preprocessed, output_type=pytesseract.Output.DICT)

        texts = []
        confidences = []

        for i in range(len(data["text"])):
            if int(data["conf"][i]) > VisionConfig.OCR_CONFIDENCE_THRESHOLD * 100:
                texts.append(data["text"][i])
                confidences.append(int(data["conf"][i]) / 100.0)

        if not texts:
            return "", 0.0

        text = " ".join(texts)
        confidence = np.mean(confidences) if confidences else 0.0
        return text.strip(), float(confidence)

    except Exception as e:
        logger.warning("Tesseract OCR error: %s", e)
        return "", 0.0


_easyocr_reader = None


def get_easyocr_reader():
    """Get or initialize singleton EasyOCR Reader instance."""
    global _easyocr_reader
    if _easyocr_reader is None:
        import easyocr
        _easyocr_reader = easyocr.Reader(VisionConfig.OCR_LANGUAGES, gpu=False)
    return _easyocr_reader


def extract_text_easyocr(roi: np.ndarray, reader=None) -> Tuple[str, float]:
    """
    Extract text from ROI using EasyOCR.

    Args:
        roi: extracted region of interest
        reader: EasyOCR Reader instance (lazy initialized / cached)

    Returns:
        (text, confidence) tuple
    """
    try:
        if reader is None:
            reader = get_easyocr_reader()

        results = reader.readtext(roi)

        if not results:
            return "", 0.0

        texts = []
        confidences = []

        for (_, text, conf) in results:
            if conf > VisionConfig.OCR_CONFIDENCE_THRESHOLD:
                texts.append(text)
                confidences.append(conf)

        if not texts:
            return "", 0.0

        text = " ".join(texts)
        confidence = np.mean(confidences) if confidences else 0.0
        return text.strip(), float(confidence)

    except Exception as e:
        logger.warning("EasyOCR error: %s", e)
        return "", 0.0


def extract_text_from_roi(
    image: np.ndarray,
    bbox: Dict[str, int],
    padding_ratio: float = None,
    engine: str = None,
) -> Tuple[str, float]:
    """
    Extract text from a region of interest within an image.

    Args:
        image: full image
        bbox: {x, y, width, height} bounding box
        padding_ratio: expansion ratio for ROI (default: from config)
        engine: OCR engine ('tesseract' or 'easyocr'; default: from config)

    Returns:
        (text, confidence) tuple
    """
    if padding_ratio is None:
        padding_ratio = VisionConfig.ROI_PADDING_RATIO
    if engine is None:
        engine = VisionConfig.OCR_ENGINE

    x, y, w, h = bbox["x"], bbox["y"], bbox["width"], bbox["height"]
    pad_x = int(w * padding_ratio)
    pad_y = int(h * padding_ratio)

    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x2 = min(image.shape[1], x + w + pad_x)
    y2 = min(image.shape[0], y + h + pad_y)

    roi = image[y1:y2, x1:x2]

    if roi.size == 0:
        return "", 0.0

    if engine == "tesseract":
        return extract_text_tesseract(roi)
    elif engine == "easyocr":
        return extract_text_easyocr(roi)
    else:
        return "", 0.0
