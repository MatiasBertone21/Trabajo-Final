import time
from typing import Any, Dict, List, Optional
from playwright.sync_api import expect

from pages.base_page import BasePage
from utils.openvisor_helper import (
    ENV_TEMPLATE_CATALOG,
    PLAYWRIGHT_ROOT,
    clear_templates_from_api,
    publish_step_audit,
)


class CartPage(BasePage):
    def goto(self):
        self.navigate("/cart")

    def remove_item(self, index: int = 0):
        self.page.locator(self.selectors["remove_item"]).nth(index).click()
        self.page.wait_for_load_state("networkidle")

    def clear_cart(self):
        selector = self.selectors.get("clear_cart")
        if not selector:
            raise NotImplementedError("clear_cart is not available for this frontend")
        self.page.click(selector)
        self.page.wait_for_load_state("networkidle")

    def is_empty(self) -> bool:
        return self.page.locator(self.selectors["empty_cart"]).is_visible(timeout=self.timeout)

    def remove_item_get_by(self, index: int = 0):
        remove_button = self._get_locator_by("remove_item")
        expect(remove_button).to_be_visible()
        remove_button.click()
        self.page.wait_for_load_state("networkidle")

    def _get_cart_row_get_by(self, product_name: str):
        """Locate the cart row container for `product_name` using semantic locators."""
        if self.env == "react":
            return self.page.get_by_test_id("cart-item").filter(has_text=product_name).first
        if self.env == "angular":
            return self.page.get_by_test_id("page-cart").locator(".cart-row").filter(has_text=product_name).first
        return self.page.get_by_role("listitem").filter(has_text=product_name).first

    def audit_cart_item_and_remove_get_by(self, product_name: str = "basketball"):
        """
        Step 4 (`getby_full` 1:1 counterpart of `audit_cart_item_and_remove_opencv`):
          - Validate thumbnail image (`img`), title (`product_name`), description (React/Angular),
            decrease button (`-`), increase button (`+`), and remove button inside the `product_name` row.
          - Click the remove button on the `product_name` row.
        """
        t4a = time.perf_counter()
        row = self._get_cart_row_get_by(product_name)
        expect(row).to_be_visible()

        # 1. Thumbnail image
        expect(row.get_by_role("img", name=product_name)).to_be_visible()

        # 2. Description & quantity controls (- / +) + remove button
        if self.env == "react":
            expect(row.get_by_test_id("cart-item-description")).to_be_visible()
            dec_btn = row.get_by_test_id("decrease-quantity")
            inc_btn = row.get_by_test_id("increase-quantity")
            rem_btn = row.get_by_test_id("remove-item-button")
            assertions_count = 5
        elif self.env == "angular":
            expect(row.locator(".cart-meta").first).to_be_visible()
            dec_btn = row.get_by_role("button", name="-")
            inc_btn = row.get_by_role("button", name="+")
            rem_btn = row.get_by_role("button", name="Quitar")
            assertions_count = 5
        else:
            dec_btn = row.get_by_role("button", name=f"Decrease quantity for {product_name}")
            inc_btn = row.get_by_role("button", name=f"Increase quantity for {product_name}")
            rem_btn = row.get_by_role("button", name="Remove")
            assertions_count = 4

        expect(dec_btn).to_be_visible()
        expect(inc_btn).to_be_visible()
        expect(rem_btn).to_be_visible()

        self._record_getby_step(
            step_name="step4a_validate_cart_row_structure",
            elapsed_ms=(time.perf_counter() - t4a) * 1000.0,
            assertions_count=assertions_count,
        )

        # 3. Title verification + click remove
        t4b = time.perf_counter()
        if self.env == "angular":
            expect(row.get_by_text(product_name, exact=True)).to_be_visible()
        else:
            expect(row.get_by_role("heading", name=product_name)).to_be_visible()

        rem_btn.click()
        self.page.wait_for_load_state("networkidle")

        self._record_getby_step(
            step_name="step4b_verify_cart_title_and_click_remove",
            elapsed_ms=(time.perf_counter() - t4b) * 1000.0,
            assertions_count=1,
        )

    def expect_product_not_in_cart_get_by(self, product_name: str = "basketball"):
        """
        Step 5 (`getby_full` 1:1 counterpart of `expect_product_not_in_cart_opencv`):
        Verify via semantic locators that `product_name` is no longer present in `/cart`.
        """
        t0 = time.perf_counter()
        if self.env == "react":
            matching_rows = self.page.get_by_test_id("cart-item").filter(has_text=product_name)
        elif self.env == "angular":
            matching_rows = self.page.get_by_test_id("page-cart").locator(".cart-row").filter(has_text=product_name)
        else:
            matching_rows = self.page.get_by_role("listitem").filter(has_text=product_name)

        expect(matching_rows).to_have_count(0)
        self._record_getby_step(
            step_name="step5_verify_product_removed_from_cart",
            elapsed_ms=(time.perf_counter() - t0) * 1000.0,
            assertions_count=1,
        )

    # --------------------------------------------------------
    # --------------------------- opencv strategy -----------------------------
    # --------------------------------------------------------

    def _template_exists(self, key: str) -> bool:
        rel_path = ENV_TEMPLATE_CATALOG.get(key, key)
        return (PLAYWRIGHT_ROOT / "templates" / self.env / rel_path).exists()

    @staticmethod
    def _pick_row_candidate(
        candidates: List[Dict[str, Any]],
        key_suffix: str,
        row_cy: float,
        max_dy: float = 105.0,
    ) -> Optional[Dict[str, Any]]:
        """Pick the candidate matching `key_suffix` whose vertical center is closest to `row_cy`."""
        matching = [
            c for c in candidates
            if key_suffix in str((c.get("meta") or {}).get("template_id", ""))
            and int((c.get("bbox") or {}).get("y", 0)) >= 80
        ]
        if not matching:
            return None
        in_row = [
            c for c in matching
            if abs(float(c["center_point"]["y"]) - row_cy) <= max_dy
        ]
        pool = in_row if in_row else matching
        return min(pool, key=lambda c: abs(float(c["center_point"]["y"]) - row_cy))

    def expect_product_in_cart_opencv(
        self, product_name: str = "basketball"
    ) -> Dict[str, Any]:
        """
        Validate on `/cart` that the added product (`product_name`) is visually present
        via Template Matching + EasyOCR + Semantic Ranking (`target_description`).
        """
        t0 = time.perf_counter()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(250)

        title_key = "cart_item_title" if self._template_exists("cart_item_title") else "product_title"
        result = self._detect_visual(
            template_keys=[title_key],
            enable_ocr=True,
            visual_threshold=0.70,
            identifier="step4-cart-item",
            target_description=product_name,
            synonyms=["basket", product_name],
        )
        title_cands = [
            c for c in result.get("candidates", [])
            if title_key in str((c.get("meta") or {}).get("template_id", ""))
            and int((c.get("bbox") or {}).get("y", 0)) >= 90
        ]
        matched_cand = next(
            (
                c for c in title_cands
                if product_name.lower() in self._extract_candidate_text(c).lower()
                or "basket" in self._extract_candidate_text(c).lower()
            ),
            title_cands[0] if title_cands else None,
        )
        assert matched_cand is not None, (
            f"[Step 4] Could not visually detect '{product_name}' inside /cart in {self.env}. "
            f"Audit dir: {result.get('audit_dir')}"
        )

        detected_text = self._extract_candidate_text(matched_cand)
        assert (
            product_name.lower() in detected_text.lower()
            or "basket" in detected_text.lower()
        ), (
            f"[Step 4] Expected product OCR in /cart to contain '{product_name}', "
            f"got '{detected_text}' in {self.env}. Audit dir: {result.get('audit_dir')}"
        )

        cx, cy = int(matched_cand["center_point"]["x"]), int(matched_cand["center_point"]["y"])
        audit_img = publish_step_audit(
            step_id="step4_cart_item_verified",
            raw_image_path=result["screenshot_path"],
            step_title=(
                f"STEP 4 [{self.env.upper()}]: Validate Product in Cart "
                f"(Template + OCR=True -> '{detected_text}')"
            ),
            annotations=[
                {"candidate": matched_cand, "role": "assert_ocr", "label": "Cart Item"}
            ],
            metadata={"enable_ocr": True, "detected_product_text": detected_text},
        )

        clear_templates_from_api()
        self._record_visual_step(
            step_name="step4_verify_product_in_cart",
            result=result,
            elapsed_ms=(time.perf_counter() - t0) * 1000.0,
            confidence_score=matched_cand.get("confidence_score"),
            enable_ocr=True,
            center_point={"x": cx, "y": cy},
            audit_image=audit_img,
        )
        return matched_cand

    def audit_cart_item_and_remove_opencv(
        self, product_name: str = "basketball"
    ) -> Dict[str, Any]:
        """
        Step 4: Visually validate the `basketball` cart row subcomponents on `/cart`:
          - Thumbnail image (`cart_item_image`)
          - Product title (`cart_item_title` + OCR == `product_name`)
          - Product description (`cart_item_description`, when present in the frontend)
          - Decrease button `-` (`cart_item_decrease`)
          - Increase button `+` (`cart_item_increase`)
          - Remove button (`cart_item_remove`)
        Then click the `remove` button of the `basketball` row to delete it from the cart.
        """
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(300)

        struct_keys = [
            k for k in (
                "cart_item_container",
                "cart_item_image",
                "cart_item_description",
                "cart_item_decrease",
                "cart_item_increase",
                "cart_item_remove",
            )
            if self._template_exists(k)
        ]
        assert struct_keys, (
            f"[Step 4] Cart item templates not found in templates/{self.env}/cart-item/. "
            f"Run: python utils/harvest_templates.py --env {self.env}"
        )

        # 4A. Structural detection of cart-item subcomponents (enable_ocr=False)
        t4a = time.perf_counter()
        res_struct = self._detect_visual(
            template_keys=struct_keys,
            enable_ocr=False,
            visual_threshold=0.70,
            identifier="step4a-cart-row-structure",
        )
        struct_cands = res_struct.get("candidates", [])
        screenshot_path = res_struct["screenshot_path"]

        # 4B. OCR verification of the product title on the same screenshot (enable_ocr=True)
        t4b = time.perf_counter()
        title_key = "cart_item_title" if self._template_exists("cart_item_title") else "product_title"
        res_title = self._detect_visual(
            template_keys=[title_key],
            enable_ocr=True,
            visual_threshold=0.70,
            identifier="step4b-cart-row-title",
            target_description=product_name,
            synonyms=["basket", product_name],
            existing_screenshot_path=screenshot_path,
        )
        title_cands = [
            c for c in res_title.get("candidates", [])
            if title_key in str((c.get("meta") or {}).get("template_id", ""))
            and int((c.get("bbox") or {}).get("y", 0)) >= 80
        ]
        matched_title = next(
            (
                c for c in title_cands
                if product_name.lower() in self._extract_candidate_text(c).lower()
                or "basket" in self._extract_candidate_text(c).lower()
            ),
            title_cands[0] if title_cands else None,
        )
        assert matched_title is not None, (
            f"[Step 4] Could not visually detect '{product_name}' title in /cart ({self.env})."
        )
        detected_text = self._extract_candidate_text(matched_title)
        assert (
            product_name.lower() in detected_text.lower()
            or "basket" in detected_text.lower()
        ), (
            f"[Step 4] Expected cart item OCR to contain '{product_name}', got '{detected_text}' ({self.env})."
        )

        # Determine the basketball row container (`matched_row`) and vertical anchor (`row_cy`)
        row_cands = [
            c for c in struct_cands
            if "cart_item_container" in str((c.get("meta") or {}).get("template_id", ""))
            and int((c.get("bbox") or {}).get("y", 0)) >= 80
        ]
        img_cands = [
            c for c in struct_cands
            if "cart_item_image" in str((c.get("meta") or {}).get("template_id", ""))
            and int((c.get("bbox") or {}).get("y", 0)) >= 80
        ]
        matched_img = img_cands[0] if img_cands else None
        assert matched_img is not None, (
            f"[Step 4] Could not visually detect basketball thumbnail ('cart_item_image') in /cart ({self.env})."
        )

        matched_row = next(
            (r for r in row_cands if self._is_inside_bbox(matched_img, r, pad=16)),
            row_cands[0] if row_cands else None,
        )
        row_cy = float(matched_img["center_point"]["y"])

        def _resolve_in_row(key_suffix: str) -> Optional[Dict[str, Any]]:
            sub_cands = [
                c for c in struct_cands
                if key_suffix in str((c.get("meta") or {}).get("template_id", ""))
            ]
            if matched_row is not None:
                inside = self._find_child_inside_bbox(sub_cands, matched_row, pad=14)
                if inside is not None:
                    return inside
            return self._pick_row_candidate(struct_cands, key_suffix, row_cy)

        matched_desc = (
            _resolve_in_row("cart_item_description")
            if "cart_item_description" in struct_keys
            else None
        )
        matched_dec = _resolve_in_row("cart_item_decrease")
        matched_inc = _resolve_in_row("cart_item_increase")
        matched_rem = _resolve_in_row("cart_item_remove")

        assert matched_dec is not None, f"[Step 4] Could not detect '-' button in basketball cart row ({self.env})."
        assert matched_inc is not None, f"[Step 4] Could not detect '+' button in basketball cart row ({self.env})."
        assert matched_rem is not None, f"[Step 4] Could not detect 'remove' button in basketball cart row ({self.env})."
        if "cart_item_description" in struct_keys:
            assert matched_desc is not None, (
                f"[Step 4] Could not detect product description in basketball cart row ({self.env})."
            )

        annotations = [
            {"candidate": matched_img, "role": "assert_visual", "label": "Thumb (basketball)"},
            {"candidate": matched_title, "role": "assert_ocr", "label": "Title"},
        ]
        if matched_desc is not None:
            annotations.append(
                {"candidate": matched_desc, "role": "assert_visual", "label": "Description"}
            )
        annotations.extend(
            [
                {"candidate": matched_dec, "role": "assert_visual", "label": "Btn (-)"},
                {"candidate": matched_inc, "role": "assert_visual", "label": "Btn (+)"},
                {"candidate": matched_rem, "role": "click", "label": "Remove Item"},
            ]
        )

        self._record_visual_step(
            step_name="step4a_validate_cart_row_structure",
            result=res_struct,
            elapsed_ms=(time.perf_counter() - t4a) * 1000.0,
            confidence_score=matched_img.get("confidence_score"),
            enable_ocr=False,
            visual_assertions_count=len(annotations) - 1,
        )

        rem_x = int(matched_rem["center_point"]["x"])
        rem_y = int(matched_rem["center_point"]["y"])
        audit_img = publish_step_audit(
            step_id="step4_cart_item_verified",
            raw_image_path=screenshot_path,
            step_title=(
                f"STEP 4 [{self.env.upper()}]: Audit Cart Item ('{detected_text}') + "
                f"Thumb/Controls (-/+) + Click Remove"
            ),
            annotations=annotations,
            metadata={
                "enable_ocr": True,
                "detected_product_text": detected_text,
                "thumb_confidence": matched_img.get("confidence_score"),
                "remove_confidence": matched_rem.get("confidence_score"),
                "reused_screenshot": True,
            },
        )

        self.page.mouse.click(rem_x, rem_y)
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(400)

        self._record_visual_step(
            step_name="step4b_verify_cart_title_and_click_remove",
            result=res_title,
            elapsed_ms=(time.perf_counter() - t4b) * 1000.0,
            confidence_score=matched_rem.get("confidence_score"),
            enable_ocr=True,
            center_point={"x": rem_x, "y": rem_y},
            reused_screenshot=True,
            audit_image=audit_img,
        )
        return {
            "image": matched_img,
            "title": matched_title,
            "description": matched_desc,
            "decrease": matched_dec,
            "increase": matched_inc,
            "remove": matched_rem,
        }

    def expect_product_not_in_cart_opencv(
        self, product_name: str = "basketball"
    ) -> Dict[str, Any]:
        """
        Step 5: Visually validate on `/cart` that `product_name` ('basketball') is no longer present
        after clicking its remove button (neither its thumbnail image nor its OCR title appears).
        """
        t0 = time.perf_counter()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(350)

        title_key = "cart_item_title" if self._template_exists("cart_item_title") else "product_title"
        check_keys = [k for k in ("cart_item_image", title_key) if self._template_exists(k)]

        result = self._detect_visual(
            template_keys=check_keys,
            enable_ocr=True,
            visual_threshold=0.72,
            identifier="step5-cart-item-removed",
        )
        cands = result.get("candidates", [])

        remaining_thumb = [
            c for c in cands
            if "cart_item_image" in str((c.get("meta") or {}).get("template_id", ""))
            and float((c.get("meta") or {}).get("template_score") or c.get("confidence_score") or 0.0) >= 0.78
            and int((c.get("bbox") or {}).get("y", 0)) >= 80
        ]
        remaining_title = [
            c for c in cands
            if (
                product_name.lower() in self._extract_candidate_text(c).lower()
                or "basket" in self._extract_candidate_text(c).lower()
            )
            and int((c.get("bbox") or {}).get("y", 0)) >= 80
        ]

        assert not remaining_thumb and not remaining_title, (
            f"[Step 5] Expected '{product_name}' to be removed from /cart in {self.env}, "
            f"but still found thumb={len(remaining_thumb)}, title={len(remaining_title)}. "
            f"Audit dir: {result.get('audit_dir')}"
        )

        audit_img = publish_step_audit(
            step_id="step5_cart_item_removed",
            raw_image_path=result["screenshot_path"],
            step_title=(
                f"STEP 5 [{self.env.upper()}]: Verify '{product_name}' Removed from Cart "
                f"(0 matches -> Removed OK)"
            ),
            annotations=[],
            metadata={
                "enable_ocr": True,
                "removed_product": product_name,
                "remaining_basketball_matches": 0,
            },
        )

        clear_templates_from_api()
        self._record_visual_step(
            step_name="step5_verify_product_removed_from_cart",
            result=result,
            elapsed_ms=(time.perf_counter() - t0) * 1000.0,
            confidence_score=1.0,
            enable_ocr=True,
            audit_image=audit_img,
        )
        return result
