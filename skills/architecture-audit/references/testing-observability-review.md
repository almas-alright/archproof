# Testing and Observability (Domains L and N)

## §L Testing and Quality Assurance

Line coverage is not proof of quality. Assess *what* is tested, *how well*, and whether CI enforces it.

### Steps

1. Inventory test types and frameworks: unit, integration (real DB/containers?), E2E (Playwright/Cypress/Selenium), contract (Pact, schema tests), performance (k6, Gatling, JMeter, Locust), security (SAST/DAST in CI), mutation testing (Stryker, Infection, PIT, mutmut).
2. Map tests to the critical business flows from Phase 2. Produce a **critical-flow coverage table**:

| Critical flow | Unit | Integration | E2E | Negative/edge cases | Evidence |
|---|---|---|---|---|---|
| Checkout & payment | partial | none | 1 happy path | none | `tests/Feature/CheckoutTest.php` |

3. Read a sample of tests (at least 10, biased to critical flows) for quality.

### Checklist

- [ ] Assertions meaningful (not just "no exception" or snapshot-everything).
- [ ] Over-mocking: tests that mock the unit under test's collaborators so heavily they test the mocks; repository/ORM mocked in tests meant to verify queries.
- [ ] Test isolation: shared DB state, order dependence, real network calls, time-dependent tests (`now()` without clock control), random seeds.
- [ ] Flakiness indicators: retries configured in CI, `sleep` in tests, skipped/quarantined tests (`@Disabled`, `skip`, `xit`, `markTestSkipped`) — count and age.
- [ ] Negative and authorisation tests: does any test assert that user A cannot access user B's resource? (Absence → `WEAKNESS` in L; link to F findings.)
- [ ] Concurrency/idempotency tests for money/stock flows.
- [ ] Migration tests (up/down on a real DB).
- [ ] Fixtures/factories realistic; test data builders.
- [ ] CI: tests run on every PR, required to pass, coverage reported (not gated blindly), runtime reasonable, parallelised.
- [ ] Coverage numbers: report only from an actual coverage file/run; at L0 say "coverage not measured".

## §N Observability and Monitoring

- [ ] Structured logging (JSON) with levels; consistent fields (timestamp, level, service, trace_id, request_id, tenant_id, user_id where lawful).
- [ ] Correlation/request IDs generated at the edge and propagated to logs, outbound calls and messages.
- [ ] Sensitive data in logs (owner: F — cross-reference): request bodies logged wholesale, auth headers, tokens, PII.
- [ ] Metrics: RED (rate, errors, duration) for endpoints; USE for resources; business KPIs; queue depth and job latency; DB pool usage. Library present (Prometheus client, Micrometer, OpenTelemetry, StatsD, Datadog)?
- [ ] Distributed tracing: OpenTelemetry/APM instrumentation, context propagation across async boundaries.
- [ ] Error tracking (Sentry, Rollbar, Bugsnag, App Insights) with release tagging and PII scrubbing.
- [ ] Audit logs for security-relevant actions (login, permission changes, data exports, admin actions) — append-only, tamper-evident where regulated.
- [ ] Health endpoints: application and dependency health (cross-reference K).
- [ ] Alerting: alert rules in repo (Prometheus rules, Terraform monitors)? SLOs/SLIs defined? Alerts tied to runbooks?
- [ ] Dashboards as code.
- [ ] Incident investigation capability: could an engineer answer "which requests failed for tenant X between 10:00 and 10:15 and why" with what exists? Walk through it explicitly — this is a strong, concrete way to present observability gaps.

Monitoring configured outside the repository is not visible; record as `ASSUMPTION` rather than "no monitoring exists".
