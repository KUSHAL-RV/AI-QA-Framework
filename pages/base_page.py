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
        self.wait_timeout = int(os.environ.get("SELENIUM_WAIT_TIMEOUT", 10))
        self.wait = WebDriverWait(driver, self.wait_timeout)
        self._healer = healer
        self.visual_engine = VisualEngine()

    def _load_fallbacks(self):
        return {}

    def handle_modals(self):
        close_patterns = [
            "//button[contains(@class, 'close')]",
            "//*[contains(@class, 'modal')]//button",
            "//div[contains(@class, 'overlay')]"
        ]
        for pattern in close_patterns:
            try:
                close_btn = self.driver.find_element(By.XPATH, pattern)
                if close_btn.is_displayed():
                    close_btn.click()
            except:
                continue

    @ResilienceEngine.retry_on_failure(max_retries=3)
    def open_url(self, url):
        self.driver.get(url)

    def wait_for_page_load(self, timeout=30):
        WebDriverWait(self.driver, timeout).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )

    def find_element(self, locator, locator_key: str = ""):
        """
        Final, fail-safe element discovery.
        Optimized for both high-speed production execution and MagicMock unit testing.
        """
        # 1. Fast Path: Try finding it immediately (matches most unit test mocks)
        try:
            return self.driver.find_element(*locator)
        except NoSuchElementException:
            pass

        # 2. Wait Path: Try with explicit wait (for real browsers)
        try:
            return self.wait.until(EC.visibility_of_element_located(locator))
        except (TimeoutException, NoSuchElementException):
            pass

        # 3. Healing Path: Ultimate fallback (for AI-enabled runs)
        if self._healer:
            healed = self._try_llm_healing(locator, locator_key)
            if healed:
                return healed
        
        # 4. Final Failure: Map to standard Selenium exception
        raise NoSuchElementException(f"Element not found after standard discovery and healing: {locator}")

    # --- Standard Utility Methods ---

    def enter_text(self, locator, text, locator_key=""):
        element = self.find_element(locator, locator_key)
        element.clear()
        element.send_keys(text)

    def click(self, locator, locator_key=""):
        element = self.find_element(locator, locator_key)
        element.click()

    def click_element(self, locator, locator_key=""):
        self.click(locator, locator_key)

    def get_element_text(self, locator, locator_key=""):
        element = self.find_element(locator, locator_key)
        return element.text

    def assert_visual_match(self, name, threshold=0.05):
        os.makedirs("screenshots/latest", exist_ok=True)
        os.makedirs("screenshots/baselines", exist_ok=True)
        current_path = f"screenshots/latest/{name}.png"
        baseline_path = f"screenshots/baselines/{name}.png"
        self.driver.save_screenshot(current_path)
        if not os.path.exists(baseline_path):
            self.driver.save_screenshot(baseline_path)
            return True
        success, msg = self.visual_engine.compare_screenshots(baseline_path, current_path, threshold)
        assert success, msg

    def _try_llm_healing(self, original_locator, locator_key):
        if not self._healer: return None
        try:
            snippet = self.driver.page_source[:10000]
            suggestion = self._healer.heal(snippet, str(original_locator), locator_key)
            
            xpath = None
            if isinstance(suggestion, dict) and "xpath" in suggestion:
                xpath = suggestion["xpath"]
            elif suggestion and hasattr(suggestion, "xpath"):
                xpath = getattr(suggestion, "xpath")
                
            if xpath:
                element = self.driver.find_element(By.XPATH, xpath)
                if hasattr(self._healer, "write_back"):
                    self._healer.write_back(locator_key, xpath)
                return element
        except:
            pass
        return None
