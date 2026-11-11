"""
Shared domain constants, directory paths, color palettes, and CSV schemas
for the Automation Lab CI reporting and dashboard builders.
"""
from pathlib import Path
from typing import Dict, List, Tuple

PLAYWRIGHT_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = PLAYWRIGHT_ROOT / "templates"
REPORTS_DIR = PLAYWRIGHT_ROOT / "reports"
HISTORY_DIR = PLAYWRIGHT_ROOT / "metrics-history"

STRATEGIES: List[str] = ["base", "getby", "opencv", "getby_full", "opencv_full"]
ATOMIC_STRATEGIES: List[str] = ["base", "getby", "opencv"]
FULL_STRATEGIES: List[str] = ["getby_full", "opencv_full"]
FRONTENDS: List[str] = ["react", "angular", "svelte"]

FULL_FLOW_STEPS: List[Tuple[str, str]] = [
    ("step1_nav_products", "S1: Nav Products"),
    ("step2a_validate_product_card_and_btn", "S2a: Card Struct"),
    ("step2b_validate_cart_zero_and_click_add", "S2b: Cart=0 & Add"),
    ("step3_verify_cart_one_and_open", "S3: Cart=2 & Open"),
    ("step4a_validate_cart_row_structure", "S4a: Row Struct"),
    ("step4b_verify_cart_title_and_click_remove", "S4b: Title & Remove"),
    ("step5_verify_product_removed_from_cart", "S5: Verify Empty"),
]

STRATEGY_COLORS: Dict[str, Tuple[int, int, int]] = {
    "base": (37, 99, 235),        # Blue
    "getby": (16, 185, 129),      # Emerald
    "opencv": (245, 158, 11),     # Amber/Orange
    "getby_full": (13, 148, 136), # Teal
    "opencv_full": (225, 29, 72), # Rose/Red
}

LAYER_COLORS: Dict[str, Tuple[int, int, int]] = {
    "DOM (CSS / get_by)": (16, 185, 129),
    "Viewport Capture": (59, 130, 246),
    "Network + Decode": (139, 92, 246),
    "Template Matching (TM_CCOEFF_NORMED)": (245, 158, 11),
    "EasyOCR + Ranking": (239, 68, 68),
}

HISTORY_CSV_FIELDNAMES: List[str] = [
    "build_number",
    "timestamp",
    "strategy",
    "frontend",
    "runs",
    "passed",
    "pass_rate_pct",
    "total_median_ms",
    "total_p95_ms",
    "total_mean_ms",
    "total_stdev_ms",
    "call_median_ms",
    "step_median_ms",
    "step_p95_ms",
    "capture_ms",
    "network_ms",
    "decode_preprocess_ms",
    "template_ms",
    "ocr_ranking_ms",
    "mean_confidence",
    "dom_hit_rate_pct",
]

EXPECTED_TEMPLATES: Dict[str, str] = {
    "nav_products": "home-nav-products-btn.png",
    "nav_cart": "home-nav-cart-btn.png",
    "logout": "home-logout-btn.png",
    "add_to_cart": "products-add-to-cart-btn.png",
    "product_card": "product-card/product-card-container.png",
    "laptop_card": "product-card/laptop-card-container.png",
    "product_title": "product-card/product-card-title.png",
    "product_price": "product-card/product-card-price.png",
    "product_image": "product-card/product-card-image.png",
    "cart_item_container": "cart-item/cart-item-container.png",
    "cart_item_image": "cart-item/cart-item-image.png",
    "cart_item_title": "cart-item/cart-item-title.png",
    "cart_item_description": "cart-item/cart-item-description.png",
    "cart_item_decrease": "cart-item/cart-item-decrease-btn.png",
    "cart_item_increase": "cart-item/cart-item-increase-btn.png",
    "cart_item_remove": "cart-item/cart-item-remove-btn.png",
}
