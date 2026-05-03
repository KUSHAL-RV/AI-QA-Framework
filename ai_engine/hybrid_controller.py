import os
import sys
import time
from ai_engine.nav_graph import NavigationGraphBuilder
from ai_engine.risk_engine import RiskScorer
from utils.state_manager import StateManager
from utils.visual_engine import VisualEngine
from utils.resilience import ResilienceEngine
from selenium.webdriver.common.by import By

# Ensure root in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class HybridExecutionController:
    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url
        self.nav_builder = NavigationGraphBuilder(base_url)
        self.risk_scorer = RiskScorer()
        self.state_manager = StateManager(session_id=f"session_{int(time.time())}")
        self.visual_engine = VisualEngine()

    @ResilienceEngine.retry_on_failure(max_retries=3)
    def plan_and_execute(self):
        """The main autonomous loop with Resilience and Caching."""
        print(f"--- Starting Hardened Autonomous Audit: {self.base_url} ---")
        
        # Step 1: Map the site
        graph = self.nav_builder.build_graph()
        self.state_manager.set_variable("site_graph", graph)
        
        # Step 2: Audit each node
        for url in graph.keys():
            self.execute_path(url)
            
        print(f"--- Hardened Audit Complete. Session: {self.state_manager.session_id} ---")

    def execute_path(self, url):
        print(f"Auditing Path: {url}")
        self.driver.get(url)
        time.sleep(ResilienceEngine.get_human_delay())
        
        # Identify Risks (Uses Cache automatically)
        features = self.risk_scorer.score_elements(self.driver.page_source, url)
        
        for feature in features:
            if feature.get("risk_score", 0) >= 7:
                self.test_feature(feature)

    @ResilienceEngine.retry_on_failure(max_retries=2)
    def test_feature(self, feature):
        name = feature.get("element_name")
        locators = feature.get("locators", {})
        
        print(f"  Testing: {name}")
        
        element = None
        # Try all strategies in order of stability
        for strategy, value in locators.items():
            if not value: continue
            try:
                if strategy == "id":
                    element = self.driver.find_element(By.ID, value)
                elif strategy == "aria":
                    element = self.driver.find_element(By.XPATH, f"//*[@aria-label='{value}']")
                elif strategy == "css":
                    element = self.driver.find_element(By.CSS_SELECTOR, value)
                elif strategy == "xpath":
                    element = self.driver.find_element(By.XPATH, value)
                
                if element:
                    print(f"    Found via {strategy}")
                    break
            except:
                continue

        if not element:
            raise Exception(f"All locator strategies failed for {name}")

        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            
            # Save screenshot with absolute path
            os.makedirs("reports/sessions/screenshots", exist_ok=True)
            shot_path = os.path.abspath(f"reports/sessions/screenshots/{self.state_manager.session_id}_{name}.png")
            self.driver.save_screenshot(shot_path)
            
            # Record Success
            self.state_manager.log_action(f"Interact {name}", "Success", screenshot=f"screenshots/{os.path.basename(shot_path)}")
        except Exception as e:
            print(f"  Interaction Failure: {name} - {e}")
            self.state_manager.log_action(f"Interact {name}", "Failed")

if __name__ == "__main__":
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.laridaetea.com"
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument(f"user-agent={ResilienceEngine.get_random_user_agent()}")
    driver = webdriver.Chrome(options=options)
    
    controller = HybridExecutionController(driver, target_url)
    controller.plan_and_execute()
    driver.quit()
