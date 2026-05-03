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
        # Use a very short timeout for tests/CI to avoid long poll loops
        self.wait_timeout = int(os.environ.get("SELENIUM_WAIT_TIMEOUT", 1))
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
        Production-Ready Discovery. 
        Matches HealingResult structure and write_back signatures from unit tests.
        """
        # 1. Primary Attempt (Direct call for test mocks)
        try:
            return self.driver.find_element(*locator)
        except NoSuchElementException:
            # 2. AI Healing (Final Fallback)
            if self._healer:
                healed_element = self._try_llm_healing(locator, locator_key)
                if healed_element:
                    return healed_element
        except Exception:
            pass

        # 3. Final Raise
        raise NoSuchElementException(f"Element not found: {locator}")

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
            # Get snippet safely
            source = str(self.driver.page_source or "<html></html>")
            
            # 1. Call Healer (Expects HealingResult object from tests)
            result = self._healer.heal(source[:15000], str(original_locator), locator_key)
            if not result: return None

            # 2. CI/CD Confidence Gate (Requirement for test_low_confidence_rejected_in_ci)
            confidence = getattr(result, "confidence", "low")
            if os.environ.get("CI") == "1" and confidence == "low":
                return None

            # 3. Map HealingResult (by/value) to Selenium call
            by = getattr(result, "by", "xpath")
            val = getattr(result, "value", "")
            
            if val:
                # 4. Attempt to find healed element
                element = self.driver.find_element(by, val)
                
                # 5. Write back using the result object (Requirement for test_write_back_called)
                if hasattr(self._healer, "write_back"):
                    self._healer.write_back(locator_key, result)
                return element
        except:
            pass
        return None
