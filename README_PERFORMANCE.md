# st-risk-platform Performance Optimization

## Overview

This document summarizes the comprehensive 6-week performance optimization initiative for st-risk-platform, targeting 3-5x throughput improvement and 50-70% reduction in response times.

## Quick Links

- **[Performance Roadmap](monitoring/PERFORMANCE_OPTIMIZATION_ROADMAP.md)** - Complete optimization strategy and timeline
- **[Integration Guide](INTEGRATION_GUIDE.md)** - Step-by-step instructions for implementing optimizations
- **[SLA Document](docs/SLA.md)** - Service level agreements and performance targets
- **[Monitoring Setup](monitoring/prometheus_setup_guide.md)** - Prometheus and Grafana configuration

## 6 Optimization Components

### 1. PERF-1: SLA & Documentation
- Service level agreements with p99 latency targets (<150ms)
- Baseline performance benchmarking
- Alert thresholds configuration

**Files**: `docs/SLA.md`

### 2. PERF-2: Prometheus & Grafana Integration
- Request rate, latency, and error tracking
- Real-time performance visualization
- Alert rules and dashboards

**Files**: 
- `monitoring/prometheus.yml`
- `monitoring/app_fastapi_prometheus_integration.py`
- `monitoring/grafana_dashboard.json`
- `monitoring/prometheus_setup_guide.md`

### 3. PERF-3: Redis Caching Strategy
- RedisCacheManager with connection pooling
- @cache_result decorator for automatic caching
- Multi-tier TTL configuration (3600s for models, 300s for metrics)

**Files**: `monitoring/redis_cache_strategy.py`

**Expected Impact**:
- 60-70% reduction in model inference calls
- 40-50% faster dashboard loads
- 30% reduction in ClickHouse load

### 4. PERF-4: ClickHouse Optimization
- Primary key and partition optimization
- Skip indexes for fast filtering
- Projection-based materialized views
- Column compression with advanced codecs

**Files**: `monitoring/clickhouse_optimization.sql`

**Expected Impact**:
- 50-70% query performance improvement
- 40% reduction in storage space
- 30-40% less memory usage

### 5. PERF-5: Database Connection Pooling
- ClickHouse connection pool (10 connections)
- Async PostgreSQL pool (asyncpg, 5-20 connections)
- Redis connection pooling
- Automatic health checks and retry logic

**Files**: `monitoring/connection_pooling.py`

**Expected Impact**:
- 40-50% reduction in connection overhead
- Better resource utilization
- Improved response times under load

### 6. PERF-6: Async Request Processing
- AsyncTaskQueue with semaphore-based concurrency
- BatchProcessor for efficient bulk operations
- RiskAssessmentBatchProcessor for parallel portfolio assessment
- ParallelDataFetcher for concurrent data sourcing
- RateLimiter and RequestMetrics for monitoring

**Files**: `monitoring/async_request_processing.py`

**Expected Impact**:
- 3-5x throughput increase
- 50-70% latency reduction
- Handle 10x concurrent requests

## Performance Targets

### Before Optimization
- Throughput: 100 req/s
- API Response Time: 200-500ms
- Model Inference: 5-10s
- Dashboard Load: 2-3s
- CPU Utilization: 70-80%

### After Optimization
- Throughput: 300-500 req/s
- API Response Time: 50-100ms
- Model Inference: 1-2s
- Dashboard Load: 0.5-1s
- CPU Utilization: 40-50%

## Getting Started

### 1. Installation
```bash
pip install -r requirements.txt
pip install redis prometheus-client asyncpg locust pytest
```

### 2. Setup Infrastructure
```bash
docker-compose -f docker-compose.yml up -d redis prometheus grafana clickhouse
```

### 3. Apply Database Optimizations
```bash
clickhouse-client -h clickhouse -f monitoring/clickhouse_optimization.sql
```

### 4. Integrate Components
Follow the [Integration Guide](INTEGRATION_GUIDE.md) for step-by-step instructions

### 5. Run Tests
```bash
# Integration tests
pytest tests/test_performance_integration.py -v

# Load testing
locust -f tests/load_test_config.py --host=http://localhost:8000 --users=100
```

## Monitoring & Validation

### Metrics to Track
- **Cache Hit Rate**: Target >60%
- **p99 Latency**: Target <150ms
- **Error Rate**: Target <0.1%
- **Connection Pool Utilization**: Target <80%
- **Throughput**: Target 300+ req/s

### Grafana Dashboards
- Import `monitoring/grafana_dashboard.json` for visualization
- Monitor: Request latency, cache effectiveness, database performance

### Load Testing
```bash
# Baseline (100 users)
locust -f tests/load_test_config.py --users=100 --spawn-rate=10 --run-time=10m

# Stress test (300+ users)
locust -f tests/load_test_config.py --users=300 --spawn-rate=30 --run-time=15m
```

## Documentation

- `monitoring/` - All optimization components and configurations
- `tests/` - Integration tests and load testing scenarios
- `docs/` - SLA and service documentation
- `INTEGRATION_GUIDE.md` - Detailed integration instructions
- `monitoring/PERFORMANCE_OPTIMIZATION_ROADMAP.md` - Complete technical roadmap

## Support

For implementation questions, refer to:
1. [Integration Guide](INTEGRATION_GUIDE.md)
2. [Performance Roadmap](monitoring/PERFORMANCE_OPTIMIZATION_ROADMAP.md)
3. Individual component files in `monitoring/` folder
