import pytest
from unittest.mock import MagicMock
from ai_engine.validator import AIScenarioValidator
from ai_engine.dry_run import dry_run


# --- Unit tests for the validator itself ---

class TestAIScenarioValidator:

    def _make_page(self, methods: list[str]):
        """Create a mock Page Object with the given public methods."""
        class MockPage:
            pass
        
        page = MockPage()
        for m in methods:
            # Define a bound method
            setattr(MockPage, m, lambda self: None)
        return page

    def test_valid_scenario_all_steps_matched(self):
        page = self._make_page(["login", "navigate_to", "verify_element_present"])
        validator = AIScenarioValidator([page])
        result = validator.validate_scenario({
            "name": "Login flow",
            "steps": ["login with credentials", "navigate to dashboard", "verify welcome message"]
        })
        assert result.is_valid is True
        assert len(result.unmatched_steps) == 0

    def test_invalid_scenario_unmatched_step(self):
        page = self._make_page(["login"])
        validator = AIScenarioValidator([page])
        result = validator.validate_scenario({
            "name": "Missing method",
            "steps": ["login with credentials", "perform_unknown_action"]
        })
        assert result.is_valid is False
        assert "perform_unknown_action" in result.unmatched_steps

    def test_empty_steps_fails_validation(self):
        page = self._make_page(["login"])
        validator = AIScenarioValidator([page])
        result = validator.validate_scenario({"name": "Empty scenario", "steps": []})
        assert result.is_valid is False
        assert any("no steps" in w.lower() for w in result.warnings)

    def test_validate_all_returns_aggregate_pass(self):
        page = self._make_page(["login", "search", "add_to_cart"])
        validator = AIScenarioValidator([page])
        scenarios = [
            {"name": "Login", "steps": ["login with valid credentials"]},
            {"name": "Search", "steps": ["search for product"]},
        ]
        results, all_passed = validator.validate_all(scenarios)
        assert all_passed is True
        assert len(results) == 2

    def test_validate_all_fails_if_any_invalid(self):
        page = self._make_page(["login"])
        validator = AIScenarioValidator([page])
        scenarios = [
            {"name": "Valid", "steps": ["login with credentials"]},
            {"name": "Invalid", "steps": ["does_not_exist_anywhere"]},
        ]
        _, all_passed = validator.validate_all(scenarios)
        assert all_passed is False

    def test_methods_aggregated_across_multiple_pages(self):
        login_page = self._make_page(["login", "logout"])
        cart_page   = self._make_page(["add_to_cart", "proceed_to_checkout"])
        validator = AIScenarioValidator([login_page, cart_page])
        result = validator.validate_scenario({
            "name": "Full journey",
            "steps": [
                "login with credentials",
                "add to cart",
                "checkout",
            ]
        })
        assert result.is_valid is True


# --- Integration-style dry run test ---

def test_dry_run_returns_false_on_unmappable_scenarios(monkeypatch):
    """Dry run should block execution when AI outputs gibberish steps."""
    from ai_engine import generator as gen_module

    monkeypatch.setattr(
        gen_module.AITestGenerator,
        "generate_scenarios",
        lambda self, desc: [{"name": "Bad scenario", "steps": ["xyzzy frobulate"]}]
    )
    mock_page = MagicMock()
    result = dry_run("some feature", page_objects=[mock_page])
    assert result is False
