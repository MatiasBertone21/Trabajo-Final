"""
E2E Integration test for vision-service API:
Validates template registration, template clearing, and element detection.
Logs each HTTP request/response to console (-s) and persists logs to reports/test_runs/.
"""
import json
from datetime import datetime
from pathlib import Path
import requests

TESTS_DIR = Path(__file__).resolve().parent
ASSETS_DIR = TESTS_DIR / "assets"
TEMPLATE_PATH = ASSETS_DIR / "templates" / "add_to_cart.png"
SCREENSHOT_PATH = ASSETS_DIR / "datasets" / "home_page-react.png"
REPORTS_DIR = TESTS_DIR.parent / "reports" / "test_runs"


def _log_and_record(lines: list, message: str) -> None:
    """Print to console and append to log buffer."""
    print(message)
    lines.append(message)


def test_api_template_lifecycle_and_detection(api_base_url: str):
    """
    Test full template lifecycle:
    1. Clear templates
    2. Register 'add_to_cart' template
    3. Detect button on screenshot
    4. Validate at least one high-confidence match with matching template_id
    5. Clean up templates
    """
    log_buffer = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _log_and_record(log_buffer, f"\n{'='*70}")
    _log_and_record(log_buffer, f"API TEMPLATE E2E TEST - EXECUTION LOG [{timestamp}]")
    _log_and_record(log_buffer, f"{'='*70}")

    # 1. Clear previous templates
    _log_and_record(log_buffer, f"\n[STEP 1] POST {api_base_url}/templates/clear")
    clear_resp = requests.post(f"{api_base_url}/templates/clear", timeout=10)
    _log_and_record(log_buffer, f"Status: {clear_resp.status_code}")
    _log_and_record(log_buffer, f"Response: {json.dumps(clear_resp.json(), indent=2)}")
    assert clear_resp.status_code == 200, f"Failed to clear templates: {clear_resp.text}"

    # 2. Register 'add_to_cart' template
    _log_and_record(log_buffer, f"\n[STEP 2] POST {api_base_url}/templates/register (template_name='add_to_cart')")
    assert TEMPLATE_PATH.exists(), f"Template image not found: {TEMPLATE_PATH}"
    with open(TEMPLATE_PATH, "rb") as f:
        reg_resp = requests.post(
            f"{api_base_url}/templates/register",
            params={"template_name": "add_to_cart"},
            files={"file": ("add_to_cart.png", f, "image/png")},
            timeout=10,
        )
    _log_and_record(log_buffer, f"Status: {reg_resp.status_code}")
    _log_and_record(log_buffer, f"Response: {json.dumps(reg_resp.json(), indent=2)}")
    assert reg_resp.status_code == 200, f"Failed to register template: {reg_resp.text}"
    reg_data = reg_resp.json()
    assert reg_data.get("status") == "registered"
    assert reg_data.get("template_name") == "add_to_cart"

    # 3. Detect elements on screenshot
    _log_and_record(log_buffer, f"\n[STEP 3] POST {api_base_url}/detect (image='home_page-react.png')")
    assert SCREENSHOT_PATH.exists(), f"Screenshot not found: {SCREENSHOT_PATH}"
    with open(SCREENSHOT_PATH, "rb") as f:
        detect_resp = requests.post(
            f"{api_base_url}/detect",
            files={"file": ("home_page-react.png", f, "image/png")},
            timeout=30,
        )
    _log_and_record(log_buffer, f"Status: {detect_resp.status_code}")
    detect_data = detect_resp.json()
    _log_and_record(log_buffer, f"Response Status: {detect_data.get('status')}")
    _log_and_record(log_buffer, f"Candidates Found: {detect_data.get('candidates_count')}")
    assert detect_resp.status_code == 200, f"Detection failed: {detect_resp.text}"
    assert detect_data.get("status") == "success"

    # 4. Verify candidates found via template
    candidates = detect_data.get("candidates", [])
    assert len(candidates) > 0, "No candidates found on screen"

    template_candidates = [
        c for c in candidates
        if c.get("source_strategy") == "template" or c.get("meta", {}).get("template_id") == "add_to_cart"
    ]
    _log_and_record(log_buffer, f"Template Candidates Matched: {len(template_candidates)}")
    for idx, c in enumerate(template_candidates, 1):
        _log_and_record(log_buffer, f"  Candidate [{idx}]:")
        _log_and_record(log_buffer, f"    Template ID: {c.get('meta', {}).get('template_id')}")
        _log_and_record(log_buffer, f"    Confidence:  {c.get('confidence_score')}")
        _log_and_record(log_buffer, f"    BBox:        {c.get('bbox')}")
        _log_and_record(log_buffer, f"    Center:      {c.get('center_point')}")
        _log_and_record(log_buffer, f"    OCR Text:    {c.get('semantic_text')}")

    assert len(template_candidates) > 0, "Should detect button via template strategy"
    best_candidate = max(template_candidates, key=lambda c: c["confidence_score"])
    assert best_candidate.get("meta", {}).get("template_id") == "add_to_cart", "Expected template_id 'add_to_cart' in meta"
    assert best_candidate["confidence_score"] >= 0.5, "Confidence score too low"
    assert "bbox" in best_candidate
    assert "center_point" in best_candidate

    # 5. Clean up templates
    _log_and_record(log_buffer, f"\n[STEP 4] POST {api_base_url}/templates/clear (cleanup)")
    clear_resp = requests.post(f"{api_base_url}/templates/clear", timeout=10)
    _log_and_record(log_buffer, f"Status: {clear_resp.status_code}")
    _log_and_record(log_buffer, f"Response: {json.dumps(clear_resp.json(), indent=2)}")
    assert clear_resp.status_code == 200

    _log_and_record(log_buffer, f"\n{'='*70}")
    _log_and_record(log_buffer, "ALL ASSERTIONS PASSED SUCCESSFULLY")
    _log_and_record(log_buffer, f"{'='*70}\n")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = REPORTS_DIR / "api_templates_e2e.log"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("\n".join(log_buffer))
    print(f"Log persisted to: {log_file}")
