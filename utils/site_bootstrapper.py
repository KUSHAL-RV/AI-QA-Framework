import sys
import os

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import re
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from groq import Groq
from config.settings import settings

class SiteBootstrapper:
    def __init__(self, url):
        self.url = url
        self.site_name = self._extract_site_name(url)
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def _extract_site_name(self, url):
        # Remove protocol and www
        name = re.sub(r'https?://(www\.)?', '', url)
        # Take the main domain part
        name = name.split('.')[0]
        # Clean special chars
        name = re.sub(r'[^a-zA-Z0-9]', '_', name).lower()
        return name

    def get_site_source(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        driver = webdriver.Chrome(options=options)
        try:
            driver.get(self.url)
            time.sleep(3)
            return driver.page_source
        finally:
            driver.quit()

    def bootstrap(self):
        print(f"Bootstrapping tests for: {self.url}...")
        source = self.get_site_source()
        source_snippet = source[:6000]

        page_filename = f"{self.site_name}_page"
        page_class = f"{self.site_name.replace('_', '').capitalize()}Page"

        prompt = f"""
        Generate a Page Object and a PyTest suite for: {self.url}
        
        HTML SNIPPET: {source_snippet}
        
        FILENAMES (USE THESE EXACTLY):
        - Page Module: pages.{page_filename}
        - Page Class: {page_class}
        
        OUTPUT FORMAT:
        ---PAGE_CODE---
        <python class code>
        ---TEST_CODE---
        <pytest code>
        
        RULES:
        1. Import: from pages.{page_filename} import {page_class}
        2. Inherit from 'pages.base_page.BasePage'.
        3. Keep the test short (max 3 assertions).
        4. No markdown blocks inside the code.
        """

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.choices[0].message.content

        # Extract blocks
        try:
            page_code = text.split("---PAGE_CODE---")[1].split("---TEST_CODE---")[0].strip()
            test_code = text.split("---TEST_CODE---")[1].strip()
            
            # Clean markdown
            page_code = re.sub(r'^```python\n|```$', '', page_code, flags=re.MULTILINE)
            test_code = re.sub(r'^```python\n|```$', '', test_code, flags=re.MULTILINE)
        except Exception:
            print("AI format error, attempting regex recovery...")
            # Fallback if AI didn't use markers correctly
            page_code = re.search(r'class .*Page\(BasePage\):.*(?=class|def|import|---TEST)', text, re.DOTALL).group(0)
            test_code = re.search(r'def test_.*', text, re.DOTALL).group(0)

        # Write files
        os.makedirs("pages", exist_ok=True)
        os.makedirs("tests", exist_ok=True)

        with open(f"pages/{page_filename}.py", "w", encoding="utf-8") as f:
            f.write(page_code)
        with open(f"tests/test_{self.site_name}_auto.py", "w", encoding="utf-8") as f:
            f.write(test_code)

        print(f"Created: pages/{page_filename}.py")
        print(f"Created: tests/test_{self.site_name}_auto.py")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        bootstrapper = SiteBootstrapper("https://www.google.com")
    else:
        bootstrapper = SiteBootstrapper(sys.argv[1])
    bootstrapper.bootstrap()
