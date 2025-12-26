# Troubleshooting Guide for st-risk-platform

This guide provides solutions for common issues encountered in production deployments and local development.

## High Latency Issues

### Problem: API Response Times > 500ms

**Symptoms:**
- Users report slow dashboard loads
- Monitoring shows p95 latency exceeding SLA
- CPU usage appears normal

**Diagnosis:**
```bash
# Check ClickHouse query performance
curl -s 'http://clickhouse:8123/' --data-binary '
SELECT query_duration_ms, query FROM system.query_log 
WHERE query_duration_ms > 500 
ORDER BY query_start_time DESC LIMIT 10'

# Check FastAPI application logs
docker logs st-risk-api | grep "duration"
```

**Solutions:**
1. **Check ClickHouse table size:**
   ```sql
   SELECT table, formatReadableSize(bytes_on_disk) as size
   FROM system.tables
   WHERE database != 'system'
   ORDER BY bytes_on_disk DESC;
   ```

2. **Optimize slow queries:**
   - Add indices to frequently filtered columns
   - Use query sampling with SAMPLE clause
   - Enable query cache: `SELECT ... FROM table SETTINGS use_query_cache=1`

3. **Check FastAPI worker pool:**
   ```bash
   # Verify Gunicorn is using multiple workers
   ps aux | grep gunicorn
   # Expected: --workers 8+ for multi-core systems
   ```

4. **Database connection pool:**
   - Verify max_connections in docker-compose.yml
   - Adjust FastAPI `pool_size` in database config
   - Use connection pooling with pgBouncer for PostgreSQL backends

## Memory Issues

### Problem: Container OOMKilled or Memory Leak

**Symptoms:**
- Docker container restarts frequently
- Memory usage grows continuously over hours
- Kubernetes pod evictions

**Diagnosis:**
```bash
# Monitor memory in real-time
docker stats --no-stream

# Check for memory leaks in FastAPI
python -m memory_profiler your_app.py

# ClickHouse memory usage
curl -s 'http://clickhouse:8123/' --data-binary \
  'SELECT user, formatReadableSize(memory_usage) as used 
   FROM system.processes'
```

**Solutions:**
1. **Increase container memory limit:**
   ```yaml
   # In docker-compose.yml
   services:
     st-risk-api:
       environment:
         - WORKERS=8
         - MAX_OVERFLOW=10
       deploy:
         resources:
           limits:
             memory: 2G
           reservations:
             memory: 1G
   ```

2. **Fix memory leaks in FastAPI:**
   - Use `functools.lru_cache` with maxsize parameter
   - Implement proper async cleanup in context managers
   - Use `/metrics` endpoint to monitor memory via Prometheus

3. **Optimize ClickHouse memory:**
   ```xml
   <!-- In ClickHouse config -->
   <config>
     <max_memory_usage>4000000000</max_memory_usage>
     <max_memory_usage_for_user>3000000000</max_memory_usage_for_user>
   </config>
   ```

## Database Connection Errors

### Problem: "FATAL: remaining connection slots are reserved"

**Symptoms:**
- Intermittent 502 Bad Gateway errors
- Connection pool exhausted messages
- Cascading failures under load

**Diagnosis:**
```bash
# Check active connections
curl -s 'http://clickhouse:8123/' --data-binary \
  'SELECT count(*) FROM system.processes'

# Monitor connection trends
watch -n 1 'docker exec postgres_container psql -U user -d db -c \
  "SELECT count(*) FROM pg_stat_activity"'
```

**Solutions:**
1. **Increase connection limits:**
   ```yaml
   # docker-compose.yml
   postgres:
     environment:
       - POSTGRES_INIT_ARGS=-c max_connections=200
   ```

2. **Implement connection pooling:**
   ```python
   # In FastAPI app
   from sqlalchemy import create_engine
   
   engine = create_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=40,
       pool_pre_ping=True,  # Validate connections
       pool_recycle=3600,   # Recycle after 1 hour
   )
   ```

3. **Monitor connection usage:**
   ```python
   # Add Prometheus metric
   from prometheus_client import Gauge
   
   connection_gauge = Gauge(
       'db_connections_active',
       'Active database connections'
   )
   ```

## ClickHouse Issues

### Problem: "Table not replicated" or Replication Lag

**Symptoms:**
- Data inconsistency between replicas
- Delayed risk calculations
- Replication lag > 60 seconds

**Diagnosis:**
```bash
# Check replication status
curl -s 'http://clickhouse:8123/' --data-binary \
  'SELECT replica_name, table, is_leader, absolute_delay 
   FROM system.replicas'

# Check replication queue
curl -s 'http://clickhouse:8123/' --data-binary \
  'SELECT * FROM system.replication_queue'
```

**Solutions:**
1. **Fix replication lag:**
   ```sql
   -- On lagged replica
   SYSTEM SYNC REPLICA table_name;
   
   -- Restart replication
   SYSTEM DROP REPLICA 'replica_name';
   SYSTEM ADD REPLICA 'replica_name';
   ```

2. **Increase replication threads:**
   ```xml
   <background_replication_pool_size>8</background_replication_pool_size>
   ```

3. **Monitor replication metrics:**
   ```python
   # Prometheus check
   - alert: ReplicationLagHigh
     expr: clickhouse_replication_delay > 60
   ```

## Network & Firewall Issues

### Problem: Service Cannot Reach ClickHouse/Database

**Symptoms:**
- "Connection refused" errors
- Timeout errors (>30s)
- Works locally but fails in Kubernetes

**Diagnosis:**
```bash
# Test connectivity
netstat -an | grep ESTABLISHED

# Check DNS resolution
nslookup clickhouse
dig clickhouse

# Test port connectivity
nc -zv clickhouse 8123
telnet clickhouse 8123
```

**Solutions:**
1. **Fix Docker networking:**
   ```bash
   # Verify container is in correct network
   docker network inspect st-risk-platform_default
   
   # Use service name, not IP address
   # Correct: clickhouse:8123
   # Wrong: 172.17.0.3:8123
   ```

2. **Configure Kubernetes networking:**
   ```yaml
   apiVersion: v1
   kind: NetworkPolicy
   metadata:
     name: st-risk-policy
   spec:
     podSelector:
       matchLabels:
         app: st-risk
     policyTypes:
     - Ingress
     - Egress
     ingress:
     - from:
       - podSelector:
           matchLabels:
             app: st-risk
   ```

3. **Check DNS in Kubernetes:**
   ```bash
   kubectl exec pod-name -- nslookup clickhouse.default.svc.cluster.local
   ```

## CPU Spikes

### Problem: CPU Usage Suddenly Increases to 100%

**Symptoms:**
- Application becomes unresponsive
- Timeouts on all requests
- Cascading failures

**Diagnosis:**
```bash
# Identify hot processes
top -b -n 1 | head -20

# Profile Python CPU usage
python -m cProfile -s cumulative your_app.py

# ClickHouse hot queries
curl -s 'http://clickhouse:8123/' --data-binary \
  'SELECT query, query_duration_ms FROM system.query_log 
   WHERE query_start_time > now() - interval 1 minute 
   ORDER BY query_duration_ms DESC LIMIT 10'
```

**Solutions:**
1. **Optimize hot queries:**
   - Add indices to WHERE clause columns
   - Use PREWHERE clause for filtering
   - Enable async_insert for high-volume writes

2. **Implement rate limiting:**
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   
   @app.get("/api/risk")
   @limiter.limit("100/minute")
   async def get_risk(request: Request):
       ...
   ```

3. **Scale horizontally:**
   - Add more FastAPI workers
   - Add more ClickHouse shards
   - Use Kubernetes HPA for auto-scaling

## Deployment Issues

### Problem: Deployment Stuck or Failing

**Symptoms:**
- Rolling update hangs
- Readiness probes fail
- Liveness probes constantly restarting pods

**Diagnosis:**
```bash
# Check deployment status
kubectl rollout status deployment/st-risk-api

# View pod events
kubectl describe pod pod-name

# Check logs
kubectl logs pod-name --all-containers=true --timestamps=true

# Check resource availability
kubectl top nodes
kubectl top pods
```

**Solutions:**
1. **Fix health check timeouts:**
   ```yaml
   livenessProbe:
     httpGet:
       path: /health
       port: 8000
     initialDelaySeconds: 30
     timeoutSeconds: 10
     periodSeconds: 10
     failureThreshold: 3
   ```

2. **Increase readiness grace period:**
   ```yaml
   readinessProbe:
     httpGet:
       path: /ready
       port: 8000
     initialDelaySeconds: 15
     timeoutSeconds: 5
     periodSeconds: 5
   ```

3. **Ensure sufficient resources:**
   ```yaml
   resources:
     requests:
       memory: "512Mi"
       cpu: "250m"
     limits:
       memory: "2Gi"
       cpu: "1000m"
   ```

## Monitoring & Alerts

### Key Metrics to Watch

1. **Application Metrics:**
   - Request latency (p50, p95, p99)
   - Error rate (4xx, 5xx)
   - Request throughput
   - Worker process count

2. **Database Metrics:**
   - Query latency
   - Replication lag
   - Insert rate
   - Connection count

3. **Infrastructure Metrics:**
   - CPU utilization
   - Memory usage
   - Disk I/O
   - Network bandwidth

### Recommended Alert Rules

```yaml
alerts:
  - name: HighLatency
    condition: p95_latency > 500ms
    duration: 5m
    severity: warning
  
  - name: HighErrorRate
    condition: error_rate > 1%
    duration: 5m
    severity: critical
  
  - name: ReplicationLag
    condition: replication_lag > 60s
    duration: 10m
    severity: warning
  
  - name: ConnectionPoolExhausted
    condition: active_connections / max_connections > 0.8
    duration: 5m
    severity: critical
```

## Performance Tuning Checklist

- [ ] Enable ClickHouse query cache
- [ ] Configure appropriate worker count
- [ ] Set connection pool size based on load
- [ ] Enable query profiling
- [ ] Configure log levels appropriately
- [ ] Set up monitoring and alerting
- [ ] Enable database replication
- [ ] Configure backup strategy
- [ ] Implement rate limiting
- [ ] Set up circuit breakers for external APIs

## Getting Help

For additional support:
1. Check application logs: `kubectl logs -f deployment/st-risk-api`
2. Check database logs: `docker logs st-risk-clickhouse`
3. Review monitoring dashboards in Grafana
4. Consult PERFORMANCE_CHECKLIST.md for optimization guidelines
5. Review DEPLOYMENT_GUIDE.md for deployment-specific issues
