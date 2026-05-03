import os
import sys
import json
from groq import Groq
from config.settings import settings

# Ensure root in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_engine.execution_cache import ExecutionCache

class RiskScorer:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.cache = ExecutionCache()

    def score_elements(self, page_source, url):
        """Analyzes page source and returns a list of high-risk elements to test."""
        # Focus on a larger snippet for better context
        snippet = page_source[:8000]
        
        # Check Cache first
        cached = self.cache.get_decision(url, snippet)
        if cached:
            print(f"  Using cached risk analysis for: {url}")
            return cached
            
        print(f"Scoring risks for: {url} (New analysis)...")

        prompt = f"""
        Analyze the following HTML and identify the top 5 most critical business features (buttons, inputs, links).
        URL: {url}
        HTML Snippet: {snippet}
        
        TASK:
        Assign a risk score (1-10) and provide multiple locator strategies (id, aria, css, xpath).
        
        OUTPUT FORMAT:
        {{
          "elements": [
            {{
              "element_name": "...", 
              "locators": {{"id": "...", "aria": "...", "css": "...", "xpath": "..."}}, 
              "risk_score": 10, 
              "rationale": "..."
            }}
          ]
        }}
        """

        try:
            # Attempt with primary model
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
        except Exception as e:
            if "rate_limit" in str(e).lower():
                print("  Primary model rate limited. Falling back to llama3-8b-8192...")
                response = self.client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
            else:
                raise

        try:
            data = json.loads(response.choices[0].message.content)
            elements = []
            
            # Flexible extraction
            if isinstance(data, dict):
                if "elements" in data:
                    elements = data["elements"]
                else:
                    # Look for any list in the dict
                    for val in data.values():
                        if isinstance(val, list):
                            elements = val
                            break
            elif isinstance(data, list):
                elements = data
                if not elements and len(data) > 0:
                    # If the root is a list wrapped in a single key
                    first_key = list(data.keys())[0]
                    if isinstance(data[first_key], list):
                        elements = data[first_key]
            
            # Save to cache
            if elements:
                self.cache.save_decision(url, snippet, elements)
            return elements
        except Exception as e:
            print(f"Risk Scoring Error: {e}")
            return []

if __name__ == "__main__":
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    
    url = "https://www.laridaetea.com"
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    
    scorer = RiskScorer()
    risks = scorer.score_elements(driver.page_source, url)
    print(json.dumps(risks, indent=2))
    driver.quit()
