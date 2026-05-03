import os
import json
import time

class StateManager:
    def __init__(self, session_id):
        self.session_id = session_id
        self.context = {
            "current_step": 0,
            "history": [],
            "variables": {},
            "start_time": time.time()
        }
        self.log_path = f"reports/sessions/{session_id}.json"
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log_action(self, action_name, result, screenshot=None):
        """Records an action and its outcome in the session history."""
        self.context["current_step"] += 1
        entry = {
            "step": self.context["current_step"],
            "action": action_name,
            "result": result,
            "timestamp": time.time(),
            "screenshot": screenshot
        }
        self.context["history"].append(entry)
        self._persist()

    def set_variable(self, key, value):
        """Stores a variable for use in later steps (e.g., Order ID)."""
        self.context["variables"][key] = value
        self._persist()

    def get_variable(self, key, default=None):
        return self.context["variables"].get(key, default)

    def _persist(self):
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(self.context, f, indent=4)

    def get_summary(self):
        duration = time.time() - self.context["start_time"]
        return {
            "steps": self.context["current_step"],
            "duration_sec": round(duration, 2),
            "status": "Completed" if self.context["history"][-1]["result"] == "Success" else "Failed"
        }
