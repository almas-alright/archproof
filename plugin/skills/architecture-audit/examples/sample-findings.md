# Sample Findings: Calibration Examples

These examples show the quality bar. Pair this file with `sample-findings.json`, which holds the same demo findings in machine format and validates against the plugin's `tests/fixtures/orders-api/` demo repository.

## 1. A well-formed confirmed vulnerability

> **F-001: SQL injection in order search via unparameterised status filter**
> Domain F · VULNERABILITY · **CRITICAL** · CONFIRMED · L3 × I4 = 12 · Confidence High · Complexity S · Immediate
>
> **Location**: `src/routes/orders.js:8-12` (mounted behind `requireAuth` at `src/server.js:8`)
> ```js
> const sql = "SELECT id, total, status FROM orders WHERE user_id = $1 AND status = '" + status + "'";
> ```
> **Attack path**: entry `GET /orders/search` → input `req.query.status` → validation: none → authorisation: any valid JWT → sink `pool.query(sql)` (line 11) → mitigations: none (the bound `user_id` is bypassed by an `OR` clause) → precondition: authenticated user → impact: read all orders, plus whatever else the DB role can reach.
> **Root cause**: string concatenation mixed with parameter binding; no validation layer for filters.
> **Remediation**: bind as `$2` and allow-list the status values; use a least-privilege DB role.
> **Verification notes**: no global validation middleware; pg does not sanitise concatenated text.

Why it is good: every link of the path is cited, the mitigation search is explicit, the severity follows the documented model, and the fix addresses the root cause.

## 2. The same issue written badly (do not do this)

> "SQL Injection — Critical. The application may be vulnerable to SQL injection in several places. Use prepared statements."

Problems: no location, no evidence, "may" combined with "Critical" (fails the confidence cap), "several places" is unverifiable, and the fix is generic.

## 3. A static memory risk, correctly bounded

> **G-001: Unbounded, never-invalidated in-process order cache**: RISK · MEDIUM · CONFIRMED (pattern) · Confidence Medium
> `src/cache.js:2-10`: `const cache = new Map();`, with no TTL, size limit or invalidation.
> **Runtime verification needed**: run locally with `--inspect`, request 50k distinct IDs, take 3 heap snapshots, and confirm the Map's retained size grows linearly.

Why it is good: it does not claim "memory leak confirmed". The code pattern is confirmed; the consequence is a risk with a concrete test that would confirm it.

## 4. An absence finding

> **L-001: No automated tests despite a configured test script**: cites `package.json:7` (the place where tests *should* be wired in) and lists what was searched for (`*.test.js`, `*.spec.js`, `test/`, `__tests__`).

Absence findings cite the location where the control belongs and record the search that came up empty. They are never typed `VULNERABILITY`.

## 5. A strength worth preserving

> **F-003: JWT verification pins algorithm, audience and issuer**: STRENGTH · INFO. `src/middleware/auth.js:8-12`. Recommendation: preserve; consider JWKS rotation.

## 6. A false positive rejected by the verifier

> **F-004: Committed environment file contains secrets** → FALSE_POSITIVE. The file is `.env.example` with placeholders, and git history contains no real `.env`.

Rejected findings stay in Appendix A, so the reader can see what was checked and why it was dismissed.

## 7. Trade-off versus defect

> "The service uses a single PostgreSQL instance." For an internal tool with 50 users and a 4-hour RTO stated in Phase 0, this is a `TRADE_OFF` (INFO/LOW) with a note on when it stops being acceptable. It is not a HIGH "single point of failure" defect.

## 8. Cross-domain de-duplication

The missing ownership check (F-002) also makes the cache (G-001) serve objects across users. Report the root cause once, under F-002, and link it: `related_findings: ["G-001"]`. Do not file a second "cache leaks data" vulnerability.

## Testing against the demo

The project repository contains the demo service these findings cite (`tests/fixtures/orders-api/`) and an automated self-test. They live outside the plugin, so installing the plugin never ships intentionally vulnerable code.
