# Cost Optimization Guide for st-risk-platform

Strategies for reducing cloud infrastructure and operational costs while maintaining performance and availability.

## Compute Cost Optimization

### Right-Sizing Instances

**Current Resource Usage Analysis:**
```bash
# Monitor actual CPU and memory usage
kubectl top nodes
kubectl top pods -A

# Export metrics for analysis
kubectl get --all-namespaces --output=json nodes | \
  jq '.items[] | {name: .metadata.name, cpu: .status.allocatable.cpu, memory: .status.allocatable.memory}'
```

**Optimization Strategies:**
- Use AWS t3/t4g instances (burstable) for non-critical workloads
- Schedule batch jobs during off-peak hours
- Use Spot instances for fault-tolerant workloads (30-70% savings)
- Implement auto-scaling with appropriate thresholds

### Vertical Pod Autoscaling (VPA)

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: st-risk-vpa
spec:
  targetRef:
    apiVersion: "apps/v1"
    kind: Deployment
    name: st-risk-api
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: st-risk-api
      minAllowed:
        cpu: 100m
        memory: 128Mi
      maxAllowed:
        cpu: 2
        memory: 2Gi
```

### Horizontal Pod Autoscaling (HPA)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: st-risk-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: st-risk-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Storage Cost Optimization

### Database Optimization

**ClickHouse Table Compression:**
```xml
<!-- Configure compression for cost savings -->
<config>
  <clickhouse>
    <compression>
      <case>
        <method>zstd</method>
        <min_part_size>10000000</min_part_size>
        <min_part_size_ratio>0.01</min_part_size_ratio>
      </case>
    </compression>
    <!-- Tiered storage -->
    <storage_policy>
      <policies>
        <default>
          <volumes>
            <hot>
              <path>/var/lib/clickhouse/data</path>
              <storage_policy>hot</storage_policy>
            </hot>
            <cold>
              <path>/mnt/slow-storage/data</path>
              <storage_policy>cold</storage_policy>
            </cold>
          </volumes>
          <move_factor>0.1</move_factor>
        </default>
      </policies>
    </storage_policy>
  </clickhouse>
</config>
```

**Data Retention Policies:**
```python
# Implement data lifecycle management
from datetime import datetime, timedelta

class DataRetentionManager:
    # Hot storage: 7 days
    # Warm storage: 30 days  
    # Cold storage: 1 year
    # Archive: 7 years (for compliance)
    
    RETENTION_DAYS = {
        'hot': 7,
        'warm': 30,
        'cold': 365,
        'archive': 2555
    }
```

**Cleanup Strategies:**
```bash
# Regular cleanup job
kubectl create cronjob cleanup-old-data \
  --image=st-risk:latest \
  --schedule="0 2 * * *" \
  -- python cleanup_retention.py
```

### Persistent Volume Optimization

```yaml
# Use cheaper storage classes
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: clickhouse-storage
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: 3000
  throughput: 125
allowVolumeExpansion: true
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: clickhouse-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: clickhouse-storage
  resources:
    requests:
      storage: 500Gi
```

## Network Cost Optimization

### Data Transfer Optimization

**Reduce Inter-Region Transfers:**
- Use VPC endpoints for AWS services (no data transfer charges)
- Implement caching at edge locations
- Compress API responses with gzip/brotli
- Use CDN for static assets

**Configuration:**
```python
from fastapi.middleware.gzip import GZIPMiddleware

app.add_middleware(GZIPMiddleware, minimum_size=1000)
```

**Load Balancer Optimization:**
```yaml
# Use NLB (Network Load Balancer) for better cost/performance
apiVersion: v1
kind: Service
metadata:
  name: st-risk-nlb
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
spec:
  type: LoadBalancer
  selector:
    app: st-risk-api
  ports:
    - protocol: TCP
      port: 443
      targetPort: 8000
```

## Operational Cost Optimization

### Monitoring and Observability

**Reduce Log Storage Costs:**
```yaml
# Configure log retention in ELK/CloudWatch
index.lifecycle.name: logs
index.lifecycle.rollover.max_age: 30d
index.lifecycle.rollover.max_size: 50GB
index.lifecycle.delete.min_age: 90d
```

**Metrics Optimization:**
```python
# Reduce cardinality in Prometheus metrics
from prometheus_client import Counter

# Bad: High cardinality
bad_metric = Counter(
    'requests_total',
    'Total requests',
    ['user_id', 'endpoint']  # Could have millions of combinations
)

# Good: Low cardinality
good_metric = Counter(
    'requests_total',
    'Total requests',
    ['endpoint', 'method']  # Limited combinations
)
```

### License and Tool Costs

**Open Source Alternatives:**
- Replace Datadog with Prometheus + Grafana
- Use open-source APM (Jaeger, Tempo) instead of commercial solutions
- Use OpenTelemetry for vendor-agnostic observability
- Leverage ELK stack instead of Splunk

## Development and Testing Costs

### Staging Environment Optimization

```bash
# Reduce staging environment to non-business hours
# Using Kubernetes CronJob
kubectl create cronjob scale-down-staging \
  --image=bitnami/kubectl:latest \
  --schedule="20 18 * * 1-5" \
  -- scale deployment st-risk-api --replicas=1 -n staging

kubectl create cronjob scale-up-staging \
  --image=bitnami/kubectl:latest \
  --schedule="0 8 * * 1-5" \
  -- scale deployment st-risk-api --replicas=3 -n staging
```

### CI/CD Optimization

**Reduce Build Times and Costs:**
- Cache Docker layers
- Use matrix builds efficiently
- Parallelize tests
- Limit concurrent builds

```yaml
# GitHub Actions cost optimization
name: Build
on:
  pull_request:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11']
    steps:
      - uses: actions/checkout@v3
      - uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

## Reserved Capacity Planning

### Commitment Discounts

**AWS Savings Plans:**
- 1-year commitment: 24% savings
- 3-year commitment: 35% savings
- Recommended for predictable workloads

**Reserved Instances (RIs):**
```python
# Analyze usage patterns to determine commitment level
base_capacity = 3  # Always-on replicas
peak_capacity = 10  # Peak load replicas

# Reserve base capacity
reserved_capacity = base_capacity
spot_capacity = peak_capacity - base_capacity
```

## Cost Monitoring and Budgets

### AWS Budgets Configuration

```python
import boto3

budgets = boto3.client('budgets')

response = budgets.create_budget(
    AccountId='123456789012',
    Budget={
        'BudgetName': 'st-risk-monthly',
        'BudgetLimit': {
            'Amount': '5000.00',
            'Unit': 'USD'
        },
        'TimeUnit': 'MONTHLY',
        'BudgetType': 'COST'
    },
    NotificationsWithSubscribers=[
        {
            'Notification': {
                'NotificationType': 'FORECASTED',
                'ComparisonOperator': 'GREATER_THAN',
                'Threshold': 80
            },
            'Subscribers': [
                {
                    'SubscriptionType': 'EMAIL',
                    'Address': 'devops@example.com'
                }
            ]
        }
    ]
)
```

### Cost Attribution Tags

```python
# Tag resources for cost allocation
tags = {
    'Environment': 'production',
    'Service': 'st-risk-platform',
    'CostCenter': 'engineering',
    'Owner': 'platform-team'
}

# AWS resource tagging
ec2 = boto3.client('ec2')
ec2.create_tags(
    Resources=['i-1234567890abcdef0'],
    Tags=[{'Key': k, 'Value': v} for k, v in tags.items()]
)
```

## Cost Optimization Checklist

- [ ] Implement auto-scaling policies
- [ ] Right-size instances based on usage
- [ ] Use Spot instances for non-critical workloads
- [ ] Optimize storage compression and retention
- [ ] Use storage tiering (hot/warm/cold)
- [ ] Implement VPC endpoints
- [ ] Configure CDN for static assets
- [ ] Reduce log verbosity and retention
- [ ] Optimize metrics cardinality
- [ ] Schedule non-production environments
- [ ] Use Reserved Instances for base capacity
- [ ] Enable AWS Cost Explorer
- [ ] Set up budget alerts
- [ ] Review and optimize database queries
- [ ] Implement caching strategies

## Expected Monthly Cost Breakdown

**Production Environment (Sample):**
```
Compute:
  - 3x t4g.medium on-demand: $80/month
  - 5x t4g.small spot instances: $50/month
  Subtotal: $130/month

Database (ClickHouse):
  - 3x r6i.xlarge reserved: $400/month
  - Storage (500GB @ $0.023/GB): $12/month
  Subtotal: $412/month

Networking:
  - Data transfer: $50/month
  - NLB: $16/month
  Subtotal: $66/month

Storage:
  - EBS volumes: $30/month
  - S3 backups: $20/month
  Subtotal: $50/month

Monitoring:
  - Prometheus + Grafana: $0 (self-hosted)
  - CloudWatch: $30/month
  Subtotal: $30/month

Total Monthly: ~$688/month
Annual Cost: ~$8,256
```

## References

See additional optimization guides:
- PERFORMANCE_CHECKLIST.md - Performance optimization
- SCALING_PLAYBOOK.md - Horizontal scaling strategies
- DEPLOYMENT_CHECKLIST.md - Deployment cost considerations
