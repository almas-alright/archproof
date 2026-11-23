# API Platform and Gateway Profile (extends Domain I)

## When to activate

Activate this profile when **any** of the following holds, and record the trigger in the scope statement:

- The API is the product: a public or partner API, SaaS platform API, developer platform, or API-first backend consumed by third-party clients or SDKs.
- The system is an API engine: it generates, aggregates or federates APIs (BFF, GraphQL federation or gateway, schema stitching, API composition layer).
- The system is or contains an API gateway or edge proxy: Kong, Envoy, NGINX/OpenResty, Traefik, Apigee, AWS API Gateway, Azure APIM, Tyk, KrakenD, Spring Cloud Gateway, YARP, Ocelot, or a custom gateway.
- The user explicitly asks for an API audit.

Otherwise, the standard Domain I checklist in `distributed-systems-review.md` is enough.

Findings from this profile use domain **I** (gateway security issues still belong to **F**; gateway resilience issues to **K**). Prefix titles with `[API]` or `[Gateway]` for easy filtering.

## Audit scope boundary (architecture vs QA)

| This profile audits (architecture and governance) | Leave to QA (state as a recommendation) |
|---|---|
| Whether an API standard exists, is coherent, and is **enforced automatically** | Verifying every endpoint against the standard by hand |
| Contract source of truth and how contracts evolve | Writing per-endpoint contract tests |
| The error model and its consistency (sampled) | Exhaustive negative testing |
| Versioning, deprecation and breaking-change control | Regression suites |
| Gateway responsibilities, failure modes and configuration-as-code | Load or soak testing |

Sample at least 10 endpoints or 20% of the surface (whichever is larger, capped at 40), biased towards write operations, authentication, payment or high-value flows, and public endpoints. State the sample in the report.

## Which standard to audit against

1. **The organisation's own API style guide**, if one exists in the repo or the user provides it. It always takes precedence; audit conformance and internal consistency.
2. Otherwise use the **ArchProof baseline** (§4 below), which is informed by widely used public guidance: RFC 9110 (HTTP semantics), RFC 9457 (Problem Details), RFC 8594 (Sunset header), the IETF Deprecation header, OpenAPI 3.x, the OWASP API Security Top 10 (2023), and public style guides such as Google AIP, Microsoft REST API Guidelines and Zalando RESTful API Guidelines. Name what you used, and do not present any single public guide as mandatory.

**Severity discipline**: pure style deviations (casing, plural nouns, URL shape) are capped at **LOW**, unless they break clients, make the API ambiguous in a way that causes real misuse, or create a security issue. Inconsistency *across* the API (three error formats, two pagination styles) is a real maintainability and consumer-experience cost; it is usually MEDIUM.

## 1. Contract and specification

- [ ] Source of truth: spec-first (OpenAPI, AsyncAPI, GraphQL SDL, `.proto`) or code-first with a generated spec. Is the published spec generated in CI from code, or hand-maintained (drift risk)?
- [ ] Spec completeness: every operation has schemas for request/response/errors, auth requirements, examples, and descriptions.
- [ ] **Drift check**: compare the spec with the implementation for the sample (paths, methods, parameters, required fields, status codes). Each mismatch is evidence.
- [ ] Linting: Spectral, Redocly CLI or vacuum rulesets in CI (L1: run with the repo's ruleset, or a default ruleset, and report the counts by rule).
- [ ] Breaking-change detection in CI: `oasdiff breaking`, `openapi-diff`, `buf breaking` (gRPC), `graphql-inspector diff`. Is it absent, or present but non-blocking?
- [ ] Schema reuse (`components`), no inline duplication of core models.
- [ ] Consumer artefacts: generated SDKs and clients versioned with the spec.

## 2. Resource and operation design

- [ ] Correct HTTP method semantics: GET safe, PUT/DELETE idempotent, POST for creation and commands, PATCH semantics declared (JSON Merge Patch or JSON Patch).
- [ ] Status codes used meaningfully: 201 with Location, 202 for async with a status resource, 204, 400 vs 422 policy, 401 vs 403, 404 vs 403 for hidden resources, 409 for conflicts, 412/428 for preconditions, 429 with Retry-After. No errors returned as `200 {"success": false}`.
- [ ] Consistent naming (resources, fields, enums, casing) and stable, opaque IDs. Do not expose sequential DB IDs on multi-tenant APIs (links to F: enumeration).
- [ ] Long-running operations: an async job pattern, not request timeouts.
- [ ] Bulk and batch endpoints: size limits, partial failure reporting.
- [ ] Field selection or sparse fieldsets, expansion/embedding limits.
- [ ] Data formats: ISO 8601 UTC timestamps, money as decimal string or minor units plus currency, explicit nullability.

## 3. Error model

- [ ] One error format across the API (RFC 9457 `application/problem+json`, or a documented equivalent) with a stable machine-readable `type`/`code`, a human message, a correlation or trace ID, and field-level validation details.
- [ ] Errors map domain exceptions deliberately. No stack traces, SQL or internal hostnames leak (F if sensitive).
- [ ] Error codes are documented and stable (consumers branch on them).
- [ ] Consistency across services behind the gateway (a gateway-generated 502/504/429 uses the same envelope).

## 4. ArchProof baseline rules (when no house standard exists)

| # | Rule | Default severity if violated |
|---|---|---|
| B1 | Every endpoint documented in a machine-readable contract that CI keeps in sync | MEDIUM |
| B2 | A single, documented error envelope with stable error codes | MEDIUM |
| B3 | Breaking changes blocked in CI, or explicitly versioned | MEDIUM (HIGH for public or partner APIs) |
| B4 | A versioning and deprecation policy is published (Deprecation/Sunset headers, a notice period) | MEDIUM |
| B5 | Collection endpoints paginate with an enforced maximum page size | MEDIUM (HIGH if unbounded on large data) |
| B6 | Unsafe, retryable operations with side effects (payments, orders, provisioning) accept an idempotency key backed by a uniqueness guarantee | HIGH for money or provisioning |
| B7 | Authentication on every non-public route; object-level authorisation on every resource access | Owned by F |
| B8 | Rate limits or quotas per client or key, with 429 and Retry-After | MEDIUM (HIGH for public APIs) |
| B9 | Request size, depth and complexity limits (body size, GraphQL depth/cost, batch size) | MEDIUM |
| B10 | Correlation ID accepted or generated and returned on every response | LOW |
| B11 | Timeouts are explicit at every hop, and each hop's timeout is shorter than its caller's | Owned by K/I |
| B12 | Consistent naming, casing and date/money formats | LOW |
| B13 | Webhooks (if any) are signed, retried with backoff, carry event IDs, and are documented | MEDIUM |
| B14 | Changelog and API reference docs are generated from the contract | LOW |

## 5. Versioning, compatibility and lifecycle

- [ ] Strategy: URI (`/v1`), header or media type, date-based (`2026-01-15`), or evolution-only (additive changes plus deprecation). Any is acceptable if consistent and documented.
- [ ] What counts as breaking is defined (removing or renaming fields, tightening validation, changing enums, changing defaults or error codes).
- [ ] Deprecation process: headers, docs, usage telemetry per version, a sunset date, consumer communication.
- [ ] Multiple live versions: how many, the cost of maintaining them, shared code paths vs forks.
- [ ] Git history evidence: breaking diffs to DTOs/schemas merged without a version bump (cite commits).

## 6. Consumer-facing reliability semantics

- [ ] Idempotency keys: storage, TTL, scope (per client), behaviour on a replay with a different payload (should be 422/409).
- [ ] Concurrency control: ETags with If-Match, or version fields, for updates (lost-update prevention).
- [ ] Pagination: cursor-based for large or changing collections, stable sort, maximum limit enforced server-side.
- [ ] Retry guidance documented (which codes are retryable), with Retry-After honoured.
- [ ] Caching headers on GETs (Cache-Control, ETag) where appropriate, and none on private data.

## 7. API security (cross-reference F; do not duplicate)

Walk the OWASP API Security Top 10 (2023) as a lens, and file each finding once, under F:
API1 BOLA · API2 broken authentication · API3 broken object-property-level authorisation (mass assignment / excessive data exposure) · API4 unrestricted resource consumption · API5 broken function-level authorisation · API6 unrestricted access to sensitive business flows · API7 SSRF · API8 security misconfiguration · API9 improper inventory management (shadow, zombie or undocumented endpoints, old versions still live) · API10 unsafe consumption of third-party APIs.

API9 is particularly relevant here: compare the routes actually registered in code with the published spec and the gateway routes. Undocumented live endpoints are a finding.

## 8. Gateway-specific checklist

**Configuration as code**
- [ ] Gateway configuration is versioned in the repo (declarative config, CRDs, Terraform), reviewed, and promoted across environments. Admin-API-only or console-managed configuration is drift risk (`ASSUMPTION` if not visible).
- [ ] Route inventory: every route maps to a known upstream and owner; no catch-all proxies to internal networks.

**Responsibilities and their placement**
- [ ] Which concerns the gateway owns and which the services own: authentication (token validation, mTLS), coarse authorisation, rate limiting, CORS, request validation, transformation, caching, compression, TLS termination. Duplicated or *missing* concerns (each side assuming the other does it) are the classic gateway defect. Verify one concrete route end to end.
- [ ] Business logic creeping into the gateway (scripts, plugins, Lua/JS transforms with domain rules) is a WEAKNESS: it is hard to test and version.

**Identity propagation**
- [ ] How the authenticated identity reaches services: a re-signed internal token, a forwarded JWT, or trusted headers (`X-User-Id`). For trusted headers, verify the gateway **strips client-supplied copies** and that services are not reachable bypassing the gateway (network policy). Violation means identity spoofing (F, likely HIGH/CRITICAL).
- [ ] `X-Forwarded-For`/`Forwarded` handling: a trusted-proxy list is configured; rate limiting and audit logs use the real client IP.

**Traffic management and resilience** (cross-reference K)
- [ ] Per-route timeouts (connect, read, overall) and a **timeout budget** (gateway timeout > service timeout > downstream timeouts; never equal or inverted).
- [ ] Retries only on idempotent methods or with idempotency keys, bounded, with jitter; no retry multiplication across layers.
- [ ] Circuit breaking or outlier detection per upstream, and load-balancing and health-check configuration.
- [ ] Rate limits and quotas: per consumer, key or tenant, not just global; distributed counter store (Redis) sized and failure mode defined (fail-open vs fail-closed is a deliberate decision).
- [ ] Request limits: maximum body size, header size, URL length, upload streaming; slow-client (slowloris) protections.
- [ ] Graceful degradation: behaviour when an upstream is down (cached response, 503 with Retry-After, fallback).

**Security at the edge**
- [ ] TLS configuration (minimum version, HSTS), mTLS to upstreams where required.
- [ ] Header hygiene: strip hop-by-hop and internal headers outbound (`Server`, `X-Powered-By`, internal debug headers); request smuggling protections (consistent Content-Length/Transfer-Encoding handling between gateway and upstream).
- [ ] Admin API and dashboard not exposed publicly; admin authentication enforced.
- [ ] Plugins and extensions are pinned and up to date (gateway CVEs are high-impact).

**Multi-tenancy and monetisation** (if applicable)
- [ ] Tenant or plan derivation is trustworthy (from the credential, not a client header); quotas enforced per plan; noisy-tenant isolation.
- [ ] Usage metering accuracy and idempotency (billing correctness).

**Observability**
- [ ] Access logs with route, consumer, status, latency, upstream latency and trace ID; no secrets or tokens in logs.
- [ ] Metrics per route and per consumer (RED); trace context propagated (W3C `traceparent`) to upstreams.
- [ ] Alerting on 5xx ratio, latency SLOs, rate-limit saturation, and upstream health.

## 9. API engine / BFF / GraphQL specifics

- [ ] GraphQL: query depth and cost limits, persisted queries for public clients, introspection disabled or restricted in production, N+1 handled with DataLoader or batching, field-level authorisation, errors not leaking internals, pagination via connections.
- [ ] Federation and composition: schema registry and composition checks in CI, ownership per subgraph, gateway behaviour on subgraph failure (partial data plus errors).
- [ ] BFF: no business rules duplicated from core services; caching per user is correct; fan-out bounded with timeouts.
- [ ] gRPC: deadlines propagated, `buf lint`/`breaking` in CI, reflection disabled publicly, gRPC-gateway mapping consistent with REST conventions.

## 10. Tooling by authorisation level

| Level | Tools (examples) |
|---|---|
| L0 | Read the specs, route registrations, gateway configuration and git history; build the comparison tables by hand |
| L1 | `spectral lint`, `redocly lint`, `vacuum`, `oasdiff breaking <old> <new>` (old spec from git history), `buf lint` / `buf breaking`, `graphql-inspector`, `kube-linter`/`hadolint` on gateway manifests |
| L2/L3 | Schemathesis or Dredd contract fuzzing against a local or staging instance; k6 rate-limit and timeout behaviour tests at agreed limits. Never production |

## 11. Report additions (when this profile is active)

Add to report §7 (or a dedicated §7a "API Platform Assessment"):

- An endpoint inventory summary (count by protocol and version, public vs internal, documented vs undocumented).
- A sampled conformance table: endpoint | method | contract present | error format | auth | pagination | idempotency | notes.
- A gateway responsibility matrix: concern | gateway | services | gap/duplication.
- A timeout-budget diagram (Mermaid sequence) for one critical route.
- **Optional appendix "Proposed API Standard"**: only if the user asks for it, or there is no standard and the audit purpose is modernisation. Present it as a recommendation, clearly separate from findings and never counted as defects.
