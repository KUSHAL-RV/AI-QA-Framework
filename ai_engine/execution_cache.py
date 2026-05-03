import json
import os
import hashlib

class ExecutionCache:
    def __init__(self, cache_file="config/agent_cache.json"):
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_decision(self, prompt, dom_snippet):
        """Returns a cached decision if available for the given state."""
        state_hash = self._generate_hash(prompt, dom_snippet)
        return self.cache.get(state_hash)

    def save_decision(self, prompt, dom_snippet, decision):
        """Saves a new decision to the cache."""
        state_hash = self._generate_hash(prompt, dom_snippet)
        self.cache[state_hash] = decision
        self._persist()

    def _generate_hash(self, prompt, dom_snippet):
        # We hash the combination of prompt and DOM to ensure context-aware determinism
        raw = f"{prompt}|{dom_snippet}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def _persist(self):
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=4)
