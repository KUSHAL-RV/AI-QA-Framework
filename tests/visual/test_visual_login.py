import pytest
from pages.login_page import LoginPage

class TestVisualLogin:
    """
    Visual testing for the login page.
    """

    def test_login_page_visual_baseline(self, driver):
        """
        Captures the baseline for the login page.
        """
        login_page = LoginPage(driver)
        login_page.load()
        
        # Capture baseline or compare
        # The first time this runs, it creates the baseline.
        # Future runs will compare against it.
        login_page.assert_visual_match("login_page_load")

    def test_login_success_visual(self, driver):
        """
        Captures the visual state after a successful login.
        """
        login_page = LoginPage(driver)
        login_page.load()
        login_page.login("tomsmith", "SuperSecretPassword!")
        
        login_page.assert_visual_match("login_success_dashboard")
