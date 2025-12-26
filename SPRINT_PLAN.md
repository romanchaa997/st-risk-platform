# SPRINT PLAN: Performance Optimization (4 nedele)

## Nedelya 1: SLA & Observability

### Dan 1-2: SLA Definition (PERF-1)
- [ ] Meeting sa stakeholder-ima za SLA targets
- [ ] Definisanje P95 latency < 200-300ms
- [ ] Definisanje error rate < 0.1%
- [ ] Dokumentacija u `docs/SLA.md`

### Dan 3-5: APM & Dashboards (PERF-2)
- [ ] Install Prometheus + Grafana
- [ ] Integrate FastAPI sa prometheus_client
- [ ] Create Grafana dashboards (P50/P95/P99 latency)
- [ ] Setup alerts za SLA breach
- [ ] Test monitoring sa manual requests

## Nedelya 2: Database & Caching

### Dan 6-7: ClickHouse Optimization (PERF-4)
- [ ] Analyze slow queries sa query logs
- [ ] Add proper indexes i primary keys
- [ ] Setup connection pooling (asyncpg/clickhouse-driver)
- [ ] Profile queries under load
- [ ] Target: Query P95 < 100ms

### Dan 8-10: Redis Caching (PERF-3)
- [ ] Setup Redis u docker-compose
- [ ] Implement cache-aside pattern za heavy operations
- [ ] Add TTL sa jitter (randomization)
- [ ] Implement cache stampede protection
- [ ] Monitor hit ratio (target > 70%)

## Nedelya 3: Code Optimization & Resilience

### Dan 11-13: Code Profiling (PERF-5)
- [ ] Profile hot code paths sa cProfile
- [ ] Remove O(n^2) algoritmi
- [ ] Optimize serialization/deserialization
- [ ] Maximize async I/O u FastAPI
- [ ] Target: 15%+ latency improvement

### Dan 14-15: Resilience (PERF-7)
- [ ] Add timeouts za ClickHouse/Redis calls
- [ ] Implement exponential backoff za retries
- [ ] Add circuit breaker za critical dependencies
- [ ] Create /health i /ready endpoints
- [ ] Test graceful degradation

## Nedelya 4: Scaling & Load Testing

### Dan 16-17: Scaling Setup (PERF-6)
- [ ] Setup Nginx/Traefik load balancer
- [ ] Configure docker-compose za multiple replicas
- [ ] Document scaling recommendations
- [ ] Setup timeouts i connection limits

### Dan 18-20: Load Testing
- [ ] Write load_test.py sa locust
- [ ] Test scenarios:
  - 100 concurrent users
  - 500 concurrent users
  - Peak load profile
- [ ] Verify P95 < 300ms under load
- [ ] Generate performance report
- [ ] Deploy lessons learned

## Future (Nedelya 5+): K8s Migration (PERF-8)
- [ ] Design K8s deployments
- [ ] Define custom metrics za HPA
- [ ] Plan backlog-based autoscaling
- [ ] Document migration path
