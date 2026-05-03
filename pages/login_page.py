from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class LoginPage(BasePage):
    """
    Page Object Model for the Login Page.
    Contains locators and methods specific to the login page.
    Using a sample dummy login UI (e.g., https://the-internet.herokuapp.com/login).
    """

    # Locators
    USERNAME_INPUT = (By.ID, "username")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    FLASH_MESSAGE = (By.ID, "flash")

    def __init__(self, driver, healer=None):
        super().__init__(driver, healer)

    def load(self):
        self.open_url("https://the-internet.herokuapp.com/login")

    def login(self, username, password):
        self.enter_text(self.USERNAME_INPUT, username, locator_key="username_field")
        self.enter_text(self.PASSWORD_INPUT, password, locator_key="password_field")
        self.click_element(self.LOGIN_BUTTON, locator_key="login_button")

    def get_flash_message(self):
        return self.get_element_text(self.FLASH_MESSAGE)
