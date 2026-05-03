import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # Environment configs
    ENVIRONMENT = os.getenv("ENVIRONMENT", "qa")
    BASE_URL = os.getenv("BASE_URL", "https://the-internet.herokuapp.com")
    
    # Credentials
    TEST_USERNAME = os.getenv("TEST_USERNAME", "tomsmith")
    TEST_PASSWORD = os.getenv("TEST_PASSWORD", "SuperSecretPassword!")
    
    # External API Integrations
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

settings = Settings()
