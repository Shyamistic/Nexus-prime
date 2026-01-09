# 📚 Nexus Prime API Reference

**Version:** 1.0.0  
**Base URL:** `https://nexus-backend.nicesea-d905a880.centralindia.azurecontainerapps.io`  
**Specification:** OpenAPI 3.1

## 🔐 Authentication

Nexus Prime uses JWT (JSON Web Tokens) for API authentication.

**Header:** `Authorization: Bearer <token>`

### Login
Authenticate a user and retrieve an access token.

- **Endpoint:** `POST /api/v1/auth/login`
- **Content-Type:** `application/json`

#### Request Body
```json
{
  "email": "judge@nexus.local",
  "password": "Nexus!123"
}
```

#### Response (200 OK)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "usr_123456789",
    "email": "judge@nexus.local",
    "role": "admin",
    "tenant_id": "org_987654321"
  }
}
```

---

## 📡 Ingestion (Webhooks)

Endpoints for ingesting alerts from monitoring tools. These endpoints are rate-limited and require an API Key or valid JWT.

### Generic Webhook
Ingest a standardized alert payload from any source.

- **Endpoint:** `POST /api/v1/ingest/webhook/generic`
- **Headers:** `X-API-Key: <your_api_key>`

#### Request Body
```json
{
  "title": "High Latency in Payment Service",
  "summary": "95th percentile latency exceeded 2000ms for 5 minutes.",
  "severity": "critical",
  "source": "custom-monitor",
  "service_id": "payment-gateway-v2",
  "timestamp": "2026-01-09T10:00:00Z",
  "tags": ["production", "finance", "latency"],
  "metadata": {
    "region": "us-east-1",
    "cluster": "k8s-prod-01",
    "current_latency": 2500,
    "threshold": 2000
  }
}
```

#### Response (202 Accepted)
```json
{
  "status": "accepted",
  "incident_id": "inc_550e8400-e29b",
  "analysis_status": "pending"
}
```

### Provider Specific Webhooks
Nexus Prime natively supports payloads from major monitoring providers.

- `POST /api/v1/ingest/webhook/datadog`
- `POST /api/v1/ingest/webhook/pagerduty`
- `POST /api/v1/ingest/webhook/prometheus`
- `POST /api/v1/ingest/webhook/aws-cloudwatch`

---

## 🚨 Incidents

Manage and retrieve incident details, including AI analysis.

### List Incidents
Retrieve a paginated list of incidents for the current tenant.

- **Endpoint:** `GET /api/v1/incidents/`
- **Query Params:**
  - `skip`: (int) Number of records to skip (default: 0)
  - `limit`: (int) Max records to return (default: 20)
  - `status`: (string) Filter by status (open, investigating, resolved)

#### Response (200 OK)
```json
[
  {
    "id": "inc_550e8400-e29b",
    "title": "High Latency in Payment Service",
    "severity": "critical",
    "status": "investigating",
    "created_at": "2026-01-09T10:00:00Z",
    "ai_analysis": {
      "root_cause": "Database connection pool exhaustion due to unclosed connections in payment-service v2.1.4.",
      "confidence_score": 0.92,
      "summary": "The latency spike correlates with a deployment at 09:55 UTC."
    }
  }
]
```

### Get Incident Details
Get full details, including the timeline and remediation plan.

- **Endpoint:** `GET /api/v1/incidents/{incident_id}`

#### Response (200 OK)
```json
{
  "id": "inc_550e8400-e29b",
  "title": "High Latency in Payment Service",
  "remediation_plan": {
    "steps": [
      {
        "order": 1,
        "action": "scale_up",
        "target": "payment-gateway-v2",
        "params": {"replicas": 5},
        "description": "Scale up pods to handle immediate load."
      },
      {
        "order": 2,
        "action": "restart_service",
        "target": "payment-gateway-v2",
        "description": "Restart service to clear hung connections."
      }
    ],
    "estimated_recovery_time": "45s"
  }
}
```

---

## 📊 Dashboard & Metrics

Endpoints powering the real-time dashboard.

### System Metrics
Get aggregated performance metrics for the tenant.

- **Endpoint:** `GET /api/v1/dashboard/metrics`

#### Response (200 OK)
```json
{
  "mttr_seconds": 145,
  "active_incidents": 3,
  "incidents_today": 12,
  "ai_accuracy_rate": 0.94,
  "uptime_sla": 99.98,
  "cost_savings_usd": 15400
}
```

### System Health
Public endpoint to check API health.

- **Endpoint:** `GET /health`

#### Response (200 OK)
```json
{
  "status": "healthy",
  "version": "1.2.0",
  "services": {
    "database": "connected",
    "ai_engine": "operational",
    "queue": "operational"
  }
}
```