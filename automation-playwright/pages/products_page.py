import time
from typing import Optional, List, Dict, Tuple, Any
from playwright.sync_api import expect
from pages.base_page import BasePage
from utils.openvisor_helper import (
    ENV_TEMPLATE_CATALOG,
    PLAYWRIGHT_ROOT,
    detect_for_openvisor,
    publish_step_audit,
    record_playwright_action,
)
from utils.telemetry import telemetry


class ProductsPage(BasePage):
    def goto(self):
        self.navigate("/products")

    def get_product_cards(self):
        return self.page.locator(self.selectors["product_card"])

    def _get_dom_ground_truth(self, x: int, y: int, index: int = 0) -> Tuple[Optional[bool], Optional[Dict[str, float]]]:
        """
        Retrieve the DOM bounding boxes of the target button(s) and verify whether the vision
        click point (x, y) falls inside any valid target button in the catalog.
        """
        selector = self.selectors.get("add_to_cart")
        if not selector or not isinstance(selector, str):
            return None, None
        try:
            loc = self.page.locator(selector)
            count = loc.count()
            if count == 0:
                return None, None

            first_box = None
            for i in range(count):
                box = loc.nth(i).bounding_box(timeout=1000)
                if not box:
                    continue
                if first_box is None:
                    first_box = box
                if (
                    box["x"] <= x <= box["x"] + box["width"]
                    and box["y"] <= y <= box["y"] + box["height"]
                ):
                    return True, box
            return False, first_box
        except Exception:
            return None, None

    def add_to_cart(self, index: int = 0):
        t0 = time.perf_counter()
        self.page.locator(self.selectors["add_to_cart"]).nth(index).click()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        telemetry.record_step(
            step_name="add_to_cart",
            strategy="base",
            frontend=telemetry.frontend,
            layer_resolved="dom_css",
            total_step_ms=elapsed_ms,
            candidates_count=1,
            confidence_score=1.0,
            dom_ground_truth_hit=True,
            success=True,
        )

    def add_laptop_to_cart(self, page):
        self.page = page
        self.laptop_pro_card = page.locator(".product-card").filter(has_text="Laptop Pro")
        self.laptop_pro_add_to_cart_button = self.laptop_pro_card.get_by_role(
            "button",
            name="Agregar al carrito"
        )
        self.laptop_pro_add_to_cart_button.click()

    def add_to_cart_get_by(self, index: int = 0):
        t0 = time.perf_counter()
        self._get_locator_by("add_to_cart").nth(index).click()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        telemetry.record_step(
            step_name="add_to_cart",
            strategy="getby",
            frontend=telemetry.frontend,
            layer_resolved="dom_getby",
            total_step_ms=elapsed_ms,
            candidates_count=1,
            confidence_score=1.0,
            dom_ground_truth_hit=True,
            success=True,
        )

    def _get_product_card_get_by(self, product_name: str):
        """Locate a specific catalog card by product heading using semantic locators."""
        heading = self.page.get_by_role("heading", name=product_name)
        if self.env in ("angular", "svelte"):
            return self.page.get_by_role("article").filter(has=heading).first
        return self.page.locator(".product-card").filter(has=heading).first

    def audit_catalog_and_add_to_cart_get_by(self, items_to_add: int = 2):
        """
        Step 2 (`getby_full` 1:1 counterpart of `audit_catalog_and_add_to_cart_opencv`):
          1. Validate that the `basketball` card, `Laptop Pro` card, and their `Add to Cart`
             buttons are visible in the DOM.
          2. Validate that the initial cart counter equals `0`.
          3. Click `Add to Cart` inside `basketball` and inside `Laptop Pro`.
        """
        add_btn_cfg = self.selectors.get("add_to_cart") or {"role": "button"}
        add_btn_name = add_btn_cfg.get("name") if isinstance(add_btn_cfg, dict) else None

        # 2A. Validate Product Cards & Add to Cart buttons
        t2a = time.perf_counter()
        basketball_card = self._get_product_card_get_by("basketball")
        expect(basketball_card).to_be_visible()
        basketball_add_btn = basketball_card.get_by_role("button", name=add_btn_name)
        expect(basketball_add_btn).to_be_visible()

        laptop_add_btn = None
        if items_to_add >= 2:
            laptop_card = self._get_product_card_get_by("Laptop Pro")
            expect(laptop_card).to_be_visible()
            laptop_add_btn = laptop_card.get_by_role("button", name=add_btn_name)
            expect(laptop_add_btn).to_be_visible()

        self._record_getby_step(
            step_name="step2a_validate_product_card_and_btn",
            elapsed_ms=(time.perf_counter() - t2a) * 1000.0,
            assertions_count=4 if items_to_add >= 2 else 2,
        )

        # 2B. Validate Cart == 0 and click Add to Cart on both cards
        t2b = time.perf_counter()
        self.expect_cart_count_get_by(expected=0)
        basketball_add_btn.click()
        self.page.wait_for_load_state("networkidle")

        if laptop_add_btn is not None:
            laptop_add_btn.click()
            self.page.wait_for_load_state("networkidle")

        self._record_getby_step(
            step_name="step2b_validate_cart_zero_and_click_add",
            elapsed_ms=(time.perf_counter() - t2b) * 1000.0,
            assertions_count=1,
        )

    # --------------------------------------------------------
    # --------------------------- opencv strategy -----------------------------
    # --------------------------------------------------------

    def add_to_cart_opencv(
        self,
        index: int = 0,
        enable_ocr: bool = True,
        target_description: Optional[str] = "Add to cart",
        synonyms: Optional[List[str]] = None,
        visual_threshold: Optional[float] = None,
    ):
        """
        Add to cart using OpenVisor visual detection and record layer-by-layer telemetry + visual audit.
        """
        if synonyms is None:
            synonyms = ["bag", "carrito", "agregar"]

        desc = target_description if enable_ocr else None
        t0 = time.perf_counter()

        result = detect_for_openvisor(
            self.page,
            target_description=desc,
            element_type="button" if enable_ocr else None,
            synonyms=synonyms if enable_ocr else None,
            enable_ocr=enable_ocr,
            visual_threshold=visual_threshold,
            identifier="products-add-to-cart"
        )

        audit_dir = result.get("audit_dir")
        candidates = result.get("candidates", [])
        client_timings = result.get("client_timings_ms") or {}
        server_timings = result.get("timings_ms") or {}

        if not candidates:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            telemetry.record_step(
                step_name="add_to_cart",
                strategy="opencv",
                frontend=telemetry.frontend,
                layer_resolved="vision_failed",
                total_step_ms=elapsed_ms,
                capture_ms=client_timings.get("capture_ms", 0.0),
                network_ms=client_timings.get("network_ms", 0.0),
                server_timings_ms=server_timings,
                candidates_count=0,
                confidence_score=0.0,
                dom_ground_truth_hit=False,
                success=False,
            )
            record_playwright_action(
                audit_dir=audit_dir,
                candidate=None,
                action="none",
                status="failed",
                error=f"OpenVisor could not detect element with description='{desc}'"
            )
            raise AssertionError(
                f"OpenVisor could not detect element with description='{desc}'"
            )

        candidate = candidates[index]
        center = candidate.get("center_point", {})
        x = center.get("x")
        y = center.get("y")

        if x is None or y is None:
            record_playwright_action(
                audit_dir=audit_dir,
                candidate=candidate,
                action="click",
                index=index,
                status="failed",
                error=f"Invalid candidate coordinates: {candidate}"
            )
            raise AssertionError(
                f"Invalid candidate coordinates: {candidate}"
            )

        dom_hit, dom_bbox = self._get_dom_ground_truth(int(x), int(y), index=index)

        record_playwright_action(
            audit_dir=audit_dir,
            candidate=candidate,
            action="click",
            index=index,
            status="success",
            dom_bbox=dom_bbox,
            dom_ground_truth_hit=dom_hit,
        )

        self.page.mouse.click(x, y)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        layer_name = "vision_template_ocr" if enable_ocr else "vision_template"
        telemetry.record_step(
            step_name="add_to_cart",
            strategy="opencv",
            frontend=telemetry.frontend,
            layer_resolved=layer_name,
            total_step_ms=elapsed_ms,
            capture_ms=client_timings.get("capture_ms", 0.0),
            network_ms=client_timings.get("network_ms", 0.0),
            server_timings_ms=server_timings,
            candidates_count=len(candidates),
            confidence_score=candidate.get("confidence_score"),
            center_point={"x": int(x), "y": int(y)},
            dom_ground_truth_hit=dom_hit,
            success=True,
        )

    def audit_catalog_and_add_to_cart_opencv(self, items_to_add: int = 2) -> Dict[str, Any]:
        """
        Validate catalog UI components on `/products` and click 'Add to Cart':
          1. Structural check (`enable_ocr=False`): validate `product_card` (basketball),
             `laptop_card` (Laptop Pro), and `add_to_cart` buttons.
          2. Hierarchical BBox containment (`_find_child_inside_bbox`): resolve the specific
             `add_to_cart` button inside `basketball`'s BBox and the one inside `Laptop Pro`'s BBox.
          3. State check (`enable_ocr=True`, reusing the same screenshot): validate `nav_cart == 0`.
          4. Publish consolidated multi-bbox audit image and click both `add_to_cart` buttons.
        """
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(250)

        has_laptop_tpl = (
            PLAYWRIGHT_ROOT / "templates" / self.env / ENV_TEMPLATE_CATALOG["laptop_card"]
        ).exists()
        struct_keys = ["product_card", "add_to_cart"]
        if items_to_add >= 2 and has_laptop_tpl:
            struct_keys.insert(1, "laptop_card")

        # 2A. Structural validation (Product Cards + Add to Cart buttons, enable_ocr=False)
        t2a = time.perf_counter()
        res_struct = self._detect_visual(
            template_keys=struct_keys,
            enable_ocr=False,
            visual_threshold=0.70,
            identifier="step2a-catalog-structure",
        )
        struct_cands = res_struct.get("candidates", [])
        screenshot_path = res_struct["screenshot_path"]

        card_cands = [
            c for c in struct_cands
            if str((c.get("meta") or {}).get("template_id", "")).endswith("product_card")
        ]
        laptop_cands = [
            c for c in struct_cands
            if str((c.get("meta") or {}).get("template_id", "")).endswith("laptop_card")
        ]
        btn_cands = [
            c for c in struct_cands
            if str((c.get("meta") or {}).get("template_id", "")).endswith("add_to_cart")
        ]
        assert card_cands, f"[Step 2A] Product Card (basketball) not detected in {self.env}."
        assert btn_cands, f"[Step 2A] Add to Cart button not detected in {self.env}."

        best_card = card_cands[0]
        target_btn = self._find_child_inside_bbox(btn_cands, best_card) or btn_cands[0]

        laptop_card = laptop_cands[0] if laptop_cands else None
        second_btn = None
        if items_to_add >= 2:
            if laptop_card is not None:
                second_btn = self._find_child_inside_bbox(btn_cands, laptop_card)
            if second_btn is None:
                outside_btns = sorted(
                    [
                        b for b in btn_cands
                        if b is not target_btn and not self._is_inside_bbox(b, best_card)
                    ],
                    key=lambda b: (int(b["center_point"]["y"]) // 80, int(b["center_point"]["x"])),
                )
                second_btn = outside_btns[0] if outside_btns else target_btn

        visual_assertions_count = 3 if laptop_card is not None else 2
        self._record_visual_step(
            step_name="step2a_validate_product_card_and_btn",
            result=res_struct,
            elapsed_ms=(time.perf_counter() - t2a) * 1000.0,
            confidence_score=best_card.get("confidence_score"),
            enable_ocr=False,
            visual_assertions_count=visual_assertions_count,
        )

        # 2B. Dynamic OCR validation of Cart=0 reusing the same screenshot
        t2b = time.perf_counter()
        res_cart0 = self._detect_visual(
            template_keys=["nav_cart"],
            enable_ocr=True,
            visual_threshold=0.70,
            identifier="step2b-cart-zero",
            existing_screenshot_path=screenshot_path,
        )
        cart0_cand = self._pick_header_candidate(res_cart0.get("candidates", []), max_y=140)
        assert cart0_cand is not None, f"[Step 2B] 'nav_cart' badge not detected in {self.env}."

        cart0_text = self._extract_candidate_text(cart0_cand)
        ocr_zero_ok = "0" in cart0_text
        if not ocr_zero_ok:
            warn_msg = (
                f"[Step 2B OCR Warning] Expected initial cart counter OCR to contain '0', "
                f"got '{cart0_text}' in {self.env} (continuing flow)."
            )
            print(warn_msg)
            self.ocr_warnings.append(warn_msg)

        annotations = [
            {"candidate": best_card, "role": "assert_visual", "label": "Card: basketball"},
        ]
        if laptop_card is not None:
            annotations.append(
                {"candidate": laptop_card, "role": "assert_visual", "label": "Card: Laptop Pro"}
            )
        annotations.extend(
            [
                {
                    "candidate": cart0_cand,
                    "role": "assert_ocr" if ocr_zero_ok else "assert_ocr_warn",
                    "label": "Cart=0",
                },
                {"candidate": target_btn, "role": "click", "label": "Add #1 (in basketball BBox)"},
            ]
        )
        if second_btn is not None and second_btn is not target_btn:
            annotations.append(
                {"candidate": second_btn, "role": "click", "label": "Add #2 (in Laptop Pro BBox)"}
            )

        click_x, click_y = int(target_btn["center_point"]["x"]), int(target_btn["center_point"]["y"])
        audit_img = publish_step_audit(
            step_id="step2_products_ui_audit",
            raw_image_path=screenshot_path,
            step_title=(
                f"STEP 2 [{self.env.upper()}]: Validate Cards (basketball + Laptop Pro, OCR=False) + "
                f"Cart=0 (OCR=True) + Click Both Add to Cart"
            ),
            annotations=annotations,
            metadata={
                "basketball_card_confidence": best_card.get("confidence_score"),
                "laptop_card_confidence": laptop_card.get("confidence_score") if laptop_card else None,
                "cart0_ocr_text": cart0_text,
                "cart0_ocr_passed": ocr_zero_ok,
                "add_to_cart_confidence": target_btn.get("confidence_score"),
                "items_added": items_to_add,
                "reused_screenshot": True,
            },
        )

        self.page.mouse.click(click_x, click_y)
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(350)

        if second_btn is not None:
            sx, sy = int(second_btn["center_point"]["x"]), int(second_btn["center_point"]["y"])
            self.page.mouse.click(sx, sy)
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(350)

        self._record_visual_step(
            step_name="step2b_validate_cart_zero_and_click_add",
            result=res_cart0,
            elapsed_ms=(time.perf_counter() - t2b) * 1000.0,
            confidence_score=target_btn.get("confidence_score"),
            enable_ocr=True,
            center_point={"x": click_x, "y": click_y},
            success=ocr_zero_ok,
            reused_screenshot=True,
            audit_image=audit_img,
        )
        return {
            "product_card": best_card,
            "laptop_card": laptop_card,
            "cart_zero": cart0_cand,
            "add_to_cart": target_btn,
            "second_add_to_cart": second_btn,
            "ocr_zero_ok": ocr_zero_ok,
        }
