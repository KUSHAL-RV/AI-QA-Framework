import pytest
from utils.api_client import APIClient

@pytest.fixture(scope="module")
def api_client():
    # Using jsonplaceholder as a mock API for demonstration to avoid 401 blocks
    base_url = "https://jsonplaceholder.typicode.com"
    return APIClient(base_url)

class TestAPI:
    """
    Example API tests using the APIClient module.
    """

    def test_get_users(self, api_client):
        response = api_client.get("/users")
        
        # Validations
        assert response.status_code == 200
        
        # Validate Response JSON (JSONPlaceholder returns a list of users)
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "id" in data[0]
        assert "name" in data[0]
        
        # Validate Response Time
        assert response.elapsed.total_seconds() < 3.0  # response should be under 3s

    def test_create_user(self, api_client):
        payload = {
            "name": "morpheus",
            "username": "leader"
        }
        response = api_client.post("/users", payload=payload)
        
        # Validations
        assert response.status_code == 201
        
        # Validate Response JSON
        data = response.json()
        assert data["name"] == "morpheus"
        assert data["username"] == "leader"
        assert "id" in data
        
        # Validate Response Time
        assert response.elapsed.total_seconds() < 3.0
