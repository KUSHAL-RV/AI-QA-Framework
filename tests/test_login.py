import pytest
from pages.login_page import LoginPage

class TestLogin:
    """
    Tests for the Login page. 
    Using Pytest assertions.
    """

    def test_valid_login(self, driver, healer):
        login_page = LoginPage(driver, healer)
        login_page.load()
        login_page.login("tomsmith", "SuperSecretPassword!")
        
        flash_message = login_page.get_flash_message()
        # Assertion: Check if the success message is displayed
        assert "You logged into a secure area!" in flash_message

    def test_invalid_login(self, driver, healer):
        login_page = LoginPage(driver, healer)
        login_page.load()
        login_page.login("invalid_user", "invalid_password")
        
        flash_message = login_page.get_flash_message()
        # Assertion: Check if error message is displayed
        assert "Your username is invalid!" in flash_message
