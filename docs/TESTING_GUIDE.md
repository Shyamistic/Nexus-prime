# 🧪 Nexus Prime Testing Strategy

This document outlines the comprehensive testing strategy for the Nexus Prime platform, ensuring enterprise-grade reliability, security, and performance.

## 1. Testing Pyramid

We adhere to the standard testing pyramid to ensure rapid feedback and high confidence.

| Layer | Scope | Tools | Frequency |
|-------|-------|-------|-----------|
| **E2E** | Full user flows (Frontend + Backend + AI) | Playwright, Python Scripts | Nightly / Pre-release |
| **Integration** | API endpoints, DB interactions, Webhooks | Pytest, Postman | On PR Merge |
| **Unit** | Individual functions, AI parsers, React components | Pytest, Jest | On Commit |

---

## 2. Automated Testing Suite

### Backend Tests (Python/FastAPI)
Located in `backend/tests/`.

- **Unit Tests**: Cover domain logic, utility functions, and data models.
- **Integration Tests**: Use `TestClient` to verify API endpoints against a test database.

```bash
# Run backend tests
cd backend
pytest tests/ -v --cov=app
```

### Frontend Tests (React)
Located in `frontend/src/__tests__/`.

- **Component Tests**: Verify UI rendering and state changes using React Testing Library.
- **Hook Tests**: Verify custom hooks logic.

```bash
# Run frontend tests
cd frontend
npm test
```

---

## 3. Live Deployment Verification

We use a dedicated script to verify the health and functionality of the production environment without disrupting real data.

### Verification Script
Located at `scripts/verify_deployment.py`.

**Capabilities:**
1. Checks System Health (`/health`)
2. Verifies Authentication (`/api/v1/auth/login`)
3. Validates Dashboard Metrics (`/api/v1/dashboard/metrics`)
4. Simulates a "Dry Run" Webhook (Optional)

**Usage:**
```bash
python scripts/verify_deployment.py --env production
```

---

## 4. Load & Performance Testing

We use **Locust** to simulate high-concurrency incident ingestion to ensure the system handles enterprise-scale traffic.

**Scenarios:**
- **Webhook Storm**: 1000 concurrent webhooks/sec.
- **Dashboard Polling**: 500 concurrent users refreshing dashboards.

**SLA Thresholds:**
- API Latency (p95): < 200ms
- AI Analysis Time: < 10s
- Error Rate: < 0.1%

---

## 5. Security Testing

Security is paramount for enterprise incident response.

### Static Application Security Testing (SAST)
- **Tools**: Bandit (Python), ESLint Security Plugin (JS)
- **Pipeline**: Runs on every GitHub Action push.

### Dynamic Application Security Testing (DAST)
- **OWASP ZAP**: Automated scan of deployed endpoints.
- **Checks**: SQL Injection, XSS, Broken Auth, Sensitive Data Exposure.

---

## 6. Manual QA Checklist

Before any major release, the following manual checks are performed:

- [ ] **AI Accuracy**: Verify GPT-4 analysis on 5 sample incidents.
- [ ] **Real-time Sockets**: Verify dashboard updates without refresh.
- [ ] **Mobile View**: Check responsiveness on iOS/Android viewports.
- [ ] **Dark Mode**: Verify contrast ratios and visual consistency.
- [ ] **Tenant Isolation**: Ensure User A cannot see User B's data.

---

## 7. Continuous Integration (CI/CD)

Our GitHub Actions pipeline enforces quality gates:
1. **Linting**: Black (Python), Prettier (JS)
2. **Tests**: Must pass with 100% success.
3. **Build**: Docker build must succeed.
4. **Deploy**: Auto-deploy to Azure Container Apps (Staging).