prometheus_setup_guide.md# Prometheus Integration Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install prometheus-client
```

### 2. Add Middleware to FastAPI (in app.py)
```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Request
from fastapi.responses import Response
import time

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency (seconds)',
    labelnames=['method', 'endpoint', 'status'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0)
)

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    labelnames=['method', 'endpoint', 'status']
)

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    method, endpoint = request.method, request.url.path
    start = time.time()
    try:
        response = await call_next(request)
        status = response.status_code
    except:
        status = 500
        raise
    finally:
        duration = time.time() - start
        http_request_duration_seconds.labels(
            method=method, endpoint=endpoint, status=status
        ).observe(duration)
        http_requests_total.labels(
            method=method, endpoint=endpoint, status=status
        ).inc()
    return response

@app.get("/metrics")
def metrics():
    from prometheus_client import generate_latest
    return Response(generate_latest(), media_type="text/plain")
```

### 3. Start Prometheus
```bash
docker-compose up prometheus -d
```

Prometheus: http://localhost:9090

### 4. View Metrics
HTTP Metrics: http://localhost:8000/metrics

### 5. Query in Prometheus
- P95 Latency: `histogram_quantile(0.95, http_request_duration_seconds_bucket)`
- Requests/sec: `rate(http_requests_total[1m])`
- Error Rate: `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100`
