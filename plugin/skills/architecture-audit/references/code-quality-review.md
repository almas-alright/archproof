# Code Quality, Maintainability and Documentation (Domains E and P)

Judge against the conventions of the actual language and framework (PSR-12 and framework idioms for PHP; PEP 8/typing for Python; Effective Go; .NET design guidelines; Airbnb/Standard/TS strict for JS/TS; Rails conventions; Java/Kotlin idioms). Do not impose one language's style on another.

## §E Code Quality checklist

**Measure where possible (L1)**: `scc`/`cloc` (size), `lizard` (cyclomatic complexity, many languages), `radon` (Python), `phpmd`/`phpstan`/`psalm` (PHP), `eslint` complexity rules / `ts-prune` / `knip` (JS/TS unused code & deps), `gocyclo`/`staticcheck`/`golangci-lint` (Go), Roslyn analyzers (.NET), `rubocop`/`flog` (Ruby), PMD/SpotBugs/Checkstyle (Java), `jscpd` (duplication, many languages). At L0, sample manually and say "sampled".

Report numbers only from tools actually run; include the command.

- [ ] **Hotspots**: combine size/complexity with change frequency (`git log --format= --name-only | sort | uniq -c | sort -rn | head -30`). High-churn + high-complexity files are the top maintainability risks — this is more useful than raw averages.
- [ ] Long methods/large classes/excessive nesting — cite the worst 5–10 with metrics.
- [ ] Duplication: copy-pasted business rules (high impact) vs boilerplate (low).
- [ ] Dead code: unreferenced classes/routes/feature flags, commented-out blocks, unused dependencies (cross-reference domain A).
- [ ] Naming consistency and domain language.
- [ ] Error handling: swallowed exceptions (`catch {}`; `except: pass`; `_ = err`), catch-all that hides failures, errors returned as 200, lost stack traces, inconsistent error types across layers, panics/fatal in library code.
- [ ] Type safety: TS `any`/`@ts-ignore` density and `strict` off; PHP without `declare(strict_types=1)`/types; Python without type hints on public interfaces (and no mypy/pyright); unchecked casts.
- [ ] Validation: at boundaries (request DTOs, form requests, pydantic/zod/class-validator/Bean Validation), not scattered.
- [ ] Organisation: by feature vs by layer; consistent module layout.
- [ ] Separation of business logic and infrastructure (cross-reference domain B; do not duplicate).
- [ ] Testability: hard-coded time/randomness/network, static calls, `new` in business logic.
- [ ] Lint/format tooling present and enforced in CI.
- [ ] Technical debt markers: `TODO/FIXME/HACK/XXX` count and age (`git blame`); suppressed analyser warnings.

**Severity**: code quality issues are usually LOW–MEDIUM. Raise only when tied to defect risk in a critical flow, or when a hotspot demonstrably slows delivery (git evidence).

## Technical debt register entries

For each significant debt item: item, root cause (time pressure, missing ownership, outgrown design), business impact, engineering impact, remediation strategy (incremental), priority. Feeds report §16.

## §P Documentation and Architecture Governance checklist

- [ ] README: does following it actually set up the project? Compare commands to `package.json` scripts/Makefile/compose. Stale steps = documentation drift.
- [ ] Architecture docs and diagrams: match Phase 2 observed architecture?
- [ ] ADRs: present, dated, status maintained, decisions still in force?
- [ ] API docs: OpenAPI/GraphQL schema generated from code or hand-written (drift risk); compare 3–5 endpoints to implementation.
- [ ] Database docs/ER diagrams.
- [ ] Deployment instructions and runbooks (incident, rollback, restore, rotate secrets).
- [ ] Dependency/licence docs.
- [ ] Onboarding time indicators: local setup automation (devcontainer, compose, seed data).
- [ ] Ownership: CODEOWNERS, module owners.

Missing documentation is `WEAKNESS` or `IMPROVEMENT`, never a vulnerability. Documentation that is *wrong* in a way that causes unsafe operation (e.g. a rollback runbook that would drop data) can be MEDIUM/HIGH.
