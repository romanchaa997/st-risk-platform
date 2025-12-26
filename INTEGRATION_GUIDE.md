# Performance Optimization Integration Guide

How to integrate PERF-1 through PERF-6 optimization components into st-risk-platform.

## Quick Start

### 1. Install Dependencies
```bash
pip install redis prometheus-client asyncpg locust pytest
```

## Component Integration

### PERF-1: SLA & Monitoring
**File**: `docs/SLA.md`
- Define your service level agreements
- Set p99 latency targets (aim for <150ms)
- Establish error rate thresholds (<0.1%)

### PERF-2: Prometheus & Grafana

**Setup Prometheus**:
```yaml
# Start Prometheus with monitoring/prometheus.yml
docker run -d \
  -p 9090:9090 \
  -v $(pwd)/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

**Integrate with FastAPI**:
```python
from monitoring.app_fastapi_prometheus_integration import (
    setup_prometheus_metrics,
    middleware_metrics
)

from fastapi import FastAPI
app = FastAPI()

# Add Prometheus middleware
setup_prometheus_metrics(app)

# Or use decorator
from fastapi import APIRouter
router = APIRouter()

@router.post('/assess/{portfolio_id}')
@middleware_metrics
async def assess_portfolio(portfolio_id: str):
    # Your code here
    pass
```

**Setup Grafana**:
```bash
docker run -d \
  -p 3000:3000 \
  --env GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana

# Import monitoring/grafana_dashboard.json
```

### PERF-3: Redis Caching

**Install Redis**:
```bash
docker run -d -p 6379:6379 redis:latest
```

**Integrate into your code**:
```python
from monitoring.redis_cache_strategy import (
    RedisCacheManager,
    cache_result,
    RiskModelCache,
    MetricsCache
)

# Initialize once at startup
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    cache_manager = RedisCacheManager(
        host='redis',
        port=6379,
        pool_size=10,
        default_ttl=3600
    )
    yield
    # Shutdown
    pass

app = FastAPI(lifespan=lifespan)

# Use caching decorator
@app.post('/assess/{portfolio_id}')
@cache_result(ttl=3600, key_prefix='risk_')
async def assess_portfolio(portfolio_id: str):
    # Long operation - will be cached
    return risk_score

# Or use specialized cache classes
@app.get('/dashboard/{portfolio_id}')
async def get_dashboard(portfolio_id: str):
    # Use MetricsCache with 5-minute TTL
    metrics = await MetricsCache.get_dashboard_metrics(
        portfolio_id,
        timeframe='7d'
    )
    return metrics
```

### PERF-4: ClickHouse Optimization

**Apply optimizations**:
```bash
# Connect to ClickHouse
clickhouse-client --host=clickhouse --port=9000

# Run SQL from monitoring/clickhouse_optimization.sql
-- Set primary key and partitioning
ALTER TABLE risk_events
MODIFY ORDER BY (portfolio_id, event_type, timestamp);

-- Add indexes
ALTER TABLE risk_events
ADD INDEX event_risk_score risk_score TYPE minmax GRANULARITY 4;

-- Create materializations
ALTER TABLE risk_events
ADD PROJECTION portfolio_daily_stats (...)
```

### PERF-5: Connection Pooling

**Integrate pools**:
```python
from monitoring.connection_pooling import (
    ConnectionPoolManager,
    ClickHousePool,
    AsyncPostgresPool,
    RedisConnectionPool
)

from fastapi import FastAPI

pool_manager = ConnectionPoolManager()

app = FastAPI()

@app.on_event('startup')
async def startup():
    await pool_manager.initialize_all()
    # Check health
    health = await pool_manager.health_check_all()
    print(f'Pool health: {health}')

@app.on_event('shutdown')
async def shutdown():
    await pool_manager.close_all()

# Use in endpoints
@app.post('/assess/{portfolio_id}')
async def assess_portfolio(portfolio_id: str):
    async with pool_manager.clickhouse_pool.acquire() as conn:
        result = conn.execute(f'SELECT * FROM risk_events WHERE portfolio_id = %s', [portfolio_id])
        return result
```

### PERF-6: Async Request Processing

**Use async patterns**:
```python
from monitoring.async_request_processing import (
    RiskAssessmentBatchProcessor,
    ParallelDataFetcher,
    RateLimiter,
    async_task
)

@app.post('/assess/batch')
async def batch_assess(portfolio_ids: List[str]):
    processor = RiskAssessmentBatchProcessor()
    results = await processor.assess_portfolios(portfolio_ids)
    return results

@app.get('/dashboard/{portfolio_id}')
async def get_dashboard(portfolio_id: str):
    fetcher = ParallelDataFetcher(max_concurrent=10)
    metrics, events, alerts = await fetcher.fetch_multiple([
        lambda: fetch_metrics(portfolio_id),
        lambda: fetch_events(portfolio_id),
        lambda: fetch_alerts(portfolio_id)
    ])
    return {'metrics': metrics, 'events': events, 'alerts': alerts}

@app.post('/process')
async def process_with_background_task(
    data: dict,
    background_tasks: BackgroundTasks
):
    @async_task
    async def long_operation():
        # Process data
        await asyncio.sleep(5)
        return 'completed'
    
    background_tasks.add_task(long_operation)
    return {'status': 'processing'}
```

## Testing

### Run Integration Tests
```bash
pytest tests/test_performance_integration.py -v
```

### Load Testing
```bash
# Baseline test with 100 users
locust -f tests/load_test_config.py \
  --host=http://localhost:8000 \
  --users=100 \
  --spawn-rate=10 \
  --run-time=10m

# Cache validation with 50 users
locust -f tests/load_test_config.py \
  --host=http://localhost:8000 \
  --csv=results/cache_validation \
  --users=50 \
  --spawn-rate=5 \
  --run-time=5m

# Stress test with 300+ users
locust -f tests/load_test_config.py \
  --host=http://localhost:8000 \
  --users=300 \
  --spawn-rate=30 \
  --run-time=15m
```

## Docker Compose Setup

Create `docker-compose.override.yml`:
```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## Monitoring

### Key Metrics to Track

**Cache Metrics**:
- `redis_cache_hits` - Successful cache retrievals
- `redis_cache_misses` - Cache misses
- `cache_hit_rate` - Target: >60%

**Database Metrics**:
- `clickhouse_query_time_ms` - Query latency
- `connection_pool_utilization` - Target: <80%
- `connection_pool_wait_time_ms` - Target: <50ms

**Request Metrics**:
- `http_request_duration_seconds` - p50, p95, p99
- `http_requests_total` - By endpoint
- `http_request_errors_total` - By status code

### Grafana Dashboards

Import `monitoring/grafana_dashboard.json` to see:
- Request latency trends
- Cache effectiveness
- Database performance
- System resource usage

## Troubleshooting

### Redis Connection Issues
```python
from monitoring.redis_cache_strategy import RedisCacheManager
manager = RedisCacheManager()
try:
    manager.redis_client.ping()
    print('Redis connected')
except Exception as e:
    print(f'Redis error: {e}')
```

### ClickHouse Performance
```sql
-- Check slow queries
SELECT query_start_time, query_duration_ms, query
FROM system.query_log
WHERE query_duration_ms > 1000
ORDER BY query_duration_ms DESC
LIMIT 10;
```

### Connection Pool Exhaustion
```python
health = await pool_manager.health_check_all()
if not health['clickhouse']:
    print('ClickHouse pool unhealthy - reinitializing')
    await pool_manager.close_all()
    await pool_manager.initialize_all()
```

## Next Steps

1. ✅ Integrate PERF-1 to PERF-6 components
2. ✅ Run integration tests
3. ✅ Perform load testing with baseline metrics
4. ⬜ Compare before/after performance
5. ⬜ Deploy to staging environment
6. ⬜ Monitor performance improvements
7. ⬜ Roll out to production with canary deployment

## References

- Monitoring folder: `monitoring/`
- Test files: `tests/`
- Roadmap: `monitoring/PERFORMANCE_OPTIMIZATION_ROADMAP.md`
- SLA: `docs/SLA.md`
