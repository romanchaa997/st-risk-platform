app_fastapi_prometheus_integration.py# FastAPI Prometheus Integration Example
# Copy this code into your app.py to enable metrics collection

from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
import time
import logging

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="st-risk-platform")

# ===== PROMETHEUS METRICS =====
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency (seconds)',
    labelnames=['method', 'endpoint', 'status'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    labelnames=['method', 'endpoint', 'status']
)

requests_in_progress = Histogram(
    'requests_in_progress',
    'Requests currently being processed',
    labelnames=['method', 'endpoint']
)

# ===== MIDDLEWARE =====
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    """Track HTTP requests and expose metrics to Prometheus."""
    method = request.method
    endpoint = request.url.path
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        logger.error(f"Request error: {e}")
        raise
    finally:
        # Record metrics
        duration = time.time() - start_time
        
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint,
            status=status_code
        ).observe(duration)
        
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status_code
        ).inc()
    
    return response

# ===== METRICS ENDPOINT =====
@app.get("/metrics", tags=["monitoring"])
def metrics():
    """Expose Prometheus metrics."""
    return Response(generate_latest(REGISTRY), media_type="text/plain")

# ===== HEALTH CHECKS =====
@app.get("/health", tags=["health"])
def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "st-risk-platform"}

@app.get("/ready", tags=["health"])
def ready():
    """Readiness check endpoint."""
    return {"ready": True, "service": "st-risk-platform"}

# ===== ADD YOUR ENDPOINTS BELOW =====
# @app.post("/api/risk/assess")
# @app.get("/api/features")
# @app.post("/api/model/predict")
# etc...

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
