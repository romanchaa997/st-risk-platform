# st-risk-platform Performance Optimization Roadmap

## Executive Summary

Comprehensive 6-week performance optimization initiative targeting 3-5x throughput improvement and 50-70% reduction in response times for the st-risk-platform risk assessment system.

**Estimated Impact:**
- Throughput: 100 req/s → 300-500 req/s
- API Response Time: 200-500ms → 50-100ms
- Model Inference: 5-10s → 1-2s
- Dashboard Load: 2-3s → 0.5-1s
- Resource Utilization: 70-80% CPU → 40-50% CPU

---

## Week 1: Monitoring & Baseline (PERF-1 & PERF-2)

### PERF-1: Documentation & SLA Establishment
**Files:** `docs/SLA.md`, `monitoring/prometheus_setup_guide.md`
- Service Level Agreements for all endpoints
- Performance benchmarks and targets
- Prometheus metrics configuration
- SLA monitoring and alerting rules

**Deliverables:**
- SLA document with p99 latency targets
- Baseline metrics collection
- Alert thresholds configured

### PERF-2: Prometheus Integration
**Files:** `monitoring/prometheus.yml`, `monitoring/app_fastapi_prometheus_integration.py`, `monitoring/grafana_dashboard.json`
- Complete Prometheus scrape configuration
- FastAPI Prometheus metrics middleware
- Grafana dashboards for visualization
- Request rate, latency, and error tracking

**Implementation:**
```python
from prometheus_client import Counter, Histogram, Gauge

request_count = Counter('risk_platform_requests_total', 'Total requests')
request_duration = Histogram('risk_platform_request_duration_seconds', 'Request duration')
active_requests = Gauge('risk_platform_active_requests', 'Active requests')
```

---

## Week 2: Caching & Database Optimization (PERF-3 & PERF-4)

### PERF-3: Redis Caching Strategy
**File:** `monitoring/redis_cache_strategy.py`

**Implementation:**
- RedisCacheManager with connection pooling
- @cache_result decorator for automatic caching
- Risk model prediction caching (3600s TTL)
- Dashboard metrics caching (300s TTL)
- ClickHouse query result caching (1800s TTL)

**Expected Impact:**
- 60-70% reduction in model inference calls
- 40-50% faster dashboard loads
- 30% reduction in ClickHouse load

**Configuration:**
```yaml
Redis:
  host: redis
  port: 6379
  pool_size: 10
  default_ttl: 3600
```

### PERF-4: ClickHouse Query Optimization
**File:** `monitoring/clickhouse_optimization.sql`

**Key Optimizations:**
1. **Primary Key & Partitioning**
   - ORDER BY (portfolio_id, event_type, timestamp)
   - PARTITION BY toYYYYMMDD(timestamp)

2. **Skip Indexes**
   - Data skipping indexes for risk_score, status, portfolio_id
   - Bloom filters for categorical columns

3. **Projections (Materialized Views)**
   - portfolio_daily_stats: pre-aggregated by portfolio/date/event_type
   - hourly_portfolio_metrics: hourly aggregations

4. **Column Compression**
   - Dictionary encoding for strings
   - Gorilla codec for floats (risk_score)
   - DoubleDelta codec for timestamps

5. **Query Optimization Patterns**
   - Avoid SELECT *
   - Use aggregate functions in ClickHouse
   - Leverage approximate algorithms for large datasets

**Expected Impact:**
- 50-70% query performance improvement
- 40% reduction in storage space
- 30-40% less memory usage

---

## Week 3: Connection Management & Async (PERF-5 & PERF-6)

### PERF-5: Database Connection Pooling
**File:** `monitoring/connection_pooling.py`

**Pools Implemented:**
1. **ClickHouse Pool**
   - 10 pooled connections
   - Automatic health checks
   - Connection retry logic

2. **PostgreSQL Pool (async)**
   - asyncpg connection pool
   - 5-20 connection range
   - UTC timezone initialization

3. **Redis Pool**
   - Async redis connections
   - Health check mechanism
   - 10 max connections

**Expected Impact:**
- 40-50% reduction in connection overhead
- Better resource utilization
- Improved response times under load

**Usage:**
```python
pool_manager = ConnectionPoolManager()
await pool_manager.initialize_all()
async with pool_manager.clickhouse_pool.acquire() as conn:
    result = conn.execute(query)
```

### PERF-6: Async Request Processing
**File:** `monitoring/async_request_processing.py`

**Components:**
1. **AsyncTaskQueue**
   - Semaphore-based concurrency control
   - Max 20 concurrent tasks
   - Statistics tracking

2. **BatchProcessor**
   - Process items in batches (100 items/batch)
   - Concurrent processing within batches
   - Timeout handling

3. **RiskAssessmentBatchProcessor**
   - Specialized for portfolio assessments
   - Parallel portfolio evaluation
   - Error handling and retry logic

4. **ParallelDataFetcher**
   - Fetch from multiple sources concurrently
   - Dashboard metrics aggregation
   - Semi-parallel failure handling

5. **RateLimiter**
   - Request rate limiting (100 req/60s)
   - Backpressure handling
   - Token bucket algorithm

6. **RequestMetrics**
   - Request tracking (success/failure rates)
   - Latency percentiles (p50, p95, p99)
   - Real-time statistics

**Expected Impact:**
- 3-5x throughput increase
- 50-70% reduction in response times
- 10x concurrent request handling

**Usage Examples:**
```python
# Batch assessment
processor = RiskAssessmentBatchProcessor()
results = await processor.assess_portfolios(portfolio_ids)

# Parallel data fetching
fetcher = ParallelDataFetcher()
results = await fetcher.fetch_multiple([fetch_metrics, fetch_events, fetch_alerts])

# Async background tasks
@async_task
async def long_operation():
    # Long-running work
    pass
```

---

## Implementation Timeline

### Sprint 1 (Weeks 1-2)
- [x] PERF-1: SLA & Documentation
- [x] PERF-2: Prometheus & Grafana
- [x] PERF-3: Redis Caching
- [x] PERF-4: ClickHouse Optimization

### Sprint 2 (Weeks 3-4)
- [x] PERF-5: Connection Pooling
- [x] PERF-6: Async Processing
- [ ] Integration testing
- [ ] Load testing validation

### Sprint 3 (Weeks 5-6)
- [ ] Kubernetes Autoscaling (Future)
- [ ] Advanced monitoring
- [ ] Production deployment
- [ ] Performance regression testing

---

## Performance Metrics Dashboard

### Key Metrics to Monitor

**Request Metrics:**
- Request rate (req/s)
- Response time (p50, p95, p99)
- Error rate
- Success rate

**Database Metrics:**
- Query execution time
- Connection pool utilization
- Cache hit rate
- Data size and compression ratio

**System Metrics:**
- CPU utilization
- Memory usage
- Network I/O
- Disk I/O

### Grafana Dashboards
- `monitoring/grafana_dashboard.json` - Main performance dashboard
- Request latency breakdown
- Database performance analysis
- Cache effectiveness
- Resource utilization trends

---

## Testing & Validation

### Load Testing
```bash
# Use tests/load_test.py for validation
python tests/load_test.py --users 50 --duration 300
```

### Performance Benchmarks
- Baseline: Document current state
- Target: 3-5x improvement
- Regression: Alert on >10% performance degradation

### Metrics Validation
1. Compare p99 latency before/after
2. Validate cache hit rates (>60% expected)
3. Verify connection pool efficiency
4. Check async concurrency limits

---

## Deployment Checklist

- [ ] Load test passed (sustained 300+ req/s)
- [ ] Cache effectiveness validated (>60% hit rate)
- [ ] Connection pooling stable
- [ ] Async processing without errors
- [ ] Monitoring alerts configured
- [ ] SLA thresholds met
- [ ] Documentation updated
- [ ] Rollback plan prepared

---

## Future Optimizations (Future Backlog)

### Kubernetes Autoscaling (PERF-7)
- Horizontal Pod Autoscaling based on metrics
- Vertical Pod Autoscaling for resource optimization
- Custom metrics for risk assessment load

### Advanced Caching (PERF-8)
- Multi-level caching (L1: process, L2: Redis)
- Cache invalidation strategies
- Distributed cache with Redis Cluster

### API Gateway Optimization (PERF-9)
- Request deduplication
- Response compression (gzip)
- Circuit breakers and bulkheads

---

## References

- ClickHouse Docs: https://clickhouse.com/docs/
- Prometheus Documentation: https://prometheus.io/docs/
- FastAPI Performance: https://fastapi.tiangolo.com/
- Redis Caching: https://redis.io/
- Grafana: https://grafana.com/docs/
