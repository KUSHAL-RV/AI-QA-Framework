import pytest
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from ai_engine.locator_healer import LLMLocatorHealer
from config.settings import settings

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)

def get_driver():
    options = Options()
    if os.getenv("CI") == "true":
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)

@pytest.fixture(scope="function")
def driver(request):
    drv = get_driver()
    drv.implicitly_wait(10)
    
    yield drv
    
    # After the test finishes, capture a screenshot, DOM, and logs
    reports_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    screenshot_path = os.path.join(reports_dir, f"{request.node.name}.png")
    
    try:
        drv.save_screenshot(screenshot_path)
        
        # Capture DOM Source
        dom_path = os.path.join(reports_dir, f"{request.node.name}_dom.html")
        with open(dom_path, "w", encoding="utf-8") as f:
            f.write(drv.page_source)
            
        # Capture Browser Logs
        logs = drv.get_log("browser")
        
        # Embed in pytest-html report
        if hasattr(request.node, "extra"):
            from pytest_html import extras
            request.node.extra.append(extras.image(screenshot_path))
            request.node.extra.append(extras.text(f"DOM Path: {dom_path}", name="DOM Source"))
            request.node.extra.append(extras.text("\n".join([str(log) for log in logs]), name="Console Logs"))
    except Exception:
        pass
        
    drv.quit()

@pytest.fixture(scope="function")
def healer():
    api_key = settings.GROQ_API_KEY
    if not api_key:
        return None
    return LLMLocatorHealer(api_key=api_key)

@pytest.fixture(scope="function")
def base_page(driver, healer):
    from pages.base_page import BasePage
    return BasePage(driver=driver, healer=healer)
