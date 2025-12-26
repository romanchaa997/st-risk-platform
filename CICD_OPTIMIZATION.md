# CI/CD Optimization

## GitHub Actions Workflow

```yaml
name: Performance Tests & Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Performance Tests
        run: |
          k6 run load_test.js --vus 100 --duration 30s
      
      - name: Build Docker Image
        run: |
          docker build --cache-from type=gha -o type=gha .
      
      - name: Push to Registry
        run: |
          docker push ${{ secrets.REGISTRY }}/st-risk-platform:latest
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to K8s
        run: |
          kubectl set image deployment/fastapi-service \
            fastapi=${{ secrets.REGISTRY }}/st-risk-platform:latest
```

## Performance Checks

- Response time < 500ms (P95)
- Error rate < 0.1%
- Database queries < 50ms
- Build time < 5 minutes

---
**Status**: Production Ready
