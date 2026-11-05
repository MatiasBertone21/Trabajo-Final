import os
import re
from pathlib import Path
from dotenv import load_dotenv
import pytest
import requests
from utils.openvisor_helper import register_templates_for_api, clear_templates_from_api
from utils.telemetry import telemetry

# Load .env from automation-playwright root directory
PLAYWRIGHT_ROOT = Path(__file__).resolve().parent
env_file = PLAYWRIGHT_ROOT / ".env"
load_dotenv(env_file)

ENV_URLS = {
    "react":   os.getenv("REACT_URL", "http://localhost:3000"),
    "angular": os.getenv("ANGULAR_URL", "http://localhost:4200"),
    "svelte":  os.getenv("SVELTE_URL", "http://localhost:5173"),
}

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
USER_EMAIL = os.getenv("USER_EMAIL")
USER_PASSWORD = os.getenv("USER_PASSWORD")

KNOWN_STRATEGIES = ("base", "getby", "getby_full", "opencv", "opencv_full", "external")


def _detect_strategy(item) -> str:
    """Resolve the active strategy marker from a pytest item."""
    for marker_name in KNOWN_STRATEGIES:
        if item.get_closest_marker(marker_name) is not None:
            return marker_name
    return "unknown"


@pytest.fixture(scope="session", autouse=True)
def delete_output_dir():
    """
    Override pytest-playwright's default delete_output_dir fixture.
    Prevents deletion of test-results/ folder between runs to maintain execution audit history.
    """
    pass


@pytest.fixture(scope="session", autouse=True)
def setup_vision_templates(request):
    """
    Register vision templates with the API at session start only when running opencv tests.
    Automatically cleans up after all tests complete.
    """
    has_opencv_items = any(
        item.get_closest_marker("opencv") is not None
        for item in request.session.items
    )
    if not has_opencv_items:
        yield
        return

    print("\n Setting up vision templates...")
    try:
        results = register_templates_for_api()
        if not results:
            print(" No templates registered")
    except Exception as e:
        print(f" Failed to register templates: {e}")

    yield

    print("\n Cleaning up vision templates...")
    try:
        clear_templates_from_api()
    except Exception as e:
        print(f" Failed to clear templates: {e}")


def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default="react",
        choices=["react", "angular", "svelte"],
        help="Frontend to test: react | angular | svelte",
    )
    parser.addoption(
        "--telemetry-dir",
        action="store",
        default=None,
        help="Directory where telemetry JSONL files will be written",
    )
    parser.addoption(
        "--repeat-idx",
        action="store",
        default="1",
        help="Repetition index for benchmark runs",
    )
    parser.addoption(
        "--mutation",
        action="store",
        default="M0_CONTROL",
        help="UI mutation identifier for resilience runs",
    )


@pytest.fixture(scope="session")
def env(pytestconfig):
    return pytestconfig.getoption("--env")


@pytest.fixture(scope="session")
def base_url(env):
    return ENV_URLS[env]


@pytest.fixture(scope="session")
def base_selectors(env):
    from utils.selectors import SELECTORS
    return SELECTORS[env]


@pytest.fixture(scope="session")
def getby_selectors(env):
    from utils.selectors_get_by import SELECTORS as SELECTORS_GET_BY
    return SELECTORS_GET_BY[env]


@pytest.fixture(autouse=True)
def configure_test_telemetry(request, env):
    strategy = _detect_strategy(request.node)
    telemetry_dir = request.config.getoption("--telemetry-dir")
    repeat_idx = int(request.config.getoption("--repeat-idx") or 1)
    mutation = request.config.getoption("--mutation") or "M0_CONTROL"
    telemetry.configure(
        strategy=strategy,
        frontend=env,
        mutation=mutation,
        repeat_idx=repeat_idx,
        telemetry_dir=telemetry_dir,
    )
    yield


@pytest.fixture(autouse=True)
def reset_backend_cart(request, env):
    """
    Ensure every local E2E test starts and finishes with a clean cart state in the backend.
    Clears both the frontend-specific scope (react/angular/svelte) and the default scope.
    """
    if request.node.get_closest_marker("external") is not None:
        yield
        return

    def _clear():
        for scope in (env, "default"):
            try:
                requests.delete(
                    f"{BACKEND_API_URL}/cart/",
                    headers={"X-Cart-Scope": scope},
                    timeout=3,
                )
            except requests.RequestException:
                pass

    _clear()
    yield
    _clear()


@pytest.fixture(autouse=True)
def enrich_junit_xml(request, env, record_property, record_xml_attribute):
    """
    Enrich JUnit XML output so Jenkins 'Test Result' groups tests by <strategy>.<frontend>.<module>
    and exposes strategy/frontend metadata properties for auditability.
    """
    strategy = _detect_strategy(request.node)
    module_name = request.node.module.__name__.split(".")[-1]
    record_xml_attribute("classname", f"{strategy}.{env}.{module_name}")
    record_property("strategy", strategy)
    record_property("frontend", env)


def auth_page(page, base_url, selectors):
    from pages.login_page import LoginPage
    login = LoginPage(page, base_url, selectors)
    login.goto()
    login.fill_credentials(USER_EMAIL, USER_PASSWORD)
    login.submit()
    page.wait_for_url(f"{base_url}/", timeout=8000)
    return page


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    telemetry.record_phase(item.nodeid, report.when, report.duration)

    if report.when == "call" and report.failed:
        page = item.funcargs.get("page", None)
        if page:
            strategy = _detect_strategy(item)
            frontend = item.config.getoption("--env", default="react")
            screenshots_dir = PLAYWRIGHT_ROOT / "reports" / strategy / frontend / "screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)

            safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", item.name)
            screenshot_path = screenshots_dir / f"{safe_name}.png"
            try:
                page.screenshot(path=str(screenshot_path), full_page=True)
                rel_path = screenshot_path.relative_to(PLAYWRIGHT_ROOT).as_posix()
                item.user_properties.append(("failure_screenshot", rel_path))
                print(f"\n[Screenshot] Saved failure screenshot to {rel_path}")
            except Exception as e:
                print(f"\n[Screenshot] Could not capture failure screenshot: {e}")

    if report.when == "call":
        item._call_outcome = report.outcome
        strategy = _detect_strategy(item)
        frontend = item.config.getoption("--env", default="react")
        matching_steps = [
            s for s in telemetry.step_records
            if s.get("strategy") == strategy and s.get("frontend") == frontend
        ]
        if matching_steps:
            total_action_ms = round(sum(float(s.get("total_step_ms", 0.0)) for s in matching_steps), 2)
            item.user_properties.append(("action_step_ms", str(total_action_ms)))
            last_step = matching_steps[-1]
            if last_step.get("confidence_score") is not None:
                item.user_properties.append(("confidence_score", str(last_step.get("confidence_score"))))
            if last_step.get("dom_ground_truth_hit") is not None:
                item.user_properties.append(("dom_ground_truth_hit", str(last_step.get("dom_ground_truth_hit"))))
        if strategy == "opencv":
            repeat_idx = int(item.config.getoption("--repeat-idx") or 1)
            rel_audit_img = f"reports/{strategy}/{frontend}/vision_audit/r{repeat_idx}_add_to_cart_annotated.png"
            item.user_properties.append(("vision_annotated_image", rel_audit_img))
        elif strategy == "opencv_full":
            repeat_idx = int(item.config.getoption("--repeat-idx") or 1)
            for idx, sid in enumerate(
                (
                    "step1_nav_products",
                    "step2_products_ui_audit",
                    "step3_cart_incremented",
                    "step4_cart_item_verified",
                    "step5_cart_item_removed",
                ),
                start=1,
            ):
                rel_img = f"reports/{strategy}/{frontend}/vision_audit/r{repeat_idx}_{sid}_annotated.png"
                item.user_properties.append((f"vision_step{idx}_image", rel_img))

    if report.when == "teardown":
        strategy = _detect_strategy(item)
        frontend = item.config.getoption("--env", default="react")
        call_outcome = getattr(item, "_call_outcome", "passed")
        telemetry.finalize_test(
            nodeid=item.nodeid,
            test_name=item.name,
            strategy=strategy,
            frontend=frontend,
            outcome=call_outcome,
        )


def pytest_sessionfinish(session, exitstatus):
    telemetry.flush()
