from locust import HttpUser, task, between
import random

class RiskAssessmentUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def assess_risk(self):
        """Risk assessment endpoint (heaviest)"""
        payload = {
            "features": [random.random() for _ in range(50)],
            "model_version": "1.0"
        }
        self.client.post("/api/risk/assess", json=payload)
    
    @task(2)
    def get_features(self):
        """Feature extraction"""
        self.client.get("/api/features?entity_id=123")
    
    @task(1)
    def predict(self):
        """Model prediction"""
        payload = {"input": [random.random() for _ in range(10)]}
        self.client.post("/api/model/predict", json=payload)
    
    def on_start(self):
        """Setup for each user"""
        self.entity_id = random.randint(1000, 10000)
