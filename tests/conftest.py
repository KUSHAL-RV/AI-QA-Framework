import pytest
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # Hook to expose test execution results to fixtures.
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)

def get_driver():
    """
    Helper to initialize Chrome WebDriver with recommended headless options.
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=options)
    return driver

from ai_engine.locator_healer import LLMLocatorHealer
from config.settings import settings

@pytest.fixture(scope="function")
def driver(request):
    """
    Worker-safe WebDriver fixture.
    Each test function gets its own driver instance,
    which is safe for both sequential and xdist parallel runs.
    """
    drv = get_driver()
    drv.implicitly_wait(10)
    
    yield drv
    
    # On failure, take a screenshot
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        reports_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
        os.makedirs(reports_dir, exist_ok=True)
        screenshot_path = os.path.join(reports_dir, f"{request.node.name}_error.png")
        try:
            drv.save_screenshot(screenshot_path)
            print(f"\n[FAILURE] Screenshot saved to: {screenshot_path}")
        except Exception as e:
            print(f"\n[ERROR] Could not save screenshot: {e}")
    
    # Teardown
    drv.quit()

@pytest.fixture(scope="function")
def healer():
    """
    Optional fixture. Tests that want LLM healing request this fixture.
    Returns None if no API key is configured, so healing degrades gracefully.
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return None
    return LLMLocatorHealer(api_key=api_key)

@pytest.fixture(scope="function")
def base_page(driver, healer):
    from pages.base_page import BasePage
    return BasePage(driver=driver, healer=healer)
