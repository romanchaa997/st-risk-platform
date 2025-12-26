# API Documentation

## Endpoints

### POST /api/risk/assess
Assess risk for given metrics

**Request:**
```json
{
  "risk_id": "123",
  "metrics": [1, 2, 3]
}
```

**Response (200 OK):**
```json
{
  "risk_score": 75,
  "status": "HIGH",
  "timestamp": "2025-12-26T22:00:00Z"
}
```

**Performance:**
- P95: < 500ms
- Error Rate: < 0.1%

### GET /api/features
Get available features

**Response (200 OK):**
```json
{
  "features": [
    {"id": 1, "name": "metric_1"},
    {"id": 2, "name": "metric_2"}
  ]
}
```

### GET /health
Health check endpoint

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-26T22:00:00Z"
}
```

---
**Version**: 1.0
**Status**: Production Ready
