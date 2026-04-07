# API Endpoints Configuration
class APIEndpoints:
    BASE_URL = "https://reqres.in/api"
    USERS = f"{BASE_URL}/users"
    SINGLE_USER = lambda user_id: f"{BASE_URL}/users/{user_id}"
    LOGIN = f"{BASE_URL}/login"
    REGISTER = f"{BASE_URL}/register"
