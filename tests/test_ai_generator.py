import pytest
from ai_engine.generator import AITestGenerator

class TestAIGenerator:
    """
    Tests the logic of the AI Test Case Generator module.
    """

    def test_mock_rule_based_login_generation(self):
        generator = AITestGenerator()
        # In absence of an OPENAI_API_KEY, this uses the rule-based fallback.
        test_cases = generator.generate_test_cases("login page")
        
        assert len(test_cases) > 1
        assert any("valid credentials" in tc.lower() for tc in test_cases)
        assert any("invalid password" in tc.lower() for tc in test_cases)
        assert any("empty" in tc.lower() for tc in test_cases)
