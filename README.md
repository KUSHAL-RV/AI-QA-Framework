# AI-Enhanced Test Automation Framework

<<<<<<< HEAD
A production-grade, scalable automation framework built with **Python**, **Selenium**, and **PyTest**. This framework integrates **LLM-powered self-healing**, **AI test generation**, and **visual regression testing** to provide end-to-end quality assurance.
=======
This is a scalable automation testing framework built with Python. It supports UI testing, API testing, AI-based test generation, and features self-healing element locators.
>>>>>>> 921db0a294a74f199286f74fbed6410fe8bb0531

## 🚀 Key Innovations

### 🧠 AI Test Generation & Validation
- **Descriptive Generation**: Uses **Google Gemini (1.5 Flash)** to generate executable test scenarios from natural language feature descriptions.
- **Dry Run Validation**: A safety layer that maps AI-generated steps to Page Object methods *before* browser execution, preventing hallucinations and ensuring stability.

### 🩹 LLM-Powered Self-Healing
- **Three-Layer Escalation**: Elements are resolved through Primary -> Static Fallback -> LLM Healing.
- **Automated Recovery**: If locators break, Gemini analyzes a pruned DOM snapshot to suggest a fix.
- **Thread-Safe Persistence**: Healed locators are automatically written back to a JSON registry using `FileLock`, ensuring the AI is only called once per broken element.

### 🖼️ Visual Regression Testing
- **Pixel-Level Validation**: Uses **Pillow** for screenshot comparison with configurable thresholds.
- **Visual Diffs**: Automatically generates diff images highlighting UI shifts in red for rapid auditing.

## 📁 Project Structure

```text
PROJECT-QA/
├── ai_engine/          # Gemini integration, healing logic, and dry-run validator
├── tests/              # Functional (UI/API), AI-driven, and Visual test suites
├── pages/              # Page Object Model with integrated healing hooks
├── utils/              # Visual comparator, API clients, and core helpers
├── locators/           # Centralized locators & self-healing fallback registry
├── screenshots/        # Baseline, Latest, and Diff images for visual testing
├── config/             # Environment settings and API key management
└── .github/workflows/  # CI/CD pipeline with secret injection
```

## 🛠️ Setup & Execution

### 1. Environment Setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_api_key_here
ENVIRONMENT=qa
BASE_URL=https://the-internet.herokuapp.com
```

### 3. Running Tests
```bash
# Run functional tests (with 8-core parallelization)
pytest -n auto

# Run visual regression tests
pytest tests/visual/

# Run with HTML report
pytest --html=reports/report.html --self-contained-html
```

## 🔄 CI/CD Pipeline
The included GitHub Action (`main.yml`) automates:
1. Environment setup and dependency installation.
2. Secure secret injection for Gemini API.
3. Parallel test execution.
4. Test report artifact uploading.

## 🤖 AI Healing in Action
When a primary locator fails, you'll see the escalation in the logs:
```text
WARNING - Primary locator failed: ('id', 'broken_btn'). Attempting fallbacks...
WARNING - All static fallbacks exhausted for 'login_button'
INFO - Attempting LLM healing for 'login_button'...
INFO - LLM suggested new locator: ('xpath', '//button[@type="submit"]')
INFO - Successfully healed 'login_button'. Persisting to registry.
```
