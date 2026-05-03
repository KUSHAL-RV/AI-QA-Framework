import os
from google import genai
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class AITestGenerator:
    """
    Integrates with Google Gemini API to generate test cases based on a feature description.
    Falls back to simple rule-based generation if no API key is set.
    """
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("GEMINI_API_KEY not found. Using simple rule-based mock generator.")

    def generate_test_cases(self, feature_description: str):
        if self.client:
            return self._generate_via_gemini(feature_description)
        else:
            return self._generate_via_rules(feature_description)

    def generate_scenarios(self, feature_description: str) -> list[dict]:
        """
        Generates structured scenarios: [{"name": str, "steps": [str, ...]}]
        """
        cases = self.generate_test_cases(feature_description)
        # For this simple implementation, treat each case as a scenario with one step
        return [{"name": case, "steps": [case]} for case in cases]

    def _generate_via_gemini(self, feature_description: str):
        prompt = f"Generate a list of 5 brief testing scenarios for the following feature. Return each scenario on a new line: {feature_description}"
        try:
            response = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            return response.text.strip().split('\n')
        except Exception as e:
            logger.error(f"Gemini API failed: {e}")
            return self._generate_via_rules(feature_description)

    def _generate_via_rules(self, feature_description: str):
        feature_lower = feature_description.lower()
        test_cases = [f"Verify basic functionality of {feature_description}"]
        
        if "login" in feature_lower or "auth" in feature_lower:
            test_cases.extend([
                "Verify successful login with valid credentials",
                "Verify login fails with invalid password",
                "Verify validation error on empty username and password fields",
                "Verify password masking"
            ])
        elif "cart" in feature_lower or "checkout" in feature_lower:
            test_cases.extend([
                "Verify adding an item to the cart",
                "Verify removing an item from the cart",
                "Verify total price calculation",
                "Verify checkout process requires payment information"
            ])
        else:
            test_cases.extend([
                "Verify empty state handling",
                "Verify error handling for invalid input",
                "Verify behavior with maximum input length"
            ])
        
        return test_cases
