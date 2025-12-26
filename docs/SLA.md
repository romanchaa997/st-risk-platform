# Service Level Agreement (SLA) - st-risk-platform

**Version**: 1.0  
**Last Updated**: 2025-12-26  
**Status**: Active

## Executive Summary

This document defines the Service Level Objectives (SLOs) for the st-risk-platform risk assessment system. These targets ensure consistent, reliable service delivery to end users.

## Latency Targets

### P50 (Median Latency)
- **Target**: < 100 ms
- **Scope**: All critical endpoints (risk assessment, features, prediction)
- **Measurement**: 50th percentile of request duration

### P95 (95th Percentile Latency) - PRIMARY SLO
- **Target**: < 250 ms (preferred) / < 300 ms (acceptable)
- **Scope**: All critical endpoints
- **Measurement**: 95th percentile of request duration
- **Why**: Ensures most users experience acceptable response times

### P99 (99th Percentile Latency)
- **Target**: < 500 ms
- **Scope**: All critical endpoints
- **Measurement**: 99th percentile of request duration
- **Why**: Identifies tail latency issues affecting a small percentage of users

## Error Rate Targets

### Overall Service Error Rate
- **Target**: < 0.1% (1 error per 1000 requests)
- **Measurement**: (failed requests) / (total requests)
- **Excluded**: Client errors (4xx) - counted separately

### By Endpoint

| Endpoint | Error Rate |
|----------|------------|
| POST /api/risk/assess | < 0.05% |
| GET /api/features | < 0.05% |
| POST /api/model/predict | < 0.1% |
| GET /api/health | < 0.01% |

## Resource Utilization Targets

### CPU
- **Peak Acceptable**: 85%
- **Average Target**: 60%
- **Scope**: Per container/instance

### Memory (RAM)
- **Peak Acceptable**: 80%
- **Average Target**: 50%
- **Scope**: Per container/instance

### ClickHouse Query Performance
- **P95 Query Latency**: < 100 ms
- **Max Concurrent Queries**: 100
- **Slow Query Threshold**: > 500 ms

## Availability Targets

### Monthly Uptime
- **Target**: 99.9% (max 43 minutes downtime per month)
- **Measurement**: Service health checks

## Measurement & Monitoring

### Tools
- **APM**: Prometheus + Grafana (to be implemented in PERF-2)
- **Logging**: Structured logs with trace_id
- **Alerting**: Automated alerts on SLO breaches

### Reporting
- **Dashboard**: Real-time SLO compliance dashboard
- **Weekly Report**: SLO performance summary
- **Monthly Review**: SLA retrospective and adjustments

## Compliance & Escalation

### Alert Thresholds
1. **Warning**: SLO at 80% compliance → notify team lead
2. **Critical**: SLO at 50% compliance → escalate to engineering manager
3. **Outage**: < 50% compliance or < 95% uptime → incident response

## Revision History

| Version | Date | Changes |
|---------|------|----------|
| 1.0 | 2025-12-26 | Initial SLA definition |

---

**Approved By**: Engineering Team  
**Next Review**: 2026-01-26
