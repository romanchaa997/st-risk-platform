"""Load testing configuration for performance validation.

Usage:
    locust -f load_test_config.py --host=http://localhost:8000 --users=100 --spawn-rate=10
    # or
    python load_test_config.py
"""

from locust import HttpUser, task, between
import random


class RiskAssessmentUser(HttpUser):
    """Simulates risk assessment API users."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a simulated user starts."""
        # Portfolio IDs to test against
        self.portfolio_ids = [f'portfolio_{i:03d}' for i in range(1, 51)]
    
    @task(3)
    def assess_single_portfolio(self):
        """Task: Assess a single portfolio (high frequency)."""
        portfolio_id = random.choice(self.portfolio_ids)
        self.client.post(
            f'/api/v1/assess/{portfolio_id}',
            json={'model_version': '1.0.0'},
            timeout=30
        )
    
    @task(2)
    def batch_assess_portfolios(self):
        """Task: Assess multiple portfolios in batch (medium frequency)."""
        portfolio_ids = random.sample(self.portfolio_ids, 10)
        self.client.post(
            '/api/v1/assess/batch',
            json={'portfolio_ids': portfolio_ids},
            timeout=60
        )
    
    @task(1)
    def get_dashboard(self):
        """Task: Load dashboard with metrics (low frequency)."""
        portfolio_id = random.choice(self.portfolio_ids)
        self.client.get(
            f'/api/v1/dashboard/{portfolio_id}',
            params={'timeframe': '7d'},
            timeout=30
        )
    
    @task(2)
    def fetch_metrics(self):
        """Task: Fetch aggregated metrics."""
        self.client.get(
            '/api/v1/metrics',
            params={'limit': 100},
            timeout=15
        )
    
    @task(1)
    def get_alerts(self):
        """Task: Get active alerts."""
        portfolio_id = random.choice(self.portfolio_ids)
        self.client.get(
            f'/api/v1/alerts/{portfolio_id}',
            params={'severity': 'high'},
            timeout=10
        )


class CacheValidationUser(HttpUser):
    """Validates caching effectiveness."""
    
    wait_time = between(0.5, 2)  # Shorter wait for cache validation
    
    def on_start(self):
        """Initialize test data."""
        self.test_portfolio = 'portfolio_cache_test'
    
    @task(5)
    def repeated_assessment(self):
        """Repeated calls to same endpoint (for cache hit validation)."""
        # Should be cached after first call
        self.client.post(
            f'/api/v1/assess/{self.test_portfolio}',
            json={'model_version': '1.0.0'},
            timeout=30
        )
    
    @task(3)
    def repeated_dashboard(self):
        """Repeated dashboard calls (should hit cache)."""
        self.client.get(
            f'/api/v1/dashboard/{self.test_portfolio}',
            params={'timeframe': '7d'},
            timeout=15
        )


class StressTestUser(HttpUser):
    """Stress testing with aggressive load."""
    
    wait_time = between(0.1, 0.5)  # Minimal wait
    
    def on_start(self):
        """Initialize for stress test."""
        self.portfolio_ids = [f'stress_test_{i}' for i in range(100)]
    
    @task(10)
    def continuous_load(self):
        """Continuous aggressive load."""
        portfolio_id = random.choice(self.portfolio_ids)
        self.client.post(
            f'/api/v1/assess/{portfolio_id}',
            json={'model_version': '1.0.0'},
            timeout=60
        )


# Load test scenarios
LOAD_TEST_SCENARIOS = {
    'baseline': {
        'description': 'Baseline performance test (100 users)',
        'user_class': RiskAssessmentUser,
        'users': 100,
        'spawn_rate': 10,
        'duration_seconds': 600,
    },
    'cache_validation': {
        'description': 'Cache effectiveness validation (50 users)',
        'user_class': CacheValidationUser,
        'users': 50,
        'spawn_rate': 5,
        'duration_seconds': 300,
    },
    'stress_test': {
        'description': 'Stress test with aggressive load (300+ users)',
        'user_class': StressTestUser,
        'users': 300,
        'spawn_rate': 30,
        'duration_seconds': 900,
    },
    'soak_test': {
        'description': 'Long-running soak test (100 users, 1 hour)',
        'user_class': RiskAssessmentUser,
        'users': 100,
        'spawn_rate': 5,
        'duration_seconds': 3600,
    },
}

# Expected performance benchmarks
PERFORMANCE_TARGETS = {
    'baseline': {
        'p50_latency_ms': 100,
        'p95_latency_ms': 300,
        'p99_latency_ms': 500,
        'throughput_rps': 300,
        'error_rate_percent': 0.1,
    },
    'after_optimization': {
        'p50_latency_ms': 30,
        'p95_latency_ms': 80,
        'p99_latency_ms': 150,
        'throughput_rps': 500,
        'error_rate_percent': 0.05,
    },
}

if __name__ == '__main__':
    print('Load Test Configuration')
    print('=' * 50)
    for scenario, config in LOAD_TEST_SCENARIOS.items():
        print(f"\n{scenario.upper()}:")
        print(f"  {config['description']}")
        print(f"  Users: {config['users']}")
        print(f"  Duration: {config['duration_seconds']}s")
