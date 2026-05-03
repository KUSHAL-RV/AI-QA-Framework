import logging
import os
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from utils.resilience import ResilienceEngine

logger = logging.getLogger(__name__)

class BasePage:
    def __init__(self, driver, healer=None):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)
        self._healer = healer

    def handle_modals(self):
        """Detects and attempts to handle/close blocking modals or overlays."""
        # Common close button patterns
        close_patterns = [
            "//button[contains(@class, 'close')]",
            "//*[contains(@class, 'modal')]//button",
            "//div[contains(@class, 'overlay')]"
        ]
        
        for pattern in close_patterns:
            try:
                # Use a short wait to not slow down the test
                close_btn = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, pattern))
                )
                close_btn.click()
                print(f"  Closed detected modal/overlay: {pattern}")
                time.sleep(1)
            except:
                continue

    @ResilienceEngine.retry_on_failure(max_retries=3)
    def open_url(self, url):
        logger.info(f"Opening URL: {url}")
        self.driver.get(url)

    def wait_for_page_load(self, timeout=30):
        WebDriverWait(self.driver, timeout).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )

    @ResilienceEngine.retry_on_failure(max_retries=2)
    def find_element(self, locator, locator_key: str = ""):
        # Before finding, check if a modal is blocking
        # but only if we've failed once already
        try:
            return self.wait.until(EC.visibility_of_element_located(locator))
        except:
            print(f"  Element {locator_key} not visible. Checking for blocking modals...")
            self.handle_modals()
            return self.wait.until(EC.visibility_of_element_located(locator))
