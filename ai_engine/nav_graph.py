import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Ensure root in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class NavigationGraphBuilder:
    def __init__(self, base_url, max_depth=2):
        self.base_url = base_url
        self.max_depth = max_depth
        self.graph = {} # {url: [neighbor_urls]}
        self.visited = set()

    def get_links(self, driver, current_url):
        links = set()
        elements = driver.find_elements(By.TAG_NAME, "a")
        for el in elements:
            try:
                href = el.get_attribute("href")
                if href and self.base_url in href and "#" not in href:
                    # Clean the URL (remove trailing slashes/queries for stability)
                    clean_href = href.split('?')[0].rstrip('/')
                    links.add(clean_href)
            except Exception:
                continue
        return links

    def build_graph(self):
        print(f"Building Navigation Graph for: {self.base_url}")
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        driver = webdriver.Chrome(options=options)
        
        queue = [(self.base_url.rstrip('/'), 0)]
        
        try:
            while queue:
                url, depth = queue.pop(0)
                if url in self.visited or depth > self.max_depth:
                    continue
                
                print(f"  Analysing depth {depth}: {url}")
                driver.get(url)
                time.sleep(2) # Wait for JS
                
                self.visited.add(url)
                neighbors = self.get_links(driver, url)
                self.graph[url] = list(neighbors)
                
                for neighbor in neighbors:
                    if neighbor not in self.visited:
                        queue.append((neighbor, depth + 1))
        finally:
            driver.quit()
        
        print(f"Graph Built! Total Nodes: {len(self.graph)}")
        return self.graph

    def save_graph(self, path="reports/nav_graph.json"):
        import json
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.graph, f, indent=4)
        print(f"Graph saved to: {path}")

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.laridaetea.com"
    builder = NavigationGraphBuilder(url)
    builder.build_graph()
    builder.save_graph()
