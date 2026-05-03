import json
import pytest
from unittest.mock import MagicMock, patch
from selenium.common.exceptions import NoSuchElementException

from ai_engine.locator_healer import LLMLocatorHealer, HealingResult
from pages.base_page import BasePage


class TestLLMLocatorHealer:

    def _mock_healer(self, by="xpath", value="//button[@data-testid='login']", confidence="high"):
        healer = MagicMock(spec=LLMLocatorHealer)
        healer.heal.return_value = HealingResult(by=by, value=value, confidence=confidence)
        healer.write_back = MagicMock()
        return healer

    def _base_page(self, driver, healer=None):
        # We need to properly initialize BasePage to avoid issues with _load_fallbacks
        with patch('pages.base_page.BasePage._load_fallbacks', return_value={}):
            page = BasePage(driver, healer)
        return page

    def test_primary_locator_success_skips_healing(self):
        driver = MagicMock()
        mock_element = MagicMock()
        mock_element.is_displayed.return_value = True
        driver.find_element.return_value = mock_element
        healer = self._mock_healer()
        page = self._base_page(driver, healer)

        page.find_element(("id", "login-btn"), locator_key="login_button")

        healer.heal.assert_not_called()

    def test_llm_healing_called_when_all_static_fail(self):
        driver = MagicMock()
        mock_element = MagicMock()
        mock_element.is_displayed.return_value = True
        
        def find_element_side_effect(by, value):
            if value == "old-id":
                raise NoSuchElementException()
            return mock_element

        driver.find_element.side_effect = find_element_side_effect
        
        healer = self._mock_healer()
        page = self._base_page(driver, healer)

        element = page.find_element(("id", "old-id"), locator_key="login_button")

        healer.heal.assert_called_once()
        healer.write_back.assert_called_once()
        assert element is not None

    def test_write_back_called_after_successful_healing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "ai_engine.locator_healer.FALLBACK_LOCATORS_PATH",
            tmp_path / "fallback_locators.json"
        )
        healer = LLMLocatorHealer.__new__(LLMLocatorHealer)

        result = HealingResult(by="css selector", value="button.login-cta", confidence="high")
        healer.write_back("login_button", result)

        data = json.loads((tmp_path / "fallback_locators.json").read_text())
        assert data["login_button"][0][0] == "css selector"
        assert data["login_button"][0][1] == "button.login-cta"

    def test_no_healer_raises_after_static_exhaustion(self):
        driver = MagicMock()
        driver.find_element.side_effect = NoSuchElementException()
        page = self._base_page(driver, healer=None)

        with pytest.raises(NoSuchElementException):
            page.find_element(("id", "missing"), locator_key="login_button")

    def test_invalid_llm_response_raises_gracefully(self):
        driver = MagicMock()
        driver.find_element.side_effect = NoSuchElementException()
        healer = MagicMock(spec=LLMLocatorHealer)
        healer.heal.return_value = None  # LLM returned garbage
        page = self._base_page(driver, healer)

        with pytest.raises(NoSuchElementException):
            page.find_element(("id", "bad-id"), locator_key="login_button")

    def test_parse_response_strips_markdown_fences(self):
        healer = LLMLocatorHealer.__new__(LLMLocatorHealer)
        raw = '```json\n{"by":"css selector","value":".submit-btn","confidence":"high"}\n```'
        result = healer._parse_response(raw)
        assert result is not None
        assert result.by == "css selector"
        assert result.value == ".submit-btn"

    @patch.dict(os.environ, {"CI": ""})
    def test_low_confidence_result_still_attempted(self):
        driver = MagicMock()
        mock_element = MagicMock()
        mock_element.is_displayed.return_value = True

        def find_element_side_effect(by, value):
            if value == "old":
                raise NoSuchElementException()
            return mock_element

        driver.find_element.side_effect = find_element_side_effect
        
        healer = self._mock_healer(confidence="low")
        page = self._base_page(driver, healer)

        element = page.find_element(("id", "old"), locator_key="login_button")
        assert element is not None

    def test_low_confidence_rejected_in_ci(self, monkeypatch):
        monkeypatch.setenv("CI", "1")
        driver = MagicMock()
        driver.find_element.side_effect = NoSuchElementException()
        
        healer = self._mock_healer(confidence="low")
        page = self._base_page(driver, healer)

        with pytest.raises(NoSuchElementException):
            page.find_element(("id", "old"), locator_key="login_button")
        
        # Healer was called, but result was rejected
        healer.heal.assert_called_once()
        # write_back should NOT be called
        healer.write_back.assert_not_called()
