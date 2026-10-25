"""
Debug Script: Template Matching Multi-Scale + OCR Validation Strategy

Purpose:
    Validate a new vision strategy that replaces ContourDetector with:
    1. Grayscale conversion (ignore color variations)
    2. Multi-template bank search
    3. Multi-scale template matching
    4. OCR validation on detected ROI
    5. Visual output with bounding boxes

This is a standalone, clean implementation for technical viability testing.

Usage:
    python scripts/debug_template_ocr.py <screenshot_path> [--templates-dir <dir>]
"""

import cv2
import numpy as np
import pytesseract
from pathlib import Path
import sys
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
from scipy import ndimage


@dataclass
class TemplateMatch:
    """Result of a single template match."""
    template_name: str
    template_path: str
    scale: float
    score: float
    bbox: Dict[str, int]  # {x, y, width, height}
    roi_image: np.ndarray
    ocr_text: str
    ocr_confidence: float


class TemplateMatcherOCRStrategy:
    """
    Multi-scale template matching strategy with OCR validation.
    
    Architecture:
        1. Load screenshot and template bank
        2. Convert both to grayscale
        3. For each template:
            a. For each scale (0.5x to 1.5x):
                - Resize screenshot
                - Use cv2.matchTemplate to find matches
                - Keep best match if score > threshold
        4. For each match:
            a. Extract ROI from original image
            b. Run OCR on ROI
            c. Validate match using OCR confidence
        5. Draw bboxes on original screenshot
        6. Save result
    """
    
    def __init__(
        self,
        template_dir: Path,
        min_match_threshold: float = 0.7,
        min_ocr_threshold: float = 0.3,
        scale_range: Tuple[float, float] = (0.5, 1.5),
        scale_steps: int = 5,
    ):
        """
        Initialize strategy.
        
        Args:
            template_dir: Directory containing template images
            min_match_threshold: CV template matching threshold (0-1)
            min_ocr_threshold: OCR confidence threshold (0-1)
            scale_range: (min_scale, max_scale) for multi-scale search
            scale_steps: Number of scales to test
        """
        self.template_dir = Path(template_dir)
        self.min_match_threshold = min_match_threshold
        self.min_ocr_threshold = min_ocr_threshold
        self.scale_range = scale_range
        self.scale_steps = scale_steps
        self.roi_padding_ratio = 0.1
        
        # Load template bank
        self.templates = self._load_template_bank()
        
        print(f"✓ Loaded {len(self.templates)} templates from {self.template_dir}")
        for template in self.templates:
            print(f"  - {template['name']} ({template['gray'].shape})")
    
    def _load_template_bank(self) -> List[Dict]:
        """Load all templates from directory."""
        templates = []
        
        if not self.template_dir.exists():
            print(f"⚠ Template directory not found: {self.template_dir}")
            return templates
        
        for template_file in sorted(self.template_dir.glob("*.png")):
            image_bgr = cv2.imread(str(template_file))
            
            if image_bgr is None:
                print(f"⚠ Failed to load: {template_file}")
                continue
            
            # Convert to grayscale
            image_gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
            
            templates.append({
                'name': template_file.stem,
                'path': str(template_file),
                'bgr': image_bgr,
                'gray': image_gray,
                'h': image_gray.shape[0],
                'w': image_gray.shape[1],
            })
        
        return templates
    
    def _extract_ocr(self, roi: np.ndarray) -> Tuple[str, float]:
        """
        Extract text from ROI using Tesseract.
        
        Args:
            roi: Region of interest image
        
        Returns:
            (text, confidence) tuple
        """
        try:
            # Preprocess for OCR
            if len(roi.shape) == 3:
                roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            else:
                roi_gray = roi
            
            # Upscale ROI 2x for better OCR
            h, w = roi_gray.shape
            roi_upscaled = cv2.resize(
                roi_gray,
                (w * 2, h * 2),
                interpolation=cv2.INTER_CUBIC
            )
            
            # Binarize
            _, roi_binary = cv2.threshold(
                roi_upscaled, 127, 255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            
            # OCR
            text = pytesseract.image_to_string(roi_binary).strip()
            data = pytesseract.image_to_data(
                roi_binary, output_type=pytesseract.Output.DICT
            )
            
            # Calculate average confidence
            confidences = [
                int(conf) / 100.0
                for conf in data['conf']
                if int(conf) > 0
            ]
            
            confidence = np.mean(confidences) if confidences else 0.0
            
            return text, confidence
        
        except Exception as e:
            print(f"⚠ OCR error: {e}")
            return "", 0.0
    
    def detect(self, screenshot_path: str) -> List[TemplateMatch]:
        """
        Detect templates in screenshot using multi-scale matching + OCR.
        
        Args:
            screenshot_path: Path to screenshot image
        
        Returns:
            List of TemplateMatch results sorted by confidence
        """
        # Load screenshot
        screenshot_bgr = cv2.imread(screenshot_path)
        if screenshot_bgr is None:
            raise FileNotFoundError(f"Screenshot not found: {screenshot_path}")
        
        screenshot_gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)
        img_h, img_w = screenshot_gray.shape
        
        print(f"\n✓ Loaded screenshot: {Path(screenshot_path).name}")
        print(f"  Size: {screenshot_gray.shape}")
        print(f"  Scales to test: {self.scale_range[0]:.1f}x - {self.scale_range[1]:.1f}x " +
              f"({self.scale_steps} steps)")
        
        # Generate scale range
        scales = np.linspace(self.scale_range[0], self.scale_range[1], self.scale_steps)
        
        matches = []
        
        # ====== MULTI-TEMPLATE SEARCH ======
        for template in self.templates:
            template_name = template['name']
            template_gray = template['gray']
            template_h, template_w = template_gray.shape
            
            all_candidates = []
            
            # ====== MULTI-SCALE SEARCH ======
            for scale in scales:
                # Skip if scaled template is larger than screenshot
                scaled_h = int(template_h * scale)
                scaled_w = int(template_w * scale)
                
                if scaled_h > img_h or scaled_w > img_w:
                    continue
                
                # Resize screenshot to this scale
                resized_screenshot = cv2.resize(
                    screenshot_gray,
                    (int(img_w * scale), int(img_h * scale)),
                    interpolation=cv2.INTER_LINEAR
                )
                
                # Match template on resized screenshot
                result = cv2.matchTemplate(
                    resized_screenshot,
                    template_gray,
                    cv2.TM_CCOEFF_NORMED
                )
                
                # Find local maxima (peaks) instead of all pixels above threshold
                max_filtered = ndimage.maximum_filter(result, size=10)
                peaks = (result == max_filtered) & (result >= self.min_match_threshold)
                
                locs = np.where(peaks)
            
                for pt in zip(*locs[::-1]):
                    score = result[pt[1], pt[0]]
                    all_candidates.append((pt, score, scale))

            # ====== VALIDATE MATCHES WITH OCR ======
            print(f"\n  Template: {template_name}")
            print(f"    Candidates found: {len(all_candidates)}")

            for idx, candidate in enumerate(all_candidates, 1):
                loc, score, scale = candidate
            
                # Scale coordinates back to original screenshot
                x, y = loc
                x = int(x / scale)
                y = int(y / scale)
                width = template_w
                height = template_h
                
                # Clamp to original image bounds
                x = max(0, min(x, img_w - width))
                y = max(0, min(y, img_h - height))
                
                # Expand ROI with padding before OCR extraction
                pad_x = int(width * self.roi_padding_ratio)
                pad_y = int(height * self.roi_padding_ratio)
                
                x_padded = max(0, x - pad_x)
                y_padded = max(0, y - pad_y)
                w_padded = min(img_w, width + 2 * pad_x)
                h_padded = min(img_h, height + 2 * pad_y)
                
                roi = screenshot_bgr[y_padded:y_padded+h_padded, x_padded:x_padded+w_padded]
                
                # Run OCR
                ocr_text, ocr_confidence = self._extract_ocr(roi)
                
                # Create match result
                match = TemplateMatch(
                    template_name=template_name,
                    template_path=template['path'],
                    scale=scale,
                    score=score,
                    bbox={'x': x, 'y': y, 'width': width, 'height': height},
                    roi_image=roi,
                    ocr_text=ocr_text,
                    ocr_confidence=ocr_confidence,
                )
                
                matches.append(match)
                
                print(f"    [{idx}] Score: {score:.3f} @ {scale:.2f}x | " +
                    f"({x}, {y}) {width}×{height} | OCR: '{ocr_text}' ({ocr_confidence:.2f})")
        
        # Sort by match score (descending)
        matches.sort(key=lambda m: m.score, reverse=True)
        
        return matches
    
    def visualize(
        self,
        screenshot_path: str,
        matches: List[TemplateMatch],
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Draw bounding boxes on screenshot and save.
        
        Args:
            screenshot_path: Path to original screenshot
            matches: List of TemplateMatch results
            output_dir: Directory to save result (default: ./reports/debug_template_ocr/)
        
        Returns:
            Path to saved image
        """
        # Create output directory
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "reports" / "debug_template_ocr"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load screenshot
        image = cv2.imread(screenshot_path)
        
        # Draw bboxes and labels
        for idx, match in enumerate(matches):
            bbox = match.bbox
            x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
            
            # Draw rectangle (green)
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Draw center point (red dot)
            cx, cy = x + w // 2, y + h // 2
            cv2.circle(image, (cx, cy), 5, (0, 0, 255), -1)
            
            # Label with template name, score, and OCR text
            label1 = f"{match.template_name} ({match.score:.2f})"
            label2 = f"'{match.ocr_text[:20]}' ({match.ocr_confidence:.2f})"
            
            cv2.putText(
                image, label1, (x, y - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1
            )
            cv2.putText(
                image, label2, (x, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1
            )
        
        # Save image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"matches_{timestamp}.png"
        cv2.imwrite(str(output_path), image)
        
        print(f"\n✓ Visualization saved: {output_path}")
        return output_path
    
    def summary(self, matches: List[TemplateMatch]):
        """Print summary of detected matches."""
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        print(f"Total templates tested: {len(self.templates)}")
        print(f"Matches found: {len(matches)}")
        
        if matches:
            print(f"\nDetailed Results (sorted by confidence):")
            for idx, match in enumerate(matches, 1):
                print(f"\n  [{idx}] {match.template_name}")
                print(f"      Match Score:     {match.score:.3f}")
                print(f"      Scale:           {match.scale:.2f}x")
                print(f"      Bounding Box:    ({match.bbox['x']}, {match.bbox['y']}) " +
                      f"{match.bbox['width']}×{match.bbox['height']}")
                print(f"      OCR Text:        '{match.ocr_text}'")
                print(f"      OCR Confidence:  {match.ocr_confidence:.3f}")
        else:
            print("\n  (No matches detected)")
        
        print(f"\n{'='*70}\n")


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Template Matching + OCR Strategy Debug Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
    # Using default templates directory (tests/assets/templates/)
    python scripts/debug_template_ocr.py tests/assets/datasets/home_page-react.png
    
    # Using custom templates directory
    python scripts/debug_template_ocr.py tests/assets/datasets/home_page-react.png \\
        --templates-dir my_templates/
        """
    )
    
    parser.add_argument(
        "screenshot",
        help="Path to screenshot to analyze"
    )
    
    parser.add_argument(
        "--templates-dir",
        default="tests/assets/templates",
        help="Directory containing template images (default: tests/assets/templates)"
    )
    
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Template matching threshold 0-1 (default: 0.7)"
    )
    
    parser.add_argument(
        "--ocr-threshold",
        type=float,
        default=0.3,
        help="OCR confidence threshold 0-1 (default: 0.3)"
    )
    
    args = parser.parse_args()
    
    # Resolve paths relative to vision-service directory
    vision_service_dir = Path(__file__).parent.parent
    screenshot_path = vision_service_dir / args.screenshot
    templates_dir = vision_service_dir / args.templates_dir
    
    # Validate inputs
    if not screenshot_path.exists():
        print(f"❌ Screenshot not found: {screenshot_path}")
        sys.exit(1)
    
    # Initialize strategy
    try:
        strategy = TemplateMatcherOCRStrategy(
            template_dir=templates_dir,
            min_match_threshold=args.threshold,
            min_ocr_threshold=args.ocr_threshold,
        )
    except Exception as e:
        print(f"❌ Failed to initialize strategy: {e}")
        sys.exit(1)
    
    # Run detection
    print(f"\n{'='*70}")
    print("TEMPLATE MATCHING + OCR STRATEGY - DEBUG SCRIPT")
    print(f"{'='*70}")
    
    try:
        matches = strategy.detect(str(screenshot_path))
        
        # Visualize
        output_path = strategy.visualize(str(screenshot_path), matches)
        
        # Summary
        strategy.summary(matches)
        
        sys.exit(0 if len(matches) > 0 else 1)
    
    except Exception as e:
        print(f"❌ Error during detection: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
