import json
import os
import logging
from typing import Optional
from pathlib import Path
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from ai_engine.locator_healer import LLMLocatorHealer

# Configure basic logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

FALLBACK_PATH = Path("locators/fallback_locators.json")

# Descriptions used as LLM context — extend as you add page objects
ELEMENT_DESCRIPTIONS: dict[str, str] = {
    "login_button":       "Primary login/submit button on the login form",
    "username_field":     "Username or email text input on the login form",
    "password_field":     "Password input field on the login form",
    "search_box":         "Main site search input field",
    "add_to_cart_button": "Add to cart CTA button on a product page",
    "checkout_button":    "Proceed to checkout button in cart/basket",
    # Add new entries here as page objects grow
}

class BasePage:
    """
    The BasePage class holds all common WebDriver methods.
    Other page object classes will inherit from this base class.
    """
    def __init__(self, driver: WebDriver, healer: Optional[LLMLocatorHealer] = None):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)  # Explicit wait of 10 seconds
        self._healer = healer  # injected; None disables LLM healing
        self._fallbacks = self._load_fallbacks()

    def open_url(self, url):
        self.driver.get(url)
        logger.info(f"Opened URL: {url}")

    def find_element(self, locator, locator_key: str = ""):
        """
        Finds an element using explicit wait.
        Three-layer element resolution:
          1. Primary locator (as passed)
          2. Static fallbacks from fallback_locators.json
          3. LLM healing via Gemini (if healer is configured)
        """
        logger.info(f"Finding element: {locator}")
        
        # --- Layer 1: primary ---
        try:
            return self.wait.until(EC.visibility_of_element_located(locator))
        except (TimeoutException, NoSuchElementException):
            logger.warning(f"Primary locator failed: {locator}. Attempting fallbacks...")

        # --- Layer 2: static fallbacks ---
        # Generate locator_key from tuple if not provided
        if not locator_key:
            locator_key = f"{locator[0]}|{locator[1]}"
            
        element = self._try_static_fallbacks(locator_key)
        if element:
            return element

        # --- Layer 3: LLM healing ---
        if self._healer:
            element = self._try_llm_healing(locator_key)
            if element:
                return element

        raise NoSuchElementException(
            f"All healing strategies exhausted for locator_key='{locator_key}', "
            f"original: {locator}"
        )

    def _try_static_fallbacks(self, locator_key: str) -> Optional[WebElement]:
        fallbacks = self._fallbacks.get(locator_key, [])
        by_map = {
            "id":    By.ID,
            "xpath": By.XPATH,
            "css selector":   By.CSS_SELECTOR,
            "name":  By.NAME,
            "class name": By.CLASS_NAME
        }
        for strategy, value in fallbacks:
            logger.info(f"Trying static fallback: {strategy}='{value}'")
            try:
                # using shorter wait time for fallbacks (3 secs)
                short_wait = WebDriverWait(self.driver, 3)
                element = short_wait.until(EC.visibility_of_element_located((by_map.get(strategy, strategy), value)))
                logger.info(f"SUCCESS: Static fallback succeeded for '{locator_key}'")
                return element
            except (TimeoutException, NoSuchElementException):
                continue
        logger.warning(f"All static fallbacks exhausted for '{locator_key}'")
        return None

    def _try_llm_healing(self, locator_key: str) -> Optional[WebElement]:
        description = ELEMENT_DESCRIPTIONS.get(
            locator_key, f"Element identified by key '{locator_key}'"
        )
        logger.info(f"Attempting LLM healing for '{locator_key}'...")
        result = self._healer.heal(
            driver=self.driver,
            locator_key=locator_key,
            element_description=description,
        )
        if not result:
            return None

        import os
        if result.confidence == "low" and os.getenv("CI"):
            logger.warning(
                f"Rejecting low-confidence LLM suggestion for '{locator_key}' in CI environment."
            )
            return None

        try:
            selenium_by, value = result.to_selenium_args()
            # using shorter wait time for LLM suggestion (5 secs)
            short_wait = WebDriverWait(self.driver, 5)
            element = short_wait.until(EC.visibility_of_element_located((selenium_by, value)))
            # Write back so next run skips the LLM call
            self._healer.write_back(locator_key, result)
            return element
        except (TimeoutException, NoSuchElementException):
            logger.warning(
                f"LLM suggestion did not resolve: {result.by}='{result.value}'"
            )
            return None

    def _load_fallbacks(self) -> dict:
        if FALLBACK_PATH.exists():
            try:
                with open(FALLBACK_PATH) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Could not load fallback locators: {e}")
        return {}

    def click_element(self, locator, locator_key: str = ""):
        element = self.find_element(locator, locator_key)
        element.click()
        logger.info(f"Clicked on element: {locator}")

    def enter_text(self, locator, text, locator_key: str = ""):
        element = self.find_element(locator, locator_key)
        element.clear()
        element.send_keys(text)
        logger.info(f"Entered text '{text}' into element: {locator}")

    def get_element_text(self, locator, locator_key: str = ""):
        element = self.find_element(locator, locator_key)
        text = element.text
        logger.info(f"Got text '{text}' from element: {locator}")
        return text
    def assert_visual_match(self, test_name: str, threshold: float = 0.01):
        """
        Captures a screenshot and compares it with the baseline.
        Throws AssertionError if match exceeds threshold.
        """
        from utils.visual_comparator import VisualComparator
        
        latest_dir = VisualComparator.LATEST_DIR
        os.makedirs(latest_dir, exist_ok=True)
        screenshot_path = os.path.join(latest_dir, f"{test_name}.png")
        
        self.driver.save_screenshot(screenshot_path)
        logger.info(f"Captured visual snapshot: {screenshot_path}")
        
        # Adjust threshold slightly for CI due to font/anti-aliasing differences
        actual_threshold = threshold * 2 if os.getenv("CI") else threshold
        is_match = VisualComparator.compare(test_name, actual_threshold)
        if not is_match:
            diff_path = os.path.join(VisualComparator.DIFF_DIR, f"{test_name}_diff.png")
            raise AssertionError(f"Visual mismatch detected for {test_name}! Diff saved to {diff_path}")
        
        logger.info(f"Visual match confirmed for {test_name}")
