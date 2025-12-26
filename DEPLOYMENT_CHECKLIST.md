# Deployment Checklist

## Pre-Deployment (Week 1)

### Infrastructure Preparation
- [ ] Provision cloud resources (EKS/GKE/AKS cluster)
- [ ] Setup networking: VPC, subnets, security groups
- [ ] Configure DNS and load balancer
- [ ] Setup container registry (ECR/GCR/ACR)
- [ ] Create RDS PostgreSQL instance (multi-AZ)
- [ ] Create ClickHouse cluster (min 3 nodes)
- [ ] Create Redis cluster (4GB memory)

### Application Preparation
- [ ] Code review completed
- [ ] All tests passing (unit, integration, performance)
- [ ] Load testing completed (target: 1000 concurrent users)
- [ ] Security scanning (SAST/DAST) passed
- [ ] Database migrations tested and documented

## Deployment Phase (Week 2-3)

### Canary Deployment (5% traffic, 24 hours)
```bash
kubectl set image deployment/fastapi \
  fastapi=registry.io/st-risk-platform:v1.0.0
kubectl set image deployment/model-service \
  model=registry.io/model-service:v1.0.0
```

### Monitoring Canary
- [ ] Error rate < 0.1% (target)
- [ ] P95 latency < 500ms (target)
- [ ] No database errors
- [ ] Cache hit ratio > 70%

### Gradual Rollout
1. **Stage 1** (25% traffic, 6 hours)
   - [ ] Metrics healthy
   - [ ] No error spikes
   - [ ] Database connections stable

2. **Stage 2** (50% traffic, 6 hours)
   - [ ] CPU utilization < 70%
   - [ ] Memory usage < 75%
   - [ ] Network stable

3. **Stage 3** (100% traffic, 24 hours)
   - [ ] Full monitoring active
   - [ ] All alerting rules firing correctly
   - [ ] Team on-call ready

## Post-Deployment

### Verification (Week 4)
- [ ] All endpoints responding normally
- [ ] Database replication lag < 1s
- [ ] No customer complaints
- [ ] Performance metrics meet SLA
- [ ] Cost within budget

### Rollback Plan (If Needed)
```bash
kubectl rollout undo deployment/fastapi
kubectl rollout undo deployment/model-service
```

---
**Status**: Ready for Production
**Last Updated**: December 26, 2025
