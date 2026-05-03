from ai_engine.validator import AIScenarioValidator
from ai_engine.generator import AITestGenerator


def dry_run(feature_description: str, page_objects: list) -> bool:
    """
    Generate scenarios from a feature description, then validate them
    against available Page Object methods before any browser is launched.

    Returns True if all scenarios are executable, False otherwise.
    Prints a human-readable report to stdout.

    Usage:
        from pages.login_page import LoginPage
        from pages.cart_page import CartPage

        passed = dry_run(
            "User login and add item to cart",
            page_objects=[LoginPage(driver), CartPage(driver)]
        )
        if passed:
            pytest.main([...])
    """
    print(f"\n{'='*60}")
    print(f"  DRY RUN: {feature_description}")
    print(f"{'='*60}\n")

    generator = AITestGenerator()
    scenarios = generator.generate_scenarios(feature_description)

    if not scenarios:
        print("[WARN] AI generator returned no scenarios. Aborting.")
        return False

    validator = AIScenarioValidator(page_objects)
    results, all_passed = validator.validate_all(scenarios)

    for result in results:
        status = "PASS" if result.is_valid else "FAIL"
        print(f"[{status}] {result.scenario_name}")
        for match in result.matched_steps:
            print(f"       {match}")
        for warning in result.warnings:
            print(f"  [WARN] {warning}")
        print()

    summary = f"{'ALL SCENARIOS VALID' if all_passed else 'VALIDATION FAILED'}"
    print(f"{'='*60}")
    print(f"  {summary}  ({sum(r.is_valid for r in results)}/{len(results)} passed)")
    print(f"{'='*60}\n")

    return all_passed
