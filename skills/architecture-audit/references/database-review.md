# Database and Schema Review (Domain C)

Review the **actual definitions**: migrations (in order), ORM model/entity mappings, schema dumps (`schema.rb`, `structure.sql`, `schema.prisma`, Liquibase/Flyway changelogs, EF Core migrations & `ModelSnapshot`, Alembic versions, Django migrations, Doctrine mappings, GORM tags), raw SQL, repository code and DB config. Never judge from entity or migration file names alone.

## 1. Reconstruct the schema

- Replay migrations mentally in order (or read the latest snapshot); note later migrations that alter/drop earlier columns.
- Produce a table list with: PK, FKs, unique constraints, indexes, notable columns, row-growth expectation (inferred).
- Compare ORM mapping vs migrations: columns declared in models but missing in migrations (or vice versa) = drift.

## 2. Checklist

**Structure and integrity**
- [ ] Every table has a PK; PK type appropriate (bigint/UUID; UUIDv4 as clustered PK on InnoDB/SQL Server causes page splits — prefer UUIDv7/ULID or a surrogate bigint).
- [ ] FKs declared at DB level for real relationships (not only in the ORM). Missing FKs → orphan risk. Note when FKs were intentionally omitted (sharding, Vitess/PlanetScale) — trade-off, not defect.
- [ ] `ON DELETE` behaviour deliberate (cascade vs restrict vs set null).
- [ ] Unique constraints enforce business uniqueness (email per tenant, idempotency keys, external IDs). Application-only uniqueness checks race (check-then-insert).
- [ ] CHECK constraints / enums for constrained values; status columns as free text.
- [ ] Nullability matches the domain; NOT NULL without defaults on large tables in migrations.
- [ ] Data types: money as decimal/integer minor units (never float); timestamps with time zone/UTC discipline; text lengths; JSON columns used for queryable data (flag); booleans as strings.
- [ ] Normalisation: repeated groups, comma-separated IDs in a column, denormalised copies without a sync mechanism. Denormalisation acceptable when deliberate and maintained.

**Indexes**
- [ ] Index every FK column used in joins/deletes (Postgres does not auto-index FKs).
- [ ] Composite index column order matches query predicates (equality first, then range/sort).
- [ ] Missing indexes for: columns in `WHERE`, `ORDER BY` + `LIMIT`, tenant_id prefixes in multi-tenant tables, soft-delete filters.
- [ ] Redundant indexes (prefix duplicates), unused indexes on write-heavy tables.
- [ ] Queries defeating indexes: `LIKE '%x'`, functions on indexed columns, implicit casts, `OR` across columns.

**Query patterns**
- [ ] N+1: loops issuing queries; ORM lazy loading in serializers/templates (`with()`/`includes`/`select_related`/`prefetch_related`/`JOIN FETCH`/`Include` missing). Cite loop + relation access lines.
- [ ] Unbounded selects (`all()`, `findAll()`, `SELECT *` without LIMIT) on growing tables; offset pagination on large tables (prefer keyset).
- [ ] Full scans implied by predicates with no index; `COUNT(*)` on large tables per request.
- [ ] Raw SQL built by string concatenation (also a security finding — owner: domain F).
- [ ] Transactions: boundaries around multi-write use cases; external calls (HTTP, email, queue publish) inside open transactions; isolation level assumptions; `SELECT … FOR UPDATE` where read-modify-write races exist; long transactions holding locks.
- [ ] Connection management: pool size vs worker/process count (e.g. `pool × instances × workers` vs DB `max_connections`); PgBouncer transaction mode incompatibilities (prepared statements, session state); connections leaked in error paths.

**Migrations and change safety**
- [ ] Reversible (down migrations or documented forward-fix policy).
- [ ] Zero-downtime safety: adding NOT NULL without default, renaming columns used by running code, building indexes without `CONCURRENTLY`/`ONLINE`, large backfills inside the migration transaction, table rewrites on big tables.
- [ ] Migrations coupled to deploy order (expand/contract pattern followed?).
- [ ] Data migrations mixed with schema migrations.

**Lifecycle and governance**
- [ ] Soft deletes: unique constraints that ignore `deleted_at` (duplicates blocked or allowed wrongly); queries forgetting the filter; GDPR erasure conflicts.
- [ ] Audit history: who/when/what for sensitive entities; append-only?
- [ ] Retention/archival for high-growth tables (logs, events, notifications).
- [ ] Multi-tenancy model: shared schema + tenant_id (enforced how? global scopes, RLS, repository filter) vs schema-per-tenant vs DB-per-tenant. Every tenant-scoped query must filter — sample at least the top 10 queries. Cross-tenant leak = domain F/O owner, CRITICAL candidate.
- [ ] Scalability: read replicas and replica-lag-sensitive reads; partitioning candidates; hot rows (counters, sequences); sharding readiness only if Phase 0 growth demands it.

**NoSQL / caches / search** (if present)
- [ ] Document size growth, unbounded arrays, missing indexes, query by unindexed fields.
- [ ] Redis: key TTLs, eviction policy, used as primary store without persistence, `KEYS *` in code.
- [ ] Search index sync strategy and drift.

## 3. Runtime verification (L2+)

`EXPLAIN (ANALYZE, BUFFERS)` / `EXPLAIN FORMAT=JSON` on a local copy with representative data only; never on production. Without runtime, write "requires EXPLAIN on representative data" in the finding's `runtime_verification_needed`.

## 4. Report section content

Schema overview (ER diagram), relationships, indexing assessment, constraints, transaction management, query efficiency, data integrity, migration strategy — each with evidence and positive observations.
