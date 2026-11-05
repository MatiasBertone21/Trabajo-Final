import os
import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import Page, expect
import requests
import cv2
from typing import Optional, Dict, Any, List
import numpy as np
from utils.telemetry import telemetry

PLAYWRIGHT_ROOT = Path(__file__).resolve().parent.parent

# Logical catalog mapping component keys to relative paths under templates/<env>/
ENV_TEMPLATE_CATALOG: Dict[str, str] = {
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


def capture_for_openvisor(page: Page, identifier: str):
    """
    Capture the current browser viewport for OpenVisor analysis.

    Returns:
        Path to the generated screenshot.
    """
    page.wait_for_load_state("networkidle")

    folder_path = os.path.join(os.getcwd(), "openvisor-inputs")
    os.makedirs(folder_path, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    filename = f"{identifier}-{timestamp}.png"
    file_path = os.path.join(folder_path, filename)

    page.screenshot(
        path=file_path,
        full_page=False,
        animations="disabled"
    )

    print(f"screenshot saved: {file_path}")

    return file_path


def capture_element_for_openvisor(page: Page, element_selector: str, identifier: str):
    page.wait_for_load_state("networkidle")

    folder_path = os.path.join(os.getcwd(), "openvisor-inputs")
    os.makedirs(folder_path, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    filename = f"{identifier}-{timestamp}.png"
    file_path = os.path.join(folder_path, filename)

    element = page.locator(element_selector).first
    element.wait_for(state="visible")

    element.screenshot(
        path=file_path,
        animations="disabled"
    )

    print(f"screenshot saved: {file_path}")


def request_api_vision_detection(
        image_path: str,
        target_description: Optional[str] = None,
        element_type: Optional[str] = None,
        synonyms: Optional[List[str]] = None,
        strategies: Optional[List[str]] = None,
        enable_ocr: bool = True,
        visual_threshold: Optional[float] = None,
        api_url: Optional[str] = None
    ) -> Dict[str, Any]:
    """
    Send screenshot to vision-service API for element detection.
    """
    if api_url is None:
        api_url = os.getenv("VISION_API_URL", "http://localhost:8001/api/vision/detect")

    if not api_url.endswith("/detect"):
        api_url = api_url.rstrip("/") + "/detect"

    try:
        with open(image_path, "rb") as image_file:
            files = {"file": image_file}
            params = {
                "enable_ocr": "true" if enable_ocr else "false"
            }

            if strategies:
                params["strategies"] = ",".join(strategies)

            if visual_threshold is not None:
                params["visual_threshold"] = str(visual_threshold)

            if enable_ocr and target_description:
                params["target_description"] = target_description
            if enable_ocr and element_type:
                params["element_type"] = element_type
            if enable_ocr and synonyms:
                params["synonyms"] = ",".join(synonyms)

            response = requests.post(api_url, files=files, params=params)
            response.raise_for_status()

            result = response.json()
            print(f"Vision API Response (enable_ocr={enable_ocr}): {result.get('candidates_count', 0)} candidates found")

            if "openvisor-inputs" in image_path:
                json_path = os.path.splitext(image_path)[0] + ".json"
                with open(json_path, "w") as json_file:
                    json.dump(result, json_file, indent=2)
                print(f"Detection saved: {json_path}")

            return result

    except FileNotFoundError:
        print(f"Screenshot file not found: {image_path}")
        raise
    except requests.exceptions.ConnectionError:
        print(f"Cannot connect to Vision API at {api_url}")
        raise
    except requests.exceptions.RequestException as e:
        print(f"Vision API error: {e}")
        raise


def render_annotated_detection(
    image_path: str,
    candidates: List[Dict[str, Any]],
    output_path: str,
    selected_index: Optional[int] = 0,
    dom_bbox: Optional[Dict[str, float]] = None,
):
    """
    Render bounding boxes, center points, OCR labels and optional DOM ground-truth bbox
    on top of the screenshot.
    """
    img = cv2.imread(image_path)
    if img is None:
        return

    if dom_bbox:
        dx = int(dom_bbox.get("x", 0))
        dy = int(dom_bbox.get("y", 0))
        dw = int(dom_bbox.get("width", 0))
        dh = int(dom_bbox.get("height", 0))
        cv2.rectangle(img, (dx, dy), (dx + dw, dy + dh), (255, 255, 0), 2)
        cv2.putText(
            img,
            "DOM Ground Truth",
            (dx, max(15, dy - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (255, 255, 0),
            1,
            cv2.LINE_AA,
        )

    if not candidates:
        cv2.putText(
            img,
            "NO CANDIDATES DETECTED",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 0, 255),
            2,
            cv2.LINE_AA
        )
    else:
        for idx, c in enumerate(candidates):
            bbox = c.get("bbox", {})
            bx = int(bbox.get("x", 0))
            by = int(bbox.get("y", 0))
            bw = int(bbox.get("width", 0))
            bh = int(bbox.get("height", 0))

            is_selected = (selected_index is not None and idx == selected_index)
            box_color = (0, 255, 0) if is_selected else (0, 180, 255)
            thickness = 3 if is_selected else 2

            cv2.rectangle(img, (bx, by), (bx + bw, by + bh), box_color, thickness)

            center = c.get("center_point", {})
            cx = int(center.get("x", bx + bw // 2))
            cy = int(center.get("y", by + bh // 2))
            cv2.circle(img, (cx, cy), 5 if is_selected else 4, (0, 0, 255), -1)
            if is_selected:
                cv2.circle(img, (cx, cy), 10, (0, 0, 255), 1)

            score = float(c.get("confidence_score", 0.0))
            ocr_text = c.get("semantic_text") or ""
            prefix = f"SELECTED #{idx}" if is_selected else f"#{idx}"
            label = f"{prefix} [{score:.2f}] {ocr_text}".strip()

            (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            badge_y = max(by - 5, label_h + 5)
            cv2.rectangle(img, (bx, badge_y - label_h - 4), (bx + label_w + 6, badge_y + 2), box_color, -1)
            cv2.putText(img, label, (bx + 3, badge_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

    cv2.imwrite(output_path, img)


def render_scene_audit(
    image_path: str,
    annotations: List[Dict[str, Any]],
    output_path: str,
    step_title: Optional[str] = None,
) -> None:
    """
    Render a multi-component visual audit image for Full-Vision E2E flows.

    Each item in `annotations` is a dict with:
      - candidate: ElementCandidate dict ({bbox, center_point, confidence_score, semantic_text, meta})
      - role: 'click' | 'assert_visual' | 'assert_ocr'
      - label: human-readable label (e.g. 'Product Card', 'Cart=0', 'Add to Cart')
      - dom_bbox: optional DOM ground-truth bbox {x, y, width, height}
    """
    img = cv2.imread(image_path)
    if img is None:
        return

    if step_title:
        cv2.rectangle(img, (0, 0), (img.shape[1], 32), (15, 23, 42), -1)
        cv2.putText(
            img,
            step_title,
            (14, 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

    role_colors = {
        "click": (0, 220, 0),            # Bright Green (BGR)
        "assert_visual": (255, 140, 0),  # Deep Sky Blue (BGR)
        "assert_ocr": (200, 0, 200),     # Magenta / Purple (BGR)
        "assert_ocr_warn": (0, 140, 255),# Amber / Orange (BGR)
    }

    for item in annotations:
        cand = item.get("candidate") or {}
        role = item.get("role", "assert_visual")
        custom_label = item.get("label", "UI Element")
        dom_bbox = item.get("dom_bbox")

        if dom_bbox:
            dx = int(dom_bbox.get("x", 0))
            dy = int(dom_bbox.get("y", 0))
            dw = int(dom_bbox.get("width", 0))
            dh = int(dom_bbox.get("height", 0))
            cv2.rectangle(img, (dx, dy), (dx + dw, dy + dh), (255, 255, 0), 1)

        bbox = cand.get("bbox", {})
        if not bbox:
            continue

        bx = int(bbox.get("x", 0))
        by = int(bbox.get("y", 0))
        bw = int(bbox.get("width", 0))
        bh = int(bbox.get("height", 0))

        color = role_colors.get(role, (0, 200, 255))
        thickness = 3 if role == "click" else 2
        cv2.rectangle(img, (bx, by), (bx + bw, by + bh), color, thickness)

        center = cand.get("center_point", {})
        cx = int(center.get("x", bx + bw // 2))
        cy = int(center.get("y", by + bh // 2))

        if role == "click":
            cv2.circle(img, (cx, cy), 5, (0, 0, 255), -1)
            cv2.circle(img, (cx, cy), 11, (0, 0, 255), 2)

        score = float(cand.get("confidence_score", 0.0))
        ocr_text = cand.get("semantic_text")
        if role == "assert_ocr" and ocr_text is not None:
            badge_text = f"OCR OK [{custom_label}]: '{ocr_text}' ({score:.2f})"
        elif role == "assert_ocr_warn":
            badge_text = f"OCR WARN [{custom_label}]: '{ocr_text or ''}' ({score:.2f})"
        elif role == "click":
            badge_text = f"CLICK [{custom_label}] ({score:.2f})"
        else:
            badge_text = f"VISUAL OK [{custom_label}] ({score:.2f})"

        (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        by_text = max(by - 6, th + 38)
        cv2.rectangle(img, (bx, by_text - th - 5), (bx + tw + 8, by_text + 3), color, -1)
        cv2.putText(
            img,
            badge_text,
            (bx + 4, by_text - 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255) if role != "click" else (0, 0, 0),
            1,
            cv2.LINE_AA,
        )

    cv2.imwrite(output_path, img)


def publish_step_audit(
    step_id: str,
    raw_image_path: str,
    annotations: List[Dict[str, Any]],
    step_title: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Render a multi-annotation step audit image, copy it into
    reports/<strategy>/<frontend>/vision_audit/, save its JSON metadata,
    and emit [[ATTACHMENT|...]] for Jenkins JUnit Attachments.
    """
    base_report_dir = telemetry.telemetry_dir or (
        PLAYWRIGHT_ROOT / "reports" / telemetry.strategy / telemetry.frontend
    )
    vision_audit_dir = Path(base_report_dir) / "vision_audit"
    vision_audit_dir.mkdir(parents=True, exist_ok=True)

    prefix = f"r{telemetry.repeat_idx}_{step_id}"
    dest_annotated = vision_audit_dir / f"{prefix}_annotated.png"
    dest_meta = vision_audit_dir / f"{prefix}_audit.json"

    render_scene_audit(
        image_path=raw_image_path,
        annotations=annotations,
        output_path=str(dest_annotated),
        step_title=step_title,
    )

    payload = {
        "timestamp": datetime.now().isoformat(),
        "step_id": step_id,
        "step_title": step_title,
        "strategy": telemetry.strategy,
        "frontend": telemetry.frontend,
        "repeat_idx": telemetry.repeat_idx,
        "annotated_image": dest_annotated.name,
        "annotations": annotations,
        "metadata": metadata or {},
    }
    with open(dest_meta, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    flat_screenshots_dir = PLAYWRIGHT_ROOT / "reports" / "screenshots"
    flat_screenshots_dir.mkdir(parents=True, exist_ok=True)
    flat_copy = flat_screenshots_dir / f"full_vision_{telemetry.frontend}_{step_id}.png"
    shutil.copy2(str(dest_annotated), str(flat_copy))

    print(f"\n[[ATTACHMENT|{dest_annotated.resolve()}]]")
    return str(dest_annotated)


def record_playwright_action(
    audit_dir: Optional[str],
    candidate: Optional[Dict[str, Any]],
    action: str = "click",
    index: int = 0,
    status: str = "success",
    error: Optional[str] = None,
    dom_bbox: Optional[Dict[str, float]] = None,
    dom_ground_truth_hit: Optional[bool] = None,
) -> Optional[str]:
    """
    Save the final decision and action taken by Playwright into final_selection.json,
    re-render the annotated image highlighting the selected index and DOM ground truth,
    and publish the annotated image to the Jenkins report directory + JUnit Attachments.
    """
    if not audit_dir or not os.path.exists(audit_dir):
        return None

    action_data = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "selected_index": index,
        "status": status,
        "click_coordinates": candidate.get("center_point") if candidate else None,
        "dom_ground_truth_hit": dom_ground_truth_hit,
        "dom_bbox": dom_bbox,
        "selected_candidate": candidate,
        "error": error
    }
    action_file = os.path.join(audit_dir, "final_selection.json")
    with open(action_file, "w", encoding="utf-8") as f:
        json.dump(action_data, f, indent=2, ensure_ascii=False)
    print(f"Action saved: {action_file}")

    raw_screenshot = os.path.join(audit_dir, "screenshot.png")
    response_file = os.path.join(audit_dir, "response.json")
    annotated_path = os.path.join(audit_dir, "annotated_screenshot.png")
    if os.path.exists(raw_screenshot) and os.path.exists(response_file):
        try:
            with open(response_file, "r", encoding="utf-8") as rf:
                resp_data = json.load(rf)
            render_annotated_detection(
                raw_screenshot,
                resp_data.get("candidates", []),
                annotated_path,
                selected_index=index if status == "success" else None,
                dom_bbox=dom_bbox,
            )
        except Exception as e:
            print(f"[WARN] Could not re-render annotated detection: {e}")

    try:
        base_report_dir = telemetry.telemetry_dir or (
            PLAYWRIGHT_ROOT / "reports" / telemetry.strategy / telemetry.frontend
        )
        vision_audit_dir = Path(base_report_dir) / "vision_audit"
        vision_audit_dir.mkdir(parents=True, exist_ok=True)

        prefix = f"r{telemetry.repeat_idx}_add_to_cart"
        dest_annotated = vision_audit_dir / f"{prefix}_annotated.png"
        dest_raw = vision_audit_dir / f"{prefix}_raw.png"
        dest_response = vision_audit_dir / f"{prefix}_response.json"
        dest_selection = vision_audit_dir / f"{prefix}_selection.json"

        if os.path.exists(annotated_path):
            shutil.copy2(annotated_path, dest_annotated)
            print(f"\n[[ATTACHMENT|{dest_annotated.resolve()}]]")
        if os.path.exists(raw_screenshot):
            shutil.copy2(raw_screenshot, dest_raw)
        if os.path.exists(response_file):
            shutil.copy2(response_file, dest_response)
        if os.path.exists(action_file):
            shutil.copy2(action_file, dest_selection)
    except Exception as e:
        print(f"[WARN] Could not copy vision audit files to reports/: {e}")

    return action_file


def detect_for_openvisor(
        page: Page,
        target_description: Optional[str] = None,
        element_type: Optional[str] = None,
        synonyms: Optional[List[str]] = None,
        strategies: Optional[List[str]] = None,
        enable_ocr: bool = True,
        visual_threshold: Optional[float] = None,
        full_page: bool = False,
        identifier: str = "vision",
        existing_screenshot_path: Optional[str] = None,
    ) -> Dict[str, Any]:
    """
    Capture the viewport (or reuse `existing_screenshot_path` to avoid redundant captures),
    send detection request to vision-service, render annotated detections and return result.
    """
    page.wait_for_load_state("load")

    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    results_root = PLAYWRIGHT_ROOT / "test-results"
    audit_dir = results_root / f"{identifier}_{timestamp}"
    audit_dir.mkdir(parents=True, exist_ok=True)

    screenshot_path = os.path.join(audit_dir, "screenshot.png")
    if existing_screenshot_path and os.path.exists(existing_screenshot_path):
        shutil.copy2(existing_screenshot_path, screenshot_path)
        capture_ms = 0.0
    else:
        t_cap_start = time.perf_counter()
        page.screenshot(
            path=screenshot_path,
            full_page=full_page,
            animations="disabled"
        )
        capture_ms = (time.perf_counter() - t_cap_start) * 1000.0
        print(f"Audit screenshot saved (full_page={full_page}): {screenshot_path}")

    api_url = os.getenv("VISION_API_URL", "http://localhost:8001/api/vision/detect")
    if not api_url.endswith("/detect"):
        api_url = api_url.rstrip("/") + "/detect"

    request_data = {
        "timestamp": datetime.now().isoformat(),
        "api_url": api_url,
        "params": {
            "target_description": target_description if enable_ocr else None,
            "element_type": element_type if enable_ocr else None,
            "synonyms": synonyms if enable_ocr else None,
            "strategies": strategies,
            "enable_ocr": enable_ocr,
            "visual_threshold": visual_threshold,
            "full_page": full_page,
            "reused_screenshot": bool(existing_screenshot_path),
        },
        "screenshot_file": "screenshot.png"
    }
    request_file = os.path.join(audit_dir, "request.json")
    with open(request_file, "w", encoding="utf-8") as f:
        json.dump(request_data, f, indent=2, ensure_ascii=False)

    t_req_start = time.perf_counter()
    result = request_api_vision_detection(
        screenshot_path,
        target_description=target_description,
        element_type=element_type,
        synonyms=synonyms,
        strategies=strategies,
        enable_ocr=enable_ocr,
        visual_threshold=visual_threshold,
        api_url=api_url
    )
    http_roundtrip_ms = (time.perf_counter() - t_req_start) * 1000.0
    server_total_ms = float((result.get("timings_ms") or {}).get("total_server_ms", 0.0))
    network_ms = max(0.0, http_roundtrip_ms - server_total_ms)
    result["client_timings_ms"] = {
        "capture_ms": round(capture_ms, 2),
        "http_roundtrip_ms": round(http_roundtrip_ms, 2),
        "network_ms": round(network_ms, 2),
        "reused_screenshot": bool(existing_screenshot_path),
    }

    response_file = os.path.join(audit_dir, "response.json")
    with open(response_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    annotated_path = os.path.join(audit_dir, "annotated_screenshot.png")
    render_annotated_detection(screenshot_path, result.get("candidates", []), annotated_path)

    result["audit_dir"] = audit_dir
    result["screenshot_path"] = screenshot_path
    return result


def get_detected_text(result: Dict[str, Any], index: int = 0) -> str:
    candidates = result.get("candidates", [])
    if candidates and len(candidates) > index:
        return candidates[index].get("semantic_text") or ""
    return ""


def get_ocr_details(result: Dict[str, Any], index: int = 0) -> Dict[str, Any]:
    candidates = result.get("candidates", [])
    if candidates and len(candidates) > index:
        return candidates[index].get("ocr_details") or {}
    return {}


def register_env_templates(
    env: str,
    template_keys: Optional[List[str]] = None,
    clear_first: bool = True,
    api_url: Optional[str] = None,
) -> Dict[str, bool]:
    """
    Selectively register UI templates for a specific frontend environment (`react`, `angular`, `svelte`).

    Args:
        env: Frontend environment name ('react', 'angular', 'svelte')
        template_keys: Optional list of logical keys from ENV_TEMPLATE_CATALOG
                       (e.g. ['nav_products'], ['product_card', 'add_to_cart'], ['nav_cart']).
                       If None, registers all catalog templates for `env`.
        clear_first: Whether to clear previously registered templates in vision-service first
                     so template matching and OCR only evaluate the active target templates.
        api_url: Optional custom API URL.

    Returns:
        Dict mapping registered template_id -> bool success
    """
    if api_url is None:
        api_url = os.getenv("VISION_API_URL", "http://localhost:8001/api/vision/detect")

    if clear_first:
        clear_templates_from_api(api_url=api_url)

    base_url = api_url.rstrip("/").replace("/detect", "")
    register_url = f"{base_url}/templates/register"

    env_dir = PLAYWRIGHT_ROOT / "templates" / env
    keys_to_load = template_keys or list(ENV_TEMPLATE_CATALOG.keys())
    results: Dict[str, bool] = {}

    for key in keys_to_load:
        rel_file = ENV_TEMPLATE_CATALOG.get(key, key)
        template_path = env_dir / rel_file
        template_id = f"{env}_{key}"

        if not template_path.exists():
            print(f"[WARN] Template file not found for {template_id}: {template_path}")
            results[template_id] = False
            continue

        try:
            with open(template_path, "rb") as f:
                response = requests.post(
                    register_url,
                    files={"file": f},
                    params={"template_name": template_id},
                    timeout=10,
                )
                response.raise_for_status()
                results[template_id] = True
                print(f"[OK] Registered env template: {template_id} ({rel_file})")

            # When registering product_title or cart_item_title, also register tight-cropped typography variants
            # (1.0x, 0.95x, 0.86x) so the title matches both catalog cards (h3) and /cart rows (1rem)
            if key in ("product_title", "cart_item_title"):
                img = cv2.imread(str(template_path))
                if img is not None:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    ys, xs = np.where(gray < 220)
                    if len(ys) > 0 and len(xs) > 0:
                        tight = img[
                            max(0, int(ys.min()) - 4) : min(img.shape[0], int(ys.max()) + 5),
                            max(0, int(xs.min()) - 4) : min(img.shape[1], int(xs.max()) + 5),
                        ]
                        for scale in (1.0, 0.95, 0.86):
                            sw = max(12, int(round(tight.shape[1] * scale)))
                            sh = max(10, int(round(tight.shape[0] * scale)))
                            scaled = cv2.resize(tight, (sw, sh))
                            ok, buf = cv2.imencode(".png", scaled)
                            if ok:
                                scale_id = f"{template_id}_s{int(scale * 100)}"
                                requests.post(
                                    register_url,
                                    files={"file": (f"{scale_id}.png", buf.tobytes(), "image/png")},
                                    params={"template_name": scale_id},
                                    timeout=10,
                                )
        except Exception as e:
            print(f"[ERROR] Failed to register env template {template_id}: {e}")
            results[template_id] = False

    return results


def register_templates_for_api(api_url: Optional[str] = None, templates_dir: Optional[Path] = None) -> Dict[str, bool]:
    if api_url is None:
        api_url = os.getenv("VISION_API_URL", "http://localhost:8001/api/vision/detect")

    base_url = api_url.rstrip("/").replace("/detect", "")
    register_url = f"{base_url}/templates/register"

    if templates_dir is None:
        templates_dir = PLAYWRIGHT_ROOT / "templates"

    results = {}

    if not templates_dir.exists():
        print(f"[WARN] Templates directory not found: {templates_dir}")
        return results

    for template_path in sorted(templates_dir.glob("*.png")):
        template_name = template_path.stem

        try:
            with open(template_path, "rb") as f:
                files = {"file": f}
                params = {"template_name": template_name}

                response = requests.post(register_url, files=files, params=params)
                response.raise_for_status()

                results[template_name] = True
                print(f"[OK] Registered template: {template_name}")

        except requests.exceptions.ConnectionError:
            print(f"[ERROR] Cannot connect to Vision API at {register_url}")
            results[template_name] = False
        except Exception as e:
            print(f"[ERROR] Failed to register {template_name}: {e}")
            results[template_name] = False

    print(f"\nTemplates registered: {sum(results.values())}/{len(results)}")
    return results


def clear_templates_from_api(api_url: Optional[str] = None) -> bool:
    if api_url is None:
        api_url = os.getenv("VISION_API_URL", "http://localhost:8001/api/vision/detect")

    base_url = api_url.rstrip("/").replace("/detect", "")
    clear_url = f"{base_url}/templates/clear"

    try:
        response = requests.post(clear_url)
        response.raise_for_status()
        result = response.json()
        print(f"[OK] Cleared {result.get('templates_cleared', 0)} templates")
        return True

    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Cannot connect to Vision API at {clear_url}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to clear templates: {e}")
        return False
