import requests
import logging

logger = logging.getLogger(__name__)

class APIClient:
    """
    Wrapper for Python Requests to make API testing easier.
    Handles headers, payloads, and timeout configs.
    """

    def __init__(self, base_url, default_headers=None):
        self.base_url = base_url
        self.default_headers = default_headers or {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def get(self, endpoint, params=None, headers=None):
        url = f"{self.base_url}{endpoint}"
        req_headers = {**self.default_headers, **(headers or {})}
        logger.info(f"GET Request to {url}")
        
        response = requests.get(url, params=params, headers=req_headers, timeout=10)
        logger.info(f"Response Status: {response.status_code}")
        return response

    def post(self, endpoint, payload=None, headers=None):
        url = f"{self.base_url}{endpoint}"
        req_headers = {**self.default_headers, **(headers or {})}
        logger.info(f"POST Request to {url} with payload {payload}")
        
        response = requests.post(url, json=payload, headers=req_headers, timeout=10)
        logger.info(f"Response Status: {response.status_code}")
        return response
