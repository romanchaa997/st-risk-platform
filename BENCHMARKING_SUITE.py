#!/usr/bin/env python3

import time
import statistics
import requests

class PerformanceBenchmark:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
    
    def benchmark_endpoint(self, method, endpoint, payload=None, iterations=100):
        times = []
        for _ in range(iterations):
            start = time.time()
            if method == 'GET':
                requests.get(f'{self.base_url}{endpoint}')
            elif method == 'POST':
                requests.post(f'{self.base_url}{endpoint}', json=payload)
            elapsed = time.time() - start
            times.append(elapsed * 1000)
        
        return {
            'endpoint': endpoint,
            'p50': statistics.median(times),
            'p95': sorted(times)[int(len(times) * 0.95)],
            'p99': sorted(times)[int(len(times) * 0.99)],
            'avg': statistics.mean(times),
            'min': min(times),
            'max': max(times),
        }
    
    def run_suite(self):
        print('Running Performance Benchmarks...')
        result = self.benchmark_endpoint('POST', '/api/risk/assess',
            {'risk_id': '123', 'metrics': [1, 2, 3]})
        print(f'Risk Assessment P95: {result["p95"]:.2f}ms')

if __name__ == '__main__':
    benchmark = PerformanceBenchmark()
    benchmark.run_suite()
