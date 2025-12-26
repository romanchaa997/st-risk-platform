# Kubernetes & Autoscaling Playbook

## Phase 1: Docker-Compose to K8s Migration

### Step 1: Containerize Services
```bash
docker build -t st-risk-platform:1.0 .
docker push registry.example.com/st-risk-platform:1.0
```

### Step 2: Create Kubernetes Manifests
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi
  template:
    metadata:
      labels:
        app: fastapi
    spec:
      containers:
      - name: fastapi
        image: st-risk-platform:1.0
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

## Phase 2: Horizontal Pod Autoscaling

### HPA Configuration
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-service
  minReplicas: 3
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

## Phase 3: Queue-Based Autoscaling

### Kafka Consumer Group Scaling
```python
# Auto-scale based on consumer lag
from kafka import KafkaAdminClient

lagMetric = (queue_depth) / (running_pods)
if lagMetric > threshold:
    scale_up()
elif lagMetric < min_threshold:
    scale_down()
```

## Phase 4: Monitoring

### Key Metrics
- Pod CPU utilization
- Memory usage
- Queue depth
- Request latency

---
**Version**: 1.0
**Status**: Production Ready
