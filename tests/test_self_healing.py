import pytest
from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class BrokenLoginPage(BasePage):
    """
    Simulates a login page where the dev broke the original element locators.
    Self-healing should automatically resolve these.
    """
    USERNAME_INPUT = (By.ID, "broken_username")
    PASSWORD_INPUT = (By.ID, "broken_password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='broken']")
    FLASH_MESSAGE = (By.ID, "flash")

    def __init__(self, driver, healer=None):
        super().__init__(driver, healer)

    def load(self):
        self.open_url("https://the-internet.herokuapp.com/login")

    def login(self, username, password):
        self.enter_text(self.USERNAME_INPUT, username, locator_key="username_field")
        self.enter_text(self.PASSWORD_INPUT, password, locator_key="password_field")
        self.click_element(self.LOGIN_BUTTON, locator_key="login_button")

class TestSelfHealing:
    """
    Tests the Self Healing locator system by injecting broken locators.
    """

    def test_broken_locators_heal_successfully(self, driver, healer):
        login_page = BrokenLoginPage(driver, healer)
        login_page.load()
        login_page.login("tomsmith", "SuperSecretPassword!")
        
        message = login_page.get_element_text(login_page.FLASH_MESSAGE)
        assert "You logged into a secure area!" in message
