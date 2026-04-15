# AI-Enhanced Test Automation Framework with Self-Healing Capability

This is a scalable automation testing framework built with Python. It supports UI testing, API testing, AI-based test generation, and features self-healing element locators.

## 📁 Project Structure (STEP 1)

```text
PROJECT-QA/
│
├── tests/              # Contains all PyTest test files (UI, API)
├── pages/              # Page Object Model (POM) classes representing web pages
├── utils/              # Reusable core utilities (API clients, Loggers, Helpers)
├── locators/           # Centralized UI element locators & self-healing fallback JSON
├── api/                # API wrapper classes and models
├── reports/            # Output folder for HTML and Allure test reports
├── ai_engine/          # AI logic for descriptive test case generation
├── config/             # Configuration files (environments, driver setup)
├── .github/workflows/  # CI/CD action YAML files
└── requirements.txt    # Project dependencies
```

### Explanation of Folders
- **`tests/`**: The core execution directory. All `test_*.py` files go here so PyTest can discover them.
- **`pages/`**: Holds UI logic. Keeps tests clean by separating element interactions from test assertions.
- **`utils/`**: Helps reduce code duplication. Contains custom loggers, file readers, and API HTTP wrappers.
- **`locators/`**: Stores locator strings. If a locator breaks, the self-healing logic falls back on alternate locators defined here.
- **`api/`**: Separates API request payloads, headers, and specific endpoint details.
- **`reports/`**: Artifact storage for CI/CD or local test debugging.
- **`ai_engine/`**: Module responsible for talking to LLMs (Google Gemini) to generate readable test scenarios from features.
- **`config/`**: Manages environment variables and global variables to switch between dev/staging/prod testing seamlessly.

---

## 🛠️ Setup Instructions (STEP 2)

### 1. Python Environment Setup
Make sure you have Python 3.8+ installed on your system.

Create and activate a virtual environment:
```bash
# On Windows
python -m venv venv
venv\Scripts\activate
```

### 2. Install Required Dependencies
Install the framework libraries:
```bash
pip install -r requirements.txt
```

### 3. WebDriver Setup (Chrome)
Selenium 4 handles WebDriver management automatically (via Selenium Manager). Therefore, you do not need to download the `chromedriver` binary manually. Ensure Google Chrome is installed on your machine.

### 4. Running PyTest
Run all tests in the project:
```bash
pytest
```

Run tests with console output:
```bash
pytest -v -s
```

### 5. Generating Reports
To generate a simple integrated HTML report:
```bash
pytest --html=reports/report.html --self-contained-html
```

To use Allure (if you have Allure CLI installed):
```bash
pytest --alluredir=reports/allure-results
# After test run:
allure serve reports/allure-results
```

---

## 🏃‍♀️ Sample Test Execution Output (STEP 10)

```bash
$ pytest -v -s
============================= test session starts ==============================
collected 6 items

tests/test_ai_generator.py::TestAIGenerator::test_mock_rule_based_login_generation PASSED
tests/test_api.py::TestAPI::test_get_users PASSED
tests/test_api.py::TestAPI::test_create_user PASSED
tests/test_login.py::TestLogin::test_valid_login PASSED
tests/test_login.py::TestLogin::test_invalid_login PASSED
tests/test_self_healing.py::TestSelfHealing::test_broken_locators_heal_successfully 
WARNING: Primary locator failed: ('id', 'broken_username'). Attempting self-healing...
INFO: SUCCESS: Healed locator ('id', 'broken_username') with fallback ('name', 'username')
PASSED

============================== 6 passed in 12.4s ===============================
```

## 📈 Performance Testing (STEP 8)
Run a simple load test to benchmark the API response:
```bash
locust -f tests/performance/locustfile.py --host=https://jsonplaceholder.typicode.com
```
Navigate to `http://localhost:8089` to view the Locust dashboard and start spawning users.

## 🤖 AI Test Generation (STEP 6)
You can automatically generate test cases from feature descriptions! Setting the `GEMINI_API_KEY` environment variable enables real Google Gemini generation, otherwise it defaults to a local rule-based engine.
```python
from ai_engine.generator import AITestGenerator
generator = AITestGenerator()
print(generator.generate_test_cases("Checkout Flow"))
```

## 🔄 CI/CD Pipeline (STEP 9)
A GitHub actions YAML file is provided under `.github/workflows/main.yml`. It triggers tests on every push/PR to the `main` branch, running UI/API tests Headless and uploading an HTML report artifact.
