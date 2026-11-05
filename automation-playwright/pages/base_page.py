import time
from typing import Any, Dict, List, Optional
from playwright.sync_api import expect
from utils.openvisor_helper import (
    detect_for_openvisor,
    publish_step_audit,
    register_env_templates,
)
from utils.telemetry import telemetry


class BasePage:
    def __init__(
        self,
        page,
        base_url: str,
        selectors: Optional[dict] = None,
        env: Optional[str] = None,
    ):
        self.page = page
        self.base_url = base_url
        self.selectors = selectors or {}
        self.env = env or telemetry.frontend
        self.timeout = 8000
        self.ocr_warnings: List[str] = []

    def navigate(self, path: str = "/"):
        self.page.goto(f"{self.base_url}{path}")
        self.page.wait_for_load_state("networkidle")

    def get_title(self) -> str:
        return self.page.title()

    def expect_cart_count(self, expected: int):
        badge = self.page.locator(self.selectors["cart_counter"])

        expect(badge).to_be_visible()
        expect(badge).to_contain_text(str(expected))

    def go_to_cart(self):
        self.page.locator(self.selectors["nav_cart"]).click()
        self.page.wait_for_load_state("networkidle")

    def go_to_products(self):
        self.page.locator(self.selectors["nav_products"]).click()
        self.page.wait_for_load_state("networkidle")

    def go_to_login(self):
        self.page.locator(self.selectors["nav_login"]).click()
        self.page.wait_for_load_state("networkidle")

    def logout(self):
        self.page.locator(self.selectors["logout"]).click()
        self.page.wait_for_load_state("networkidle")

    # --------------------------------------------------------
    # --------------------------- get by strategy -----------------------------
    # --------------------------------------------------------

    def _get_locator_by(self, selector_key: str):
        """Resolves the locator natively using get_by_role or get_by_test_id"""
        config = self.selectors[selector_key]

        # Case 1: Selector is defined as a dictionary (uses get_by_role)
        if isinstance(config, dict):
            role = config["role"]
            name = config.get("name")
            if name:
                locator = self.page.get_by_role(role, name=name)
            else:
                locator = self.page.get_by_role(role)
            # support for child locator if specified
            if "child" in config:
                locator = locator.locator(config["child"])
            return locator

        # Case 2: Selector is defined as a string (uses get_by_test_id)
        else:
            by_test = self.page.get_by_test_id(config)
            if by_test.count() > 0:
                return by_test.nth(0)
            return self.page.get_by_test_id(config)

    def _record_getby_step(
        self,
        step_name: str,
        elapsed_ms: float,
        assertions_count: int = 1,
    ) -> None:
        """Record standardized step telemetry for semantic get_by E2E flows."""
        telemetry.record_step(
            step_name=step_name,
            strategy=telemetry.strategy or "getby_full",
            frontend=self.env,
            layer_resolved="dom_getby",
            total_step_ms=elapsed_ms,
            candidates_count=1,
            confidence_score=1.0,
            dom_ground_truth_hit=True,
            success=True,
            visual_assertions_count=assertions_count,
        )

    def expect_cart_count_get_by(self, expected: int):
        badge = self._get_locator_by("cart_counter")

        expect(badge).to_be_visible()
        expect(badge).to_contain_text(str(expected))

    def go_to_login_get_by(self):
        self._get_locator_by("nav_login").click()
        self.page.wait_for_load_state("networkidle")

    def go_to_cart_get_by(self):
        self._get_locator_by("nav_cart").click()
        self.page.wait_for_load_state("networkidle")

    def go_to_products_get_by(self):
        t0 = time.perf_counter()
        self._get_locator_by("nav_products").click()
        self.page.wait_for_load_state("networkidle")
        if telemetry.strategy == "getby_full":
            self._record_getby_step(
                step_name="step1_nav_products",
                elapsed_ms=(time.perf_counter() - t0) * 1000.0,
            )

    def verify_cart_and_open_get_by(self, expected: int = 1):
        """
        Step 3 (getby_full): Validate the navbar cart badge counter via semantic locators
        and click the cart link/button to open `/cart`.
        """
        t0 = time.perf_counter()
        self.expect_cart_count_get_by(expected=expected)
        self.go_to_cart_get_by()
        self._record_getby_step(
            step_name="step3_verify_cart_one_and_open",
            elapsed_ms=(time.perf_counter() - t0) * 1000.0,
            assertions_count=1,
        )

    def logout_get_by(self):
        self._get_locator_by("logout").click()
        self.page.wait_for_load_state("networkidle")

    # --------------------------------------------------------
    # --------------------------- opencv strategy -----------------------------
    # --------------------------------------------------------

    @staticmethod
    def _pick_header_candidate(
        candidates: List[Dict[str, Any]], max_y: int = 140
    ) -> Optional[Dict[str, Any]]:
        """Return the highest-confidence candidate within the top navigation header."""
        if not candidates:
            return None
        header_cands = [
            c for c in candidates if int((c.get("bbox") or {}).get("y", 9999)) <= max_y
        ]
        return header_cands[0] if header_cands else candidates[0]

    @staticmethod
    def _extract_candidate_text(cand: Dict[str, Any]) -> str:
        """Extract OCR text from a detected candidate."""
        return (
            cand.get("semantic_text")
            or (cand.get("ocr_details") or {}).get("text")
            or ""
        )

    @staticmethod
    def _is_inside_bbox(
        child: Dict[str, Any], container: Dict[str, Any], pad: int = 8
    ) -> bool:
        """
        Return True if `child`'s center point lies inside `container`'s bounding box
        (with optional tolerance `pad` in pixels).
        """
        cb = container.get("bbox") or {}
        center = child.get("center_point") or {}
        if not cb or "x" not in center or "y" not in center:
            return False
        cx, cy = int(center["x"]), int(center["y"])
        return (
            (int(cb["x"]) - pad) <= cx <= (int(cb["x"]) + int(cb["width"]) + pad)
            and (int(cb["y"]) - pad) <= cy <= (int(cb["y"]) + int(cb["height"]) + pad)
        )

    @classmethod
    def _find_child_inside_bbox(
        cls,
        candidates: List[Dict[str, Any]],
        container: Dict[str, Any],
        pad: int = 8,
    ) -> Optional[Dict[str, Any]]:
        """Return the highest-confidence candidate from `candidates` whose center lies inside `container`."""
        return next(
            (c for c in candidates if cls._is_inside_bbox(c, container, pad=pad)),
            None,
        )

    def _detect_visual(
        self,
        template_keys: List[str],
        enable_ocr: bool,
        visual_threshold: float,
        identifier: str,
        target_description: Optional[str] = None,
        synonyms: Optional[List[str]] = None,
        existing_screenshot_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register environment templates and run OpenVisor detection."""
        register_env_templates(self.env, template_keys, clear_first=True)
        return detect_for_openvisor(
            self.page,
            target_description=target_description,
            synonyms=synonyms,
            enable_ocr=enable_ocr,
            visual_threshold=visual_threshold,
            existing_screenshot_path=existing_screenshot_path,
            identifier=f"{self.env}-{identifier}",
        )

    def _record_visual_step(
        self,
        step_name: str,
        result: Dict[str, Any],
        elapsed_ms: float,
        confidence_score: Optional[float],
        enable_ocr: bool,
        visual_assertions_count: int = 1,
        center_point: Optional[Dict[str, int]] = None,
        success: bool = True,
        reused_screenshot: bool = False,
        audit_image: Optional[str] = None,
    ) -> None:
        """Record standardized step telemetry for visual operations."""
        ct = result.get("client_timings_ms") or {}
        st = result.get("timings_ms") or {}
        telemetry.record_step(
            step_name=step_name,
            strategy=telemetry.strategy or "opencv_full",
            frontend=self.env,
            layer_resolved="vision_template_ocr" if enable_ocr else "vision_template",
            total_step_ms=elapsed_ms,
            capture_ms=ct.get("capture_ms", 0.0),
            network_ms=ct.get("network_ms", 0.0),
            server_timings_ms=st,
            candidates_count=len(result.get("candidates", [])),
            confidence_score=confidence_score,
            center_point=center_point,
            success=success,
            enable_ocr=enable_ocr,
            reused_screenshot=reused_screenshot,
            visual_assertions_count=visual_assertions_count,
            audit_image=audit_image,
        )

    def go_to_products_opencv(self) -> Dict[str, Any]:
        """Locate 'Products' in the navbar via pure template matching (`enable_ocr=False`) and click."""
        t0 = time.perf_counter()
        result = self._detect_visual(
            template_keys=["nav_products"],
            enable_ocr=False,
            visual_threshold=0.70,
            identifier="step1-nav-products",
        )
        cand = self._pick_header_candidate(result.get("candidates", []), max_y=140)
        assert cand is not None, (
            f"[Step 1] Could not visually detect 'nav_products' in {self.env}. "
            f"Audit dir: {result.get('audit_dir')}"
        )

        cx, cy = int(cand["center_point"]["x"]), int(cand["center_point"]["y"])
        audit_img = publish_step_audit(
            step_id="step1_nav_products",
            raw_image_path=result["screenshot_path"],
            step_title=f"STEP 1 [{self.env.upper()}]: Click Nav Products (Template Match, OCR=False)",
            annotations=[{"candidate": cand, "role": "click", "label": "Nav: Products"}],
            metadata={"enable_ocr": False},
        )

        self.page.mouse.click(cx, cy)
        self.page.wait_for_load_state("networkidle")
        self._record_visual_step(
            step_name="step1_nav_products",
            result=result,
            elapsed_ms=(time.perf_counter() - t0) * 1000.0,
            confidence_score=cand.get("confidence_score"),
            enable_ocr=False,
            center_point={"x": cx, "y": cy},
            audit_image=audit_img,
        )
        return cand

    def verify_cart_and_open_opencv(self, expected: int = 1) -> Dict[str, Any]:
        """
        Validate the navbar cart badge counter via OCR (`enable_ocr=True`, soft-assert)
        and click its visual center to navigate to `/cart`.
        """
        t0 = time.perf_counter()
        result = self._detect_visual(
            template_keys=["nav_cart"],
            enable_ocr=True,
            visual_threshold=0.70,
            identifier="step3-cart-one",
        )
        cand = self._pick_header_candidate(result.get("candidates", []), max_y=140)
        assert cand is not None, (
            f"[Step 3] Could not visually detect 'nav_cart' in {self.env}. "
            f"Audit dir: {result.get('audit_dir')}"
        )

        ocr_text = self._extract_candidate_text(cand)
        ocr_ok = str(expected) in ocr_text
        if not ocr_ok:
            warn_msg = (
                f"[Step 3 OCR Warning] Expected cart counter OCR to contain '{expected}', "
                f"got '{ocr_text}' in {self.env} (clicking Cart anyway)."
            )
            print(warn_msg)
            self.ocr_warnings.append(warn_msg)

        cx, cy = int(cand["center_point"]["x"]), int(cand["center_point"]["y"])
        audit_img = publish_step_audit(
            step_id="step3_cart_incremented",
            raw_image_path=result["screenshot_path"],
            step_title=f"STEP 3 [{self.env.upper()}]: Validate Cart={expected} (OCR=True) + Click Cart",
            annotations=[
                {
                    "candidate": cand,
                    "role": "assert_ocr" if ocr_ok else "assert_ocr_warn",
                    "label": f"Cart={expected}",
                },
                {"candidate": cand, "role": "click", "label": "Open Cart"},
            ],
            metadata={"enable_ocr": True, "cart1_ocr_text": ocr_text, "cart1_ocr_passed": ocr_ok},
        )

        self.page.mouse.click(cx, cy)
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(300)
        self._record_visual_step(
            step_name="step3_verify_cart_one_and_open",
            result=result,
            elapsed_ms=(time.perf_counter() - t0) * 1000.0,
            confidence_score=cand.get("confidence_score"),
            enable_ocr=True,
            center_point={"x": cx, "y": cy},
            success=ocr_ok,
            audit_image=audit_img,
        )
        return cand
