import json
import os
import logging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure basic logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class BasePage:
    """
    The BasePage class holds all common WebDriver methods.
    Other page object classes will inherit from this base class.
    """
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)  # Explicit wait of 10 seconds

    def open_url(self, url):
        self.driver.get(url)
        logger.info(f"Opened URL: {url}")

    def find_element(self, locator):
        """
        Finds an element using explicit wait.
        Self-healing logic: If element is not found, attempt fallback locators.
        """
        logger.info(f"Finding element: {locator}")
        try:
            return self.wait.until(EC.visibility_of_element_located(locator))
        except (TimeoutException, NoSuchElementException):
            logger.warning(f"Primary locator failed: {locator}. Attempting self-healing...")
            return self.heal_locator(locator)

    def heal_locator(self, locator):
        """
        Attempts to find alternative locators from JSON.
        """
        locator_key = f"{locator[0]}|{locator[1]}"
        json_path = os.path.join(os.path.dirname(__file__), "..", "locators", "fallback_locators.json")
        
        try:
            with open(json_path, "r") as f:
                fallbacks = json.load(f)
        except Exception as e:
            logger.error(f"Could not load fallback locators: {e}")
            raise

        if locator_key in fallbacks:
            for strategy, value in fallbacks[locator_key]:
                fallback_locator = (strategy, value)
                logger.info(f"Trying fallback locator: {fallback_locator}")
                try:
                    # using shorter wait time for fallbacks (3 secs)
                    short_wait = WebDriverWait(self.driver, 3)
                    element = short_wait.until(EC.visibility_of_element_located(fallback_locator))
                    logger.info(f"SUCCESS: Healed locator '{locator}' with fallback '{fallback_locator}'")
                    return element
                except TimeoutException:
                    logger.warning(f"Fallback {fallback_locator} also failed.")
        
        logger.error(f"FAILURE: Could not heal locator '{locator}'")
        raise NoSuchElementException(f"Could not find element using primary {locator} or fallbacks.")
        
    def click_element(self, locator):
        element = self.find_element(locator)
        element.click()
        logger.info(f"Clicked on element: {locator}")

    def enter_text(self, locator, text):
        element = self.find_element(locator)
        element.clear()
        element.send_keys(text)
        logger.info(f"Entered text '{text}' into element: {locator}")

    def get_element_text(self, locator):
        element = self.find_element(locator)
        text = element.text
        logger.info(f"Got text '{text}' from element: {locator}")
        return text
