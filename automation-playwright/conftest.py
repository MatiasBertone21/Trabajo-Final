import pytest
import os
from dotenv import load_dotenv
import pytest_html
load_dotenv()

ENV_URLS = {
    "react":    os.getenv("REACT_URL", "http://localhost:3000"),
    "angular":  os.getenv("ANGULAR_URL", "http://localhost:4200"),
    "svelte":   os.getenv("SVELTE_URL", "http://localhost:5173"),
}

USER_EMAIL = os.getenv("USER_EMAIL")
USER_PASSWORD = os.getenv("USER_PASSWORD")


def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default="react",
        choices=["react", "angular", "svelte"],
        help="Frontend to test: react | angular | svelte",
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


#@pytest.fixture
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
    
    if report.when == "call" and report.failed:
        page = item.funcargs.get("page", None)
        if page:
            screenshot_bytes = page.screenshot(full_page=True)
            if hasattr(report, "extra"):
                report.extra.append(pytest_html.extras.image(screenshot_bytes))
            else:
                report.extra = [pytest_html.extras.image(screenshot_bytes)]
