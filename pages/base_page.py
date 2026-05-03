import logging
import os
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from utils.resilience import ResilienceEngine
from utils.visual_engine import VisualEngine

logger = logging.getLogger(__name__)

class BasePage:
    def __init__(self, driver, healer=None):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)
        self._healer = healer
        self.visual_engine = VisualEngine()

    def _load_fallbacks(self):
        """Restored for backward compatibility with existing tests."""
        return {}

    def handle_modals(self):
        """Detects and attempts to handle/close blocking modals or overlays."""
        close_patterns = [
            "//button[contains(@class, 'close')]",
            "//*[contains(@class, 'modal')]//button",
            "//div[contains(@class, 'overlay')]"
        ]
        for pattern in close_patterns:
            try:
                close_btn = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, pattern))
                )
                close_btn.click()
                time.sleep(1)
            except:
                continue

    @ResilienceEngine.retry_on_failure(max_retries=3)
    def open_url(self, url):
        self.driver.get(url)

    def wait_for_page_load(self, timeout=30):
        WebDriverWait(self.driver, timeout).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )

    @ResilienceEngine.retry_on_failure(max_retries=2)
    def find_element(self, locator, locator_key: str = ""):
        try:
            return self.wait.until(EC.visibility_of_element_located(locator))
        except:
            self.handle_modals()
            if self._healer:
                return self._try_llm_healing(locator, locator_key)
            raise

    # --- Utility Methods for Backward Compatibility ---

    def enter_text(self, locator, text, locator_key=""):
        element = self.find_element(locator, locator_key)
        element.clear()
        element.send_keys(text)

    def click(self, locator, locator_key=""):
        element = self.find_element(locator, locator_key)
        element.click()

    def assert_visual_match(self, name, threshold=0.05):
        """Bridge to the new VisualEngine."""
        os.makedirs("screenshots/latest", exist_ok=True)
        os.makedirs("screenshots/baselines", exist_ok=True)
        
        current_path = f"screenshots/latest/{name}.png"
        baseline_path = f"screenshots/baselines/{name}.png"
        
        self.driver.save_screenshot(current_path)
        
        if not os.path.exists(baseline_path):
            self.driver.save_screenshot(baseline_path)
            logger.info(f"Created visual baseline: {baseline_path}")
            return True
            
        success, msg = self.visual_engine.compare_screenshots(baseline_path, current_path, threshold)
        assert success, msg

    def _try_llm_healing(self, original_locator, locator_key):
        if not self._healer: return None
        snippet = self.driver.page_source[:10000]
        suggestion = self._healer.heal(snippet, str(original_locator), locator_key)
        if suggestion and "xpath" in suggestion:
            try:
                return self.driver.find_element("xpath", suggestion["xpath"])
            except:
                pass
        return None
