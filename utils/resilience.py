import time
import random
import functools
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException

class ResilienceEngine:
    @staticmethod
    def retry_on_failure(max_retries=3, initial_delay=2):
        """Decorator for exponential backoff retries on Selenium actions."""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                retries = 0
                delay = initial_delay
                while retries < max_retries:
                    try:
                        return func(*args, **kwargs)
                    except (WebDriverException, TimeoutException, NoSuchElementException) as e:
                        retries += 1
                        if retries == max_retries:
                            print(f"Max retries reached for {func.__name__}. Error: {e}")
                            raise
                        
                        # Categorize error
                        category = ResilienceEngine.classify_error(e)
                        print(f"Action {func.__name__} failed (Category: {category}). Retrying {retries}/{max_retries} in {delay}s...")
                        
                        time.sleep(delay + random.uniform(0.5, 1.5)) # Add jitter
                        delay *= 2 # Exponential backoff
                return None
            return wrapper
        return decorator

    @staticmethod
    def classify_error(exception):
        """Classifies the type of failure for intelligent recovery."""
        msg = str(exception).lower()
        if "timeout" in msg:
            return "NETWORK_LATENCY"
        if "unable to locate" in msg or "no such element" in msg:
            return "DOM_MISMATCH"
        if "access denied" in msg or "403" in msg or "captcha" in msg:
            return "BOT_BLOCKED"
        return "UNKNOWN_FLAKE"

    @staticmethod
    def get_human_delay():
        """Returns a randomized delay to simulate human typing/thinking."""
        return random.uniform(0.5, 2.5)

    @staticmethod
    def get_random_user_agent():
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        ]
        return random.choice(agents)
