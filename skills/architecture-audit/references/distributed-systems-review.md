# API, Distributed Systems and Reliability (Domains I, J, K)

Apply only what the actual architecture needs. A single-process app with one DB and no queues gets a short §J (concurrency within the process and DB) — do not recommend sagas or outboxes for it without a real cross-boundary consistency problem.

## §I API and Integration Architecture

> If the API is the product, or the system is an API engine or gateway, also apply `api-platform-review.md`.

- [ ] Protocols in use (REST, GraphQL, gRPC, WebSocket, SOAP, SSE) and why.
- [ ] Consistency: naming, resource modelling, status codes, error envelope (e.g. RFC 9457 problem details), date/money formats, casing.
- [ ] Versioning strategy (URI, header, schema evolution); breaking changes without versioning (compare git history of DTOs/schemas).
- [ ] Request validation at the boundary; unknown-field handling.
- [ ] Response contracts: explicit DTOs vs leaking ORM entities.
- [ ] Error handling: internal details leaked; consistent mapping of domain errors.
- [ ] AuthN/AuthZ per endpoint (owner: domain F — cross-reference only).
- [ ] Pagination (cursor vs offset), max page size, filtering/sorting allow-lists.
- [ ] Idempotency for POST/payment/order endpoints (`Idempotency-Key`, unique constraints).
- [ ] **Outbound integrations**: for every HTTP/SDK client record timeout (connect + read), retries (count, backoff, jitter, which errors), circuit breaker, fallback. Missing timeouts on outbound calls in request paths are a common HIGH reliability finding — but verify defaults (some clients default to infinite: Python `requests`, Go `http.DefaultClient`, Node `fetch`/axios default 0; others have defaults).
- [ ] Webhook handling (receiving): signature verification (domain F), fast ack + async processing, dedup by event ID, out-of-order tolerance.
- [ ] Webhook sending: retries, signing, backoff, dead-letter.
- [ ] Contract compatibility: consumer-driven contract tests, schema registry, generated clients.
- [ ] API documentation accuracy (cross-reference P).

## §J Distributed Systems and Concurrency

**In-process and DB concurrency (always check)**
- [ ] Read-modify-write races: balance/stock/counter updates without atomic SQL (`UPDATE … SET x = x - 1 WHERE x >= 1`), row locks, or optimistic versioning.
- [ ] Check-then-act uniqueness without DB constraint.
- [ ] Double-submit: duplicate orders/payments from retries or double clicks.
- [ ] Locks: lock ordering (deadlocks), distributed locks (Redis `SET NX PX` with fencing? Redlock caveats), lock held across I/O.
- [ ] Shared mutable state in multi-threaded runtimes (Java, Go, .NET): unsynchronised maps, data races (`go test -race` at L2).
- [ ] Scheduled jobs running concurrently on multiple instances (no leader election/lock).

**Cross-boundary consistency (only if multiple services/stores/brokers)**
- [ ] Dual writes: DB commit + message publish without outbox → lost or phantom events. Look for `save(); publish();` sequences.
- [ ] Consumers: at-least-once delivery assumed? Idempotent handlers (inbox/dedup table)? Message ordering assumptions vs partitioning keys?
- [ ] Retries: exponential backoff + jitter, max attempts, DLQ, poison-message handling; retry storms (synchronized retries, retries at multiple layers multiplying load).
- [ ] Distributed transactions: 2PC usage; sagas with compensations defined for every step; orchestration vs choreography clarity.
- [ ] Eventual consistency made visible to users where needed (read-your-writes).
- [ ] Service discovery and communication: hardcoded hosts, DNS caching, mTLS.
- [ ] Failure isolation: bulkheads (separate pools/queues per dependency), timeouts shorter than callers' timeouts (timeout budget).
- [ ] Distributed tracing propagation (W3C `traceparent`) across HTTP and messages (owner: N — cross-reference).

## §K Reliability and Fault Tolerance

- [ ] Failure propagation map: for each critical dependency (DB, cache, broker, each external API) — what happens to user-facing flows when it is down or slow? Fill a table: dependency | failure mode | current behaviour (cite code) | blast radius | mitigation present.
- [ ] Single points of failure (cross-reference B; own the *operational* aspect here).
- [ ] Circuit breakers / retries / timeouts configured (resilience4j, Polly, opossum, gobreaker, tenacity, Laravel retry helpers) and actually wrapped around the calls.
- [ ] Graceful degradation: optional features (recommendations, analytics) failing closed vs breaking the page.
- [ ] Health checks: liveness vs readiness separated; readiness checks dependencies sensibly (not cascading restarts when the DB blips).
- [ ] Graceful shutdown: SIGTERM handling, draining in-flight requests and jobs.
- [ ] Recovery: backups configured (IaC), restore procedure documented **and tested**, RPO/RTO stated anywhere?
- [ ] Disaster recovery: multi-AZ/region config, data replication.
- [ ] Data integrity under partial failure (transactions spanning steps, compensations).
- [ ] Operational resilience: feature flags/kill switches, rate limits, runbooks.

Reliability findings without runtime evidence describe *behaviour implied by code* — say so, and give a chaos/fault-injection test as `runtime_verification_needed` (e.g. "block DB port in docker-compose, observe API status codes and recovery time").
