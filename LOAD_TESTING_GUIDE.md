# Load Testing Guide

## k6 Script

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 100,
  duration: '30s',
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['<0.1'],
  },
};

export default function() {
  const baseUrl = 'http://localhost:8000';
  
  // Test risk assessment endpoint
  let res = http.post(`${baseUrl}/api/risk/assess`, {
    risk_id: '123',
    metrics: [1, 2, 3]
  });
  
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  sleep(1);
}
```

## Locust Script

```python
from locust import HttpUser, task, between

class RiskPlatformUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def assess_risk(self):
        self.client.post('/api/risk/assess', json={
            'risk_id': '123',
            'metrics': [1, 2, 3]
        })
    
    @task
    def get_features(self):
        self.client.get('/api/features')
```

## Running Tests

```bash
# k6
k6 run load_test.js

# Locust
locust -f locustfile.py --host=http://localhost:8000
```

---
**Status**: Production Ready
