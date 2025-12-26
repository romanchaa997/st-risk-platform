# Performance Checklist for st-risk-platform

**FastAPI + ClickHouse + Docker Optimization Guide**

---

## 1. FastAPI Optimization

### 1.1 Asynchronous Programming
- [ ] All I/O operations use `async/await` (database queries, API calls, file operations)
- [ ] Use `asyncio.gather()` for parallel requests
- [ ] Configure worker count: `uvicorn main:app --workers 4` (CPU cores count)
- [ ] Enable HTTP/2: Add `--http h2` flag

### 1.2 Request/Response Optimization
- [ ] Enable gzip compression: `from fastapi.middleware.gzip import GZIPMiddleware`
- [ ] Set appropriate response cache headers
- [ ] Use `response_model` only when needed (avoid over-validation)
- [ ] Compress large JSON responses (>1KB)

### 1.3 Connection Pooling
- [ ] ClickHouse connection pool size: 10-20 connections
- [ ] PostgreSQL connection pool: 5-10 per worker
- [ ] Redis connection pool: 5-10 connections
- [ ] Monitor pool exhaustion with `pool.size()` and `pool.free()`

### 1.4 Middleware & Rate Limiting
- [ ] Remove unnecessary middleware stack
- [ ] Implement rate limiting: 1000 req/min for public endpoints
- [ ] Add request timeout: 30s for external APIs, 5s for internal
- [ ] Use `slowapi` for rate limiting

---

## 2. ClickHouse Optimization

### 2.1 Table Design
- [ ] Use `MergeTree` family engines (preferred: `ReplacingMergeTree`)
- [ ] Set `ORDER BY` on frequently filtered columns
- [ ] Use `PARTITION BY` with time-based columns
- [ ] Keep row size < 1MB
- [ ] Prewarm tables with 100MB+ data for accurate benchmarking

### 2.2 Query Optimization
- [ ] Use column selection (avoid `SELECT *`)
- [ ] Index hot columns: `risk_id`, `timestamp`, `status`
- [ ] Use `PREWHERE` for early filtering (30-40% speedup)
- [ ] Leverage `PRIMARY KEY` for partition pruning
- [ ] Sample large queries: `SAMPLE 0.1` for testing

### 2.3 Aggregation & Data Compression
- [ ] Set `compression` codec: `LZ4` for speed, `ZSTD` for ratio
- [ ] Pre-aggregate using `SummingMergeTree` when possible
- [ ] Use `GROUP BY` with `ORDER BY` for better compression
- [ ] Archive old data: move to separate table after 90 days

### 2.4 ClickHouse Server Config
- [ ] `max_concurrent_queries`: 100-200
- [ ] `max_memory_usage`: 20GB (if 64GB RAM available)
- [ ] `max_insert_threads`: CPU count
- [ ] Enable `readonly` mode for read-heavy replicas

---

## 3. Docker & Container Optimization

### 3.1 Image Building
- [ ] Use multi-stage builds to reduce image size
- [ ] Base image: `python:3.11-slim` (65MB vs 300MB for standard)
- [ ] Cache layers: Put frequently changing code last
- [ ] Remove build dependencies in final stage
- [ ] Final image size target: < 500MB

### 3.2 Container Runtime
- [ ] Memory limit: FastAPI worker 512MB, ClickHouse 16GB
- [ ] CPU limit: 2-4 cores per service
- [ ] Enable healthchecks every 10s
- [ ] Use read-only root filesystem where possible
- [ ] Log rotation: max 10MB per file, 3 files kept

### 3.3 Docker Compose Configuration
- [ ] Service startup order: PostgreSQL -> ClickHouse -> FastAPI
- [ ] Use named volumes for persistence
- [ ] Set `restart: unless-stopped` for production
- [ ] Network mode: `bridge` (not `host`)
- [ ] Resource constraints on all services

---

## 4. Database Optimization

### 4.1 PostgreSQL (if used)
- [ ] Connection pooling: PgBouncer with 25 connections
- [ ] WAL config: `wal_buffers = 16MB`
- [ ] `shared_buffers = 1/4 RAM` (e.g., 16GB for 64GB system)
- [ ] Index hot columns: `CREATE INDEX idx_user_id ON table(user_id)`
- [ ] Regular VACUUM: every 6 hours

### 4.2 Redis Cache
- [ ] Cache TTL: 1 hour for user sessions, 15 min for computed data
- [ ] Memory limit: 4GB, eviction policy `allkeys-lru`
- [ ] Enable AOF persistence: `appendonly yes`
- [ ] Monitor cache hit ratio (target > 80%)

---

## 5. Monitoring & Observability

### 5.1 Metrics to Track
- [ ] Response time: P50, P95, P99 (target: <100ms, <500ms, <2s)
- [ ] Error rate: < 0.1%
- [ ] Database query time: < 50ms average
- [ ] CPU usage: < 70% during peak
- [ ] Memory usage: < 80% of limit

### 5.2 Logging
- [ ] Structured JSON logging (not plain text)
- [ ] Log levels: ERROR, WARN, INFO only (no DEBUG in prod)
- [ ] Centralize logs: ELK stack or cloud logging
- [ ] Log rotation: 100MB per file, 7 days retention

### 5.3 Profiling
- [ ] Profile top endpoints: `pyinstrument` or `cProfile`
- [ ] Database query logging: set `echo=True` in dev only
- [ ] Track slow queries (>500ms) in ClickHouse
- [ ] Memory profiling: `memory_profiler` for leak detection

---

## 6. Deployment Checklist

### 6.1 Pre-Deployment
- [ ] Load test: 1000 concurrent users for 5 minutes
- [ ] Database backup: full backup + 7 days of WAL
- [ ] Rollback plan: documented and tested
- [ ] Health check endpoints: `/health` returns 200

### 6.2 Gradual Rollout
- [ ] Canary deployment: 5% traffic for 24 hours
- [ ] Monitor error rate, latency, resources
- [ ] Stage 1: 25% (monitor 6 hours)
- [ ] Stage 2: 50% (monitor 6 hours)
- [ ] Stage 3: 100% (monitor 24 hours)

### 6.3 Post-Deployment
- [ ] Verify all metrics are healthy
- [ ] Check error logs for exceptions
- [ ] Compare response time before/after
- [ ] Database size growth is normal

---

## Future: K8s/HPA/Backlog-Based Autoscaling Roadmap

### Phase 1: Kubernetes Migration (Weeks 1-4)
- [ ] Convert docker-compose to Helm charts
- [ ] Set up EKS/GKE/AKS cluster
- [ ] Migrate persistent volumes to cloud storage (EBS/GCP Persistent Disk)
- [ ] Configure service mesh (Istio optional, Linkerd recommended)
- [ ] Implement network policies

### Phase 2: Horizontal Pod Autoscaling (Weeks 5-8)
- [ ] Enable HPA based on CPU (target: 70%)
- [ ] Add custom metrics: request latency, queue depth
- [ ] Set min replicas: 3, max replicas: 10
- [ ] Test autoscaling: load generation script

### Phase 3: Backlog-Based Autoscaling (Weeks 9-12)
- [ ] Implement job queue (Kafka/RabbitMQ/AWS SQS)
- [ ] Scale workers based on queue depth:
  - [ ] Queue depth < 100: 2 replicas
  - [ ] Queue depth 100-500: 4 replicas
  - [ ] Queue depth > 500: 8+ replicas
- [ ] Implement graceful shutdown (30s drain period)
- [ ] Setup alerting: queue depth > 1000 triggers PagerDuty

### Phase 4: Advanced Features (Weeks 13+)
- [ ] Implement predictive scaling based on historical load patterns
- [ ] Cost optimization: spot instances for non-critical tasks
- [ ] Multi-region failover: active-active setup
- [ ] Service-to-service load balancing with service mesh

---

## Performance Targets

| Metric | Current | Target | Deadline |
|--------|---------|--------|----------|
| API Response Time (P95) | 500ms | 200ms | Week 2 |
| Database Query Time | 100ms | 50ms | Week 1 |
| Error Rate | 0.5% | 0.05% | Week 1 |
| CPU Usage (peak) | 85% | 70% | Week 2 |
| Memory Usage (peak) | 90% | 75% | Week 2 |
| Throughput | 100 req/s | 500 req/s | Week 3 |
| Cache Hit Ratio | 65% | 85% | Week 1 |
| Concurrent Users | 50 | 1000+ | Week 4 |

---

## Quick Start

### 1. Apply FastAPI optimizations:
```bash
# Update requirements.txt
pip install fastapi[all] uvicorn[standard] slowapi aioredis

# Run with optimized settings
uvicorn main:app --workers 4 --loop uvloop --http h2
```

### 2. Optimize ClickHouse:
```bash
# Connect and check configuration
clickhouse-client -h localhost -q "SELECT * FROM system.settings WHERE name IN ('max_concurrent_queries', 'max_memory_usage')"

# Run performance check
clickhouse-client -f monitoring/clickhouse_optimization.sql
```

### 3. Check container health:
```bash
docker-compose logs -f
docker stats  # Monitor CPU, memory, network
```

---

## Need Help?

1. **Integration issues**: Check `INTEGRATION_GUIDE.md`
2. **Deployment issues**: Check `DEPLOYMENT_GUIDE.md`
3. **Performance questions**: Check `FINAL_STATUS.md`
4. **Technical details**: Check `monitoring/PERFORMANCE_OPTIMIZATION_ROADMAP.md`
5. **What changed**: Check `CHANGELOG.md`

---

**Status**: Ready for Production
**Created**: December 26, 2025

Let's go faster!
