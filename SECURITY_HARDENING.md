# Security Hardening Guide for st-risk-platform

Comprehensive security hardening procedures for the st-risk-platform production deployment.

## Application Security

### Dependency Management

**Vulnerability Scanning:**
```bash
# Scan Python dependencies
pip-audit

# Scan with Safety
safety check

# Scan Docker image with Trivy
trivy image st-risk-platform:latest

# Use SBOM for tracking
syft st-risk-platform:latest -o json > sbom.json
```

**Dependency Updates:**
- [ ] Use Dependabot for automated dependency updates
- [ ] Maintain software bill of materials (SBOM)
- [ ] Pin major versions, allow patch updates
- [ ] Review and test updates before production deployment
- [ ] Schedule regular security update reviews

### Application Code Security

**Input Validation:**
```python
# Implement strict input validation
from pydantic import BaseModel, validator

class RiskAnalysisRequest(BaseModel):
    portfolio_id: str
    analysis_type: str
    
    @validator('portfolio_id')
    def validate_portfolio_id(cls, v):
        if not v or len(v) > 50:
            raise ValueError('Invalid portfolio_id')
        return v
```

**Output Encoding:**
```python
# Always encode output for context
from markupsafe import escape

response_data = {
    'status': escape(user_input),
    'data': json.dumps(data, default=str)
}
```

**SQL Injection Prevention:**
- [ ] Use parameterized queries (SQLAlchemy ORM)
- [ ] Never use string concatenation for queries
- [ ] Use prepared statements
- [ ] Validate all database inputs

**CSRF Protection:**
```python
# Enable CSRF protection in FastAPI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
```

**XSS Prevention:**
- [ ] Use template escaping
- [ ] Content Security Policy headers
- [ ] HTTPOnly and Secure cookies
- [ ] No inline scripts

### API Security

**Authentication:**
```python
# Implement OAuth2 with JWT
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Validate credentials
    token = jwt.encode(
        {"sub": user.email, "exp": datetime.utcnow() + timedelta(hours=1)},
        SECRET_KEY,
        algorithm="HS256"
    )
    return {"access_token": token, "token_type": "bearer"}

@app.get("/api/risk")
async def get_risk(token: str = Depends(oauth2_scheme)):
    # Verify token
    pass
```

**Rate Limiting:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/risk")
@limiter.limit("100/minute")
async def get_risk(request: Request):
    pass
```

**API Key Management:**
- [ ] Rotate API keys every 90 days
- [ ] Use separate keys for different environments
- [ ] Hash API keys before storage
- [ ] Implement key versioning
- [ ] Monitor key usage for anomalies

### Secrets Management

**Secret Storage:**
```bash
# Using Kubernetes Sealed Secrets
echo -n 'supersecret' | kubectl create secret generic mysecret \
  --dry-run=client --from-file=/dev/stdin -o yaml | \
  kubeseal -f - > mysealedsecret.yaml

# Using HashiCorp Vault
vault kv put secret/st-risk/db-password value=supersecret
```

**Secret Rotation:**
- [ ] Implement automatic secret rotation
- [ ] Rotate database passwords every 30 days
- [ ] Rotate API keys every 90 days
- [ ] Update all dependent services before old credentials expire
- [ ] Maintain audit trail of all rotations

**Secret Audit Logging:**
```yaml
# Enable audit logging for secret access
apiVersion: v1
kind: AuditPolicy
rules:
- level: RequestResponse
  omitStages:
  - RequestReceived
  resources:
  - group: ""
    resources:
    - secrets
```

## Infrastructure Security

### Network Security

**Network Policies:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: st-risk-security
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
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443  # HTTPS only
  - to:
    - podSelector:
        matchLabels:
          app: clickhouse
    ports:
    - protocol: TCP
      port: 9000  # ClickHouse native
```

**Firewall Rules:**
- [ ] Deny all by default
- [ ] Allow only necessary traffic
- [ ] Use service-to-service authentication
- [ ] Monitor unusual traffic patterns
- [ ] Block known malicious IPs

**TLS/SSL Configuration:**
```nginx
# Enforce TLS 1.2+
server {
    listen 443 ssl http2;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # HSTS header
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

### Container Security

**Container Image Hardening:**
```dockerfile
# Use minimal base image
FROM python:3.11-slim

# Run as non-root user
RUN useradd -m -u 1000 appuser

# Remove unnecessary packages
RUN apt-get purge -y apt-listchanges apt-show-versions \
    && apt-get autoremove -y && apt-get clean

# Make file system read-only
RUN chmod 555 /etc /etc/ssl

USER appuser:appuser
```

**Pod Security Policy:**
```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: st-risk-restricted
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
  - ALL
  volumes:
  - 'configMap'
  - 'emptyDir'
  - 'projected'
  - 'secret'
  - 'downwardAPI'
  - 'persistentVolumeClaim'
  hostNetwork: false
  hostIPC: false
  hostPID: false
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'MustRunAs'
  readOnlyRootFilesystem: true
```

**Container Registry Security:**
- [ ] Use private Docker registry
- [ ] Sign container images
- [ ] Scan images before pushing
- [ ] Enforce image pull policies
- [ ] Use image digest pinning

### Kubernetes Security

**RBAC Configuration:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: st-risk-viewer
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: st-risk-viewer-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: st-risk-viewer
subjects:
- kind: ServiceAccount
  name: st-risk-sa
  namespace: production
```

**Service Account Security:**
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: st-risk-sa
---
apiVersion: v1
kind: Pod
metadata:
  name: st-risk-pod
spec:
  serviceAccountName: st-risk-sa
  automountServiceAccountToken: true
```

## Data Security

### Encryption

**Encryption at Rest:**
```yaml
# Enable ClickHouse encryption
<config>
  <encryption>
    <enabled>1</enabled>
    <algorithm>AES_256_GCM</algorithm>
  </encryption>
</config>
```

**Encryption in Transit:**
- [ ] Enforce HTTPS/TLS for all APIs
- [ ] Use TLS 1.2+ exclusively
- [ ] Encrypt database connections
- [ ] Use certificate pinning for critical connections

### Data Classification

**Data Sensitivity Levels:**
1. **Public:** No restrictions
2. **Internal:** Restricted to employees
3. **Confidential:** Limited access, encryption required
4. **Restricted:** Highest security level, audit logging required

**Access Control by Classification:**
```python
@app.get("/api/restricted-risk")
@require_permission("confidential_data_access")
async def get_restricted_risk(user: User = Depends(get_current_user)):
    # Log access
    audit_log.info(f"Restricted data accessed by {user.id}")
    return restricted_data
```

### Database Security

**ClickHouse Hardening:**
```xml
<config>
  <!-- Disable remote access -->
  <listen_host>127.0.0.1</listen_host>
  
  <!-- Enable query logging -->
  <query_log>
    <database>system</database>
    <table>query_log</table>
  </query_log>
  
  <!-- Row-level security -->
  <user_defined_sql_objects_path>/etc/clickhouse-server/udfs/</user_defined_sql_objects_path>
</config>
```

## Monitoring and Audit

### Audit Logging

```yaml
# Enable API audit logging
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: RequestResponse
  omitStages:
  - RequestReceived
  resources:
  - group: ""
    resources:
    - secrets
  - group: apps
    resources:
    - deployments
```

### Security Monitoring

**Prometheus Metrics:**
```python
from prometheus_client import Counter, Histogram

failed_auth = Counter(
    'auth_failures_total',
    'Total authentication failures'
)

request_duration = Histogram(
    'request_duration_seconds',
    'Request duration in seconds'
)
```

**Alert Rules:**
```yaml
alerts:
  - name: HighFailedAuthRate
    expr: rate(auth_failures_total[5m]) > 0.1
    for: 5m
    severity: critical
  
  - name: UnauthorizedAPIAccess
    expr: rate(http_requests_unauthorized[5m]) > 0
    for: 1m
    severity: warning
```

## Security Checklist

- [ ] All dependencies scanned for vulnerabilities
- [ ] Input validation implemented on all endpoints
- [ ] CSRF protection enabled
- [ ] SQL injection protections in place
- [ ] XSS prevention enabled
- [ ] Authentication mechanism deployed
- [ ] Authorization rules enforced
- [ ] Rate limiting configured
- [ ] API keys properly secured and rotated
- [ ] Secrets encrypted and audit-logged
- [ ] Network policies configured
- [ ] TLS 1.2+ enforced
- [ ] Container images hardened
- [ ] RBAC policies configured
- [ ] Pod security policies enforced
- [ ] Encryption at rest enabled
- [ ] Encryption in transit enabled
- [ ] Audit logging enabled
- [ ] Security monitoring active
- [ ] Incident response plan documented
