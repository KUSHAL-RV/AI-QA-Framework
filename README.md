# 🤖 Hardened Autonomous AI QA Framework

[![CI/CD Stability](https://img.shields.io/badge/CI%2FCD-100%25%20Stable-brightgreen)](https://github.com/KUSHAL-RV/AI-QA-Framework/actions)
[![AI Engine](https://img.shields.io/badge/AI--Engine-Groq%20%2F%20Llama%203.3-blueviolet)](https://groq.com/)
[![Engine](https://img.shields.io/badge/Engine-Selenium-blue)](https://www.selenium.dev/)

An enterprise-grade, self-healing web auditing agent designed for deep-DOM traversal and resilient test execution. This framework leverages LLMs to automatically recover from locator regressions and uses a risk-based scoring engine to prioritize business-critical navigation paths.

---

## 🌟 Key Features

*   **🛡️ 5-Stage Resilient Discovery**: Multi-layered element finding (Direct -> AI Healing -> Static Fallback -> Polling).
*   **🧠 AI Self-Healing**: Automated recovery from broken locators using Groq-powered Llama 3.3 models.
*   **📈 Risk-Based Auditing**: Automated risk scoring of web elements to prioritize checkout, login, and registration flows.
*   **👁️ Visual Regression Engine**: Pixel-perfect visual comparison with intelligent thresholding.
*   **🔌 CI/CD Native**: 100% compatible with headless environments and strict unit test mocks.

## 🛠️ Architecture Overview

The core of the framework is the **Hybrid Discovery Engine** located in `BasePage.py`. It provides a seamless bridge between modern AI-driven recovery and legacy production stability.

### Discovery Flow
1.  **Fast Path**: Immediate `find_element` call (0ms delay).
2.  **AI Path**: Falls back to `LLMLocatorHealer` for DOM-aware recovery.
3.  **Resilience Path**: Tertiary static fallbacks for mission-critical elements.
4.  **Wait Path**: Manual polling loop to handle slow asynchronous rendering.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- Chrome / ChromeDriver
- [Groq API Key](https://console.groq.com/)

### 2. Installation
```bash
git clone https://github.com/KUSHAL-RV/AI-QA-Framework.git
cd AI-QA-Framework
pip install -r requirements.txt
```

### 3. Environment Setup
Create a `.env` file:
```env
GROQ_API_KEY=your_key_here
SELENIUM_WAIT_TIMEOUT=10
CI=0
```

### 4. Running an Autonomous Audit
```bash
python ai_engine/hybrid_controller.py "https://example.com"
```

## 📊 CI/CD Pass Rates
| Category | Pass Rate | Status |
| :--- | :--- | :--- |
| **Locator Healing** | 100% | 🟢 Stable |
| **Visual Tests** | 100% | 🟢 Stable |
| **API Resilience** | 100% | 🟢 Stable |

---

## 🔮 Roadmap
- [ ] **Real-time Dashboard**: React-based UI for audit visualization.
- [ ] **Dockerization**: Distributed execution via Selenium Grid.
- [ ] **Region Masking**: Intelligent PII/Date masking for visual diffs.

## ⚖️ License
MIT License. Created by Kushal RV.
