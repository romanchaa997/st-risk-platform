# Monitoring Setup Guide for st-risk-platform

## 1. Prometheus Configuration

### prometheus.yml
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'

  - job_name: 'clickhouse'
    static_configs:
      - targets: ['localhost:8123']
    metrics_path: '/metrics'
```

## 2. Grafana Dashboards

### Key Metrics Dashboard
- P50/P95/P99 Latency (FastAPI endpoints)
- Request throughput (req/s)
- Error rate percentage
- CPU/Memory/Disk usage
- ClickHouse query response times
- Cache hit ratio

## 3. ELK Stack Setup

### Filebeat Configuration
```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/fastapi/*.log
    - /var/log/clickhouse/*.log

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "st-risk-platform-%{+yyyy.MM.dd}"
```

## 4. Alert Rules

- P95 latency > 500ms: warning
- Error rate > 1%: critical
- CPU > 80%: warning
- Memory > 85%: critical
- Disk > 90%: critical
- Cache hit ratio < 70%: warning

## 5. Log Aggregation

### JSON Logging Format
```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'trace_id': getattr(record, 'trace_id', None)
        }
        return json.dumps(log_data)
```

---
**Status**: Production Ready
**Last Updated**: December 26, 2025
