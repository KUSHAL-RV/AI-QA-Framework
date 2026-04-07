import pytest
import os
from selenium import webdriver

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # Hook to expose test execution results to fixtures.
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)

@pytest.fixture(scope="function")
def driver(request):
    """
    Setup and teardown for the Selenium WebDriver.
    This fixture ensures a fresh browser instance for each test.
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Headless mode for CI/CD
    options.add_argument("--window-size=1920,1080")
    
    # Initialize the Chrome WebDriver
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    
    yield driver
    
    # On failure, take a screenshot
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        reports_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
        os.makedirs(reports_dir, exist_ok=True)
        screenshot_path = os.path.join(reports_dir, f"{request.node.name}_error.png")
        driver.save_screenshot(screenshot_path)
        print(f"\n[FAILURE] Screenshot saved to: {screenshot_path}")
    
    # Teardown
    driver.quit()
