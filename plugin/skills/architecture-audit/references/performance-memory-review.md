# Performance, Memory and Resource Review (Domains G and H)

Memory management (G) and data leakage (domain F/O) are separate concerns. "Leak" here means resources retained or never released.

## The static/runtime rule

Every finding in these domains sets `evidence_kind`:

- `STATIC` — identifiable from code/config (e.g. a cache with no eviction, a listener added per request and never removed). Max status without runtime: `CONFIRMED` for *the code pattern*, but the finding type is `RISK` unless the consequence is certain from code alone (e.g. `Map` that only ever grows with request IDs in a long-lived process).
- `RUNTIME` — confirmed by measurement (heap snapshots across N requests, pprof diff, GC logs, benchmark). Requires L2+ authorisation; attach the method and numbers in `runtime_evidence`.

Never write "memory leak confirmed" from static reading alone. Never state current latency/throughput/capacity numbers you did not measure. Always fill `runtime_verification_needed` with the exact test: what to run, what to observe, pass/fail criterion.

## §G Memory and resource checklist

**Generic**
- [ ] Unbounded in-process caches/maps/arrays keyed by user, request, tenant or URL (no TTL, no max size, no LRU).
- [ ] Module-level/static collections appended to in request handlers.
- [ ] Event listeners/subscriptions/observers registered per request/component and never removed.
- [ ] Timers/intervals not cleared; goroutines/threads/tasks started without cancellation or exit path.
- [ ] Resources not closed on error paths: DB connections, cursors, file handles, sockets, HTTP response bodies, streams.
- [ ] Loading whole files/result sets into memory (`readFile` of uploads, `fetchAll`, `.ToList()` on huge queries, `json.load` of large payloads) instead of streaming/chunking.
- [ ] Large buffers concatenated in loops; string building in loops in languages without builders.
- [ ] Long-running workers: memory growth across jobs, no max-jobs/max-memory recycle.
- [ ] Container memory limits vs runtime heap settings (JVM `-Xmx`/`MaxRAMPercentage`, Node `--max-old-space-size`, .NET `GCHeapHardLimit`, PHP `memory_limit`) — mismatch leads to OOM kills.
- [ ] Native memory: image processing, PDF generation, compression libraries, cgo, JNI.

**Language-specific**

| Stack | Static signals | Runtime method (L2+) |
|---|---|---|
| Node.js | closures capturing request objects in long-lived scopes; `EventEmitter` listeners added per request (`MaxListenersExceededWarning`); unconsumed streams; global caches; unhandled promise chains holding references | `--inspect` + Chrome DevTools heap snapshots (3-snapshot technique), `clinic doctor/heapprofiler`, `process.memoryUsage()` over load |
| Java / Spring | static collections, `ThreadLocal` without `remove()` in thread pools, classloader leaks on redeploy, unclosed `InputStream`/`Connection` (no try-with-resources), Hibernate first-level cache in long sessions/batches | JFR, GC logs (`-Xlog:gc*`), heap dump + Eclipse MAT dominator tree, VisualVM |
| PHP | long-running workers (Laravel Octane/Horizon/queue:work, Symfony Messenger, RoadRunner, Swoole) retaining static/singleton state between requests; Doctrine `EntityManager` not cleared in batch jobs; large arrays from `->get()` | `memory_get_usage()` per job, Xdebug profiler, Blackfire, worker `--max-jobs`/`--memory` |
| Python | module-level caches, `functools.lru_cache` on methods (retains `self`), reference cycles with `__del__`, Celery workers without `max_tasks_per_child`, Django `DEBUG=True` query log growth | `tracemalloc` snapshots diff, Memray, `objgraph`, `cProfile` for CPU |
| Go | goroutines blocked forever on channels, `time.After` in loops, `http.Response.Body` not closed, contexts never cancelled, slices retaining large backing arrays, unbounded maps | `net/http/pprof` heap & goroutine profiles, `runtime.NumGoroutine()`, `go test -bench -benchmem` |
| .NET | `IDisposable` not disposed (`HttpClient` per request → socket exhaustion, `DbContext` lifetime), event handler subscriptions on long-lived publishers, static caches, `IMemoryCache` without size limit | `dotnet-counters`, `dotnet-trace`, `dotnet-gcdump`, Visual Studio / JetBrains dotMemory |
| Ruby | class-level memoisation, Sidekiq memory growth, large ActiveRecord loads (`.all.each` vs `find_each`) | `derailed_benchmarks`, `memory_profiler`, `ObjectSpace` |
| Browser SPA | listeners/intervals not cleaned in unmount; stores retaining large lists; detached DOM nodes | DevTools Memory panel, Performance monitor |

**Connection pools**
- [ ] Pool size × processes × instances vs DB/Redis max connections.
- [ ] Connections held across slow external calls.
- [ ] Missing acquire timeouts → threads hang under exhaustion.

## §H Performance and scalability checklist

- [ ] **Hot paths**: identify the 3–5 most important request flows (from Phase 2) and walk each end to end: queries issued, external calls, serialization, synchronous work.
- [ ] Algorithmic complexity: nested loops over collections that scale with data (O(n²) matching, repeated `array_search`/`includes` in loops); sorting in application instead of DB.
- [ ] Database: N+1 and missing indexes (owner: domain C — cross-reference), chatty access, missing pagination.
- [ ] Synchronous blocking: sync I/O in Node event loop (`fs.readFileSync`, `crypto.pbkdf2Sync`, large `JSON.parse`), blocking calls in async Python (`requests` inside `async def`), CPU work on request threads; email/PDF/image generation inline instead of queued.
- [ ] Concurrency limits: thread pool sizes, worker counts, `GOMAXPROCS`, PHP-FPM `pm.max_children`, Gunicorn workers/threads, async event-loop saturation.
- [ ] Caching: what is cached, keys include tenant/user where needed (correctness!), TTLs, invalidation on write, stampede protection, cache as hidden dependency (cold-start behaviour).
- [ ] Payloads: over-fetching, large responses without compression, base64 files in JSON, missing field selection.
- [ ] Serialization overhead: deep ORM object graphs serialised.
- [ ] Background jobs: retries with backoff, visibility timeouts vs job duration, poison messages, priority queues, job fan-out.
- [ ] Horizontal scaling blockers: in-memory sessions, local file storage, in-process schedulers running on every instance (duplicate cron), sticky-state websockets without a shared broker.
- [ ] Vertical limits: single-threaded runtimes, memory per process.
- [ ] Rate limiting and backpressure: bounded queues, load shedding, 429 handling.
- [ ] Frontend (if present): bundle size, code splitting, image optimisation, render-blocking resources, waterfall API calls.

## 10x / 100x scenarios

Only where meaningful (Phase 0 growth target or obvious scaling exposure). Reason qualitatively from architecture: "At 10x, the per-request `COUNT(*)` on `orders` (no index on `status`) and the 20-connection pool are the first saturation points"; state the assumption and the measurement that would confirm it. No invented numbers.

## Runtime verification plan (always produce)

A table: hypothesis | tool | procedure | metric | pass/fail threshold | environment required. This goes into report §8.
