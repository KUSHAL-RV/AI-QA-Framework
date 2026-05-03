import json
import logging
import re
from pathlib import Path
from typing import Optional
from filelock import FileLock

import google.generativeai as genai
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__)

# Adjusted path to be relative to the project root
FALLBACK_LOCATORS_PATH = Path("locators/fallback_locators.json")

# How many characters of raw HTML to send to the LLM.
# Enough context without burning tokens on boilerplate.
DOM_CHAR_LIMIT = 8_000


class HealingResult:
    def __init__(self, by: str, value: str, confidence: str):
        self.by = by
        self.value = value
        self.confidence = confidence  # "high" | "medium" | "low"

    def to_selenium_args(self) -> tuple[str, str]:
        by_map = {
            "id":    By.ID,
            "xpath": By.XPATH,
            "css":   By.CSS_SELECTOR,
            "name":  By.NAME,
        }
        return by_map.get(self.by, By.XPATH), self.value


import os
from groq import Groq

class LLMLocatorHealer:
    """
    Last-resort locator recovery using Groq.
    Called by BasePage.find_element only after all static fallbacks fail.
    """

    _SYSTEM_PROMPT = """You are an expert Selenium test automation engineer.
A UI locator has broken because the application HTML changed.
You will receive:
  1. The element description (what it does, its label/role)
  2. A pruned snapshot of the current live DOM around the area where the element should be

Your task: suggest the BEST single locator to find this element.

Respond ONLY with a valid JSON object — no markdown, no explanation:
{
  "by": "id" | "xpath" | "css" | "name",
  "value": "<locator string>",
  "confidence": "high" | "medium" | "low",
  "reasoning": "<one sentence>"
}

Rules:
- DO NOT invent or hallucinate data-testids if you don't see them in the HTML.
- Prefer stable attributes: aria-label, role, name, type, title.
- If no stable IDs exist, use a short relative XPath anchored to a unique text element or a stable parent.
- Avoid positional XPath like //div[3]/span[2] unless absolutely necessary.
- Return ONLY the JSON.
"""

    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.error("GROQ_API_KEY is not configured. AI Healing will be disabled.")
            self._client = None
            return
            
        self._client = Groq(api_key=api_key)
        self._model = "llama-3.3-70b-versatile"

    def heal(
        self,
        driver: WebDriver,
        locator_key: str,
        element_description: str,
    ) -> Optional[HealingResult]:
        """
        Attempt to heal a broken locator.

        Args:
            driver:              Active WebDriver session (used to capture DOM).
            locator_key:         The locator registry key, e.g. "login_button".
            element_description: Human-readable description sent to the LLM as context.

        Returns:
            HealingResult if a valid suggestion was produced, None otherwise.
        """
        dom_snapshot = self._extract_dom(driver)
        prompt = self._build_prompt(locator_key, element_description, dom_snapshot)

        if not self._client:
            return None
            
        try:
            chat_completion = self._client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self._SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                model=self._model,
                temperature=0.0,
            )
            raw = chat_completion.choices[0].message.content.strip()
            result = self._parse_response(raw)
            if result:
                logger.info(
                    "Groq healing succeeded for '%s': %s='%s' (confidence: %s)",
                    locator_key, result.by, result.value, result.confidence,
                )
            return result
        except Exception as exc:
            logger.warning("LLM healing failed for '%s': %s", locator_key, exc)
            return None

    def write_back(self, locator_key: str, result: HealingResult) -> None:
        """
        Persist the healed locator to fallback_locators.json so it is
        used directly on the next run without calling the LLM again.
        Uses FileLock to prevent race conditions during parallel execution.
        """
        lock = FileLock(str(FALLBACK_LOCATORS_PATH) + ".lock")
        with lock:
            data: dict = {}
            if FALLBACK_LOCATORS_PATH.exists():
                try:
                    with open(FALLBACK_LOCATORS_PATH) as f:
                        data = json.load(f)
                except json.JSONDecodeError:
                    data = {}

            entry = data.get(locator_key, [])
            if not isinstance(entry, list):
                entry = []
            
            new_locator = [result.by, result.value]
            if new_locator not in entry:
                entry.insert(0, new_locator)
            
            data[locator_key] = entry

            with open(FALLBACK_LOCATORS_PATH, "w") as f:
                json.dump(data, f, indent=2)

        logger.info("Write-back complete for '%s'", locator_key)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_dom(self, driver: WebDriver) -> str:
        """
        Extract a pruned DOM snapshot.
        Strips <script>, <style>, and SVG blobs to reduce token usage,
        then truncates to DOM_CHAR_LIMIT characters.
        """
        raw_html: str = driver.execute_script(
            "return document.body.innerHTML;"
        )
        # Remove script/style blocks
        cleaned = re.sub(r"<script[\s\S]*?</script>", "", raw_html, flags=re.I)
        cleaned = re.sub(r"<style[\s\S]*?</style>",  "", cleaned,  flags=re.I)
        cleaned = re.sub(r"<svg[\s\S]*?</svg>",      "", cleaned,  flags=re.I)
        # Collapse whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned[:DOM_CHAR_LIMIT]

    def _build_prompt(
        self,
        locator_key: str,
        element_description: str,
        dom_snapshot: str,
    ) -> str:
        return (
            f"{self._SYSTEM_PROMPT}\n\n"
            f"## Element to locate\n"
            f"Key: {locator_key}\n"
            f"Description: {element_description}\n\n"
            f"## Current DOM (pruned)\n"
            f"{dom_snapshot}"
        )

    def _parse_response(self, raw: str) -> Optional[HealingResult]:
        """
        Parse LLM JSON response. Strips markdown fences if present.
        Returns None if the response is malformed or missing required fields.
        """
        # Strip ```json ... ``` fences
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
        try:
            data = json.loads(cleaned)
            by    = data.get("by", "").lower()
            value = data.get("value", "").strip()
            conf  = data.get("confidence", "low")
            if by and value:
                return HealingResult(by=by, value=value, confidence=conf)
        except json.JSONDecodeError:
            logger.warning("LLM response was not valid JSON: %r", raw[:200])
        return None
