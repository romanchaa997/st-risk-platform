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
