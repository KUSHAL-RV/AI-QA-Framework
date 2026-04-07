from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    """
    A simple performance test mimicking user behavior on a target site.
    Run this with: locust -f tests/performance/locustfile.py --host=https://reqres.in
    """
    wait_time = between(1, 3)

    @task(2)
    def index_page(self):
        # Using ReqRes API for demonstration of traffic generating
        self.client.get("/api/users?page=1", name="Get Users Page 1")

    @task(1)
    def view_user(self):
        self.client.get("/api/users/2", name="Get Single User")

    def on_start(self):
        """Called when a Locust start before any task is scheduled."""
        pass
