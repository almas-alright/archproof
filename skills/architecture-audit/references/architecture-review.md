# Architecture Review (Domains B and D)

## §B System Architecture

### Identify the style (evidence first)

| Signal | Points to |
|---|---|
| One deployable, one DB, modules by technical layer (`controllers/`, `models/`) | Layered monolith |
| One deployable, folders by business capability with explicit public interfaces, internal packages | Modular monolith |
| `domain/` with no framework imports, `application/`, `infrastructure/`, ports/adapters interfaces | Clean / Hexagonal |
| Multiple deployables, separate DBs, network calls between them | Microservices |
| Multiple deployables sharing one DB schema | Distributed monolith (flag) |
| Aggregates, value objects, domain events, ubiquitous language in names | DDD (verify it is real, not naming only) |

State the style as **observed** and, separately, the **intended** style if documented. Gaps are *architectural drift*.

### Checklist

- [ ] **Boundaries**: are module boundaries enforced (package visibility, `internal/` in Go, PHP namespaces + deptrac, ArchUnit, eslint-plugin-boundaries, Nx tags, .NET project references) or only by convention?
- [ ] **Dependency direction**: do domain/core modules import framework, ORM, HTTP or infrastructure code? Build an import graph (`madge`, `depcruise`, `deptrac`, `jdeps`, `go list -deps`, `pydeps`, NDepend) at L1, or by grep at L0.
- [ ] **Circular dependencies** between modules/packages — list each cycle with files.
- [ ] **Coupling/cohesion**: modules reaching into each other's tables, models, or private classes; "shared"/"common"/"utils" packages that everything depends on.
- [ ] **Business-logic placement**: logic in controllers, views, ORM hooks/observers, DB triggers, stored procedures, frontend — is it duplicated across them?
- [ ] **Data ownership**: does each table/collection have one writing module/service? Cross-service direct DB access?
- [ ] **Cross-module communication**: in-process calls vs events vs HTTP; synchronous chains (A→B→C→D) on the request path.
- [ ] **Shared infrastructure**: one Redis/DB/queue for unrelated workloads (noisy-neighbour & blast radius).
- [ ] **Hidden dependencies**: global state, service locators, static singletons, env-var coupling, implicit ordering of boot/migrations, cron jobs that other features rely on.
- [ ] **Single points of failure**: single DB without replica, single worker, single region, in-memory session store, leader-only scheduler.
- [ ] **Configuration architecture**: 12-factor config vs hardcoded per-environment branches.
- [ ] **Frontend architecture** (if present): state management, API client layer, rendering model (SSR/CSR/SSG), bundle boundaries, auth token handling.
- [ ] **Architectural decision quality**: ADRs exist? Decisions reversible? Do they match constraints recorded in Phase 0?

### Good decisions to look for and preserve

Clear bounded modules; a thin controller layer; explicit transactions at the application-service level; idempotent consumers; a pragmatic monolith for a small team; strong typing at boundaries; contract-first APIs.

### Typical evidence for a finding

"`app/Http/Controllers/OrderController.php:88-161` computes tax, applies discounts and writes three tables inside the controller; same discount logic duplicated in `app/Jobs/RecalculateCart.php:40-77`." — not "business logic seems to be in controllers".

## §D Design Patterns and Principles

### Approach

1. Inventory patterns actually present (name, location, purpose).
2. For each: correct, misapplied, unnecessary, or inconsistent?
3. Only recommend a pattern when a concrete, present problem justifies it (change frequency, multiple implementations, testability pain observed). Cite that problem.

### Checklist

- [ ] **SOLID** — assess concretely:
  - SRP: classes with multiple reasons to change (cite method groups).
  - OCP: switch/if chains on type codes that grow with each feature (check git log frequency).
  - LSP: subclasses that throw "not supported" or weaken contracts.
  - ISP: fat interfaces with implementers leaving methods empty.
  - DIP: high-level policy constructing concrete infrastructure (`new HttpClient()`, `new PDO`) inside business code.
- [ ] **DI**: container used correctly vs service locator anti-pattern; constructor injection; scoped lifetimes correct (e.g. .NET scoped-in-singleton capture; Spring prototype into singleton).
- [ ] **Repository**: real abstraction over persistence, or a pass-through wrapper over an ORM that already is a repository (unnecessary layer)? Leaking query builders out of repositories?
- [ ] **Service layer**: transaction boundaries, orchestration vs domain logic, god services (> ~15 public methods across unrelated concerns, or > ~800 LOC — thresholds are signals, not rules).
- [ ] **Factory / Strategy / Adapter / Decorator / Observer / Command**: used where variation exists; adapters isolate third-party SDKs.
- [ ] **Domain events / Observer**: synchronous listeners doing I/O inside transactions; ordering assumptions; events dispatched before commit (lost or phantom events).
- [ ] **CQRS / Event sourcing**: justified by read/write asymmetry or audit needs? Projections rebuildable? Snapshotting? Versioned events?
- [ ] **Unit of Work**: one commit per use case vs many implicit commits.
- [ ] **Middleware**: cross-cutting concerns (auth, logging, rate limit) consistently applied, order correct.
- [ ] **Abstraction level**: interfaces with exactly one implementation and no test seam need — flag as `IMPROVEMENT`/`TRADE_OFF`, not defect.
- [ ] **Anti-patterns**: god objects, anemic domain model (only flag if the domain is complex enough to need behaviour), deep inheritance (> 3 levels), feature envy, shotgun surgery (one change touching many files — evidence from git history), primitive obsession on money/IDs.
- [ ] **Consistency**: same problem solved three different ways across modules.

### Severity guidance

Design issues are rarely above MEDIUM unless they directly cause defects, data corruption, or block a stated business goal. Overengineering is a real cost — record it with the same rigour as underengineering.
