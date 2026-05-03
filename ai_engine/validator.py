import inspect
from typing import Any
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    scenario_name: str
    is_valid: bool
    matched_steps: list[str] = field(default_factory=list)
    unmatched_steps: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class AIScenarioValidator:
    """
    Maps AI-generated scenario steps to registered Page Object methods.
    Call validate_all() before executing any AI-generated test suite.
    """

    # Keyword → Page Object method name mappings
    STEP_KEYWORD_MAP = {
        "login":        "login",
        "sign in":      "login",
        "logout":       "logout",
        "navigate":     "navigate_to",
        "open":         "navigate_to",
        "click":        "click_element",
        "enter":        "enter_text",
        "type":         "enter_text",
        "fill":         "enter_text",
        "submit":       "submit_form",
        "verify":       "verify_element_present",
        "assert":       "verify_element_present",
        "check":        "verify_element_present",
        "search":       "search",
        "add to cart":  "add_to_cart",
        "checkout":     "proceed_to_checkout",
        "upload":       "upload_file",
        "select":       "select_option",
        "wait":         "wait_for_element",
    }

    def __init__(self, page_objects: list[Any]):
        """
        Args:
            page_objects: List of instantiated Page Object classes to validate against.
                          e.g. [LoginPage(driver), CartPage(driver)]
        """
        self._available_methods: set[str] = set()
        for page in page_objects:
            methods = {
                name for name, _ in inspect.getmembers(page, predicate=inspect.ismethod)
                if not name.startswith("_")
            }
            self._available_methods.update(methods)

    def validate_scenario(self, scenario: dict) -> ValidationResult:
        """
        Validate a single AI-generated scenario dict.
        Expected shape: {"name": str, "steps": [str, ...]}
        """
        name = scenario.get("name", "unnamed scenario")
        steps = scenario.get("steps", [])
        result = ValidationResult(scenario_name=name, is_valid=True)

        for step in steps:
            matched_method = self._resolve_step(step)
            if matched_method:
                result.matched_steps.append(f"{step!r} → {matched_method}()")
            else:
                result.unmatched_steps.append(step)
                result.is_valid = False
                result.warnings.append(
                    f"No Page Object method found for step: {step!r}"
                )

        if not steps:
            result.is_valid = False
            result.warnings.append("Scenario has no steps.")

        return result

    def validate_all(self, scenarios: list[dict]) -> tuple[list[ValidationResult], bool]:
        """
        Validate a full list of AI-generated scenarios.
        Returns (results, all_passed).
        Use all_passed as the gate before executing the test suite.
        """
        results = [self.validate_scenario(s) for s in scenarios]
        all_passed = all(r.is_valid for r in results)
        return results, all_passed

    def _resolve_step(self, step: str) -> str | None:
        """
        Match a step string to a Page Object method name.
        First checks the keyword map, then falls back to direct method name lookup.
        """
        step_lower = step.lower()

        # 1. Keyword map lookup (longest match wins)
        best_match = None
        best_len = 0
        for keyword, method in self.STEP_KEYWORD_MAP.items():
            if keyword in step_lower and len(keyword) > best_len:
                if method in self._available_methods:
                    best_match = method
                    best_len = len(keyword)

        if best_match:
            return best_match

        # 2. Direct method name lookup (snake_case words in step)
        words = step_lower.replace(" ", "_").replace("-", "_")
        if words in self._available_methods:
            return words

        return None
