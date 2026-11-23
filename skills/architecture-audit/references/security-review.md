# Application Security Review (Domains F and O)

Reference frameworks: OWASP ASVS (record version), OWASP Top 10 (record edition), OWASP API Security Top 10 2023, CWE. Map each vulnerability to a CWE ID and, where confident, an ASVS requirement.

**Rules of engagement**: static analysis by default. No exploitation against any running system without L2/L3 authorisation; never production; no credential extraction; no data exfiltration; redact secrets.

## 1. Attack-surface map (do this first)

List every entry point: HTTP routes (with auth middleware applied), GraphQL operations, gRPC methods, WebSockets, webhooks, file upload endpoints, queue consumers fed by external producers, CLI/cron jobs reading external data, admin panels, debug/actuator/health endpoints, static file serving. Table: entry | method | auth required? | roles | input sources | file.

Tip: find routes with **no** auth middleware first; then routes whose handler takes an ID from the request.

## 2. Taint-trace procedure (mandatory for every suspected vulnerability)

Fill all eight fields in the finding's `attack_path`:

1. **Entry point** — route/handler, file:line.
2. **Attacker-controlled input** — which parameter/header/body/file/claim.
3. **Validation & sanitisation** — what is applied, where; is it bypassable (type juggling, encoding, allow vs deny list)?
4. **Authorisation checks** — authentication *and* object-level ownership check; where enforced (middleware, policy, query scope, none).
5. **Vulnerable operation (sink)** — query, shell, file path, template, deserialiser, outbound request, redirect.
6. **Existing mitigations** — framework auto-escaping, ORM parameterisation, WAF/gateway (only if config is in repo), CSP, network policy.
7. **Preconditions** — authenticated? role? feature flag? specific config?
8. **Impact** — confidentiality/integrity/availability, data classes affected, tenant scope.

If any link cannot be established from code, the finding is at most `PARTIALLY_CONFIRMED` / type `RISK`.

## 3. Checklist (§F)

**Access control** (highest yield in real audits)
- [ ] Object-level authorisation (IDOR/BOLA): every handler loading a resource by ID checks ownership/tenant. Look for `findOrFail($id)`, `findById(id)`, `get_object_or_404(Model, pk=...)`, `.findByPk(req.params.id)` without a scope.
- [ ] Function-level authorisation: admin routes protected server-side, not just hidden in UI.
- [ ] Mass assignment / over-posting: `$guarded = []`, `fill($request->all())`, `@ModelAttribute` binding entities, `Model(**request.json)`, `Object.assign(user, req.body)`, Rails `permit!`. Can a user set `role`, `is_admin`, `tenant_id`, `price`?
- [ ] Privilege escalation via role-change endpoints, invitation flows, impersonation features.
- [ ] Multi-tenant isolation enforcement point (global scope / RLS / repository filter) and bypasses (raw queries, background jobs, exports, search indices, caches keyed without tenant).

**Injection**
- [ ] SQL: string concatenation/interpolation into queries, `whereRaw`, `DB::raw`, `.raw()`, `extra()`, `createNativeQuery`, `fmt.Sprintf` into `db.Query`, `FromSqlRaw` with interpolation; ORDER BY / column names from input.
- [ ] NoSQL: operator injection (`{"$ne": null}`) via unvalidated JSON bodies into Mongo queries.
- [ ] OS command: `exec`, `system`, `shell_exec`, `child_process.exec`, `subprocess(..., shell=True)`, `Runtime.exec` with input.
- [ ] Template injection (SSTI): user input as template source.
- [ ] LDAP/XPath/header (CRLF) injection; log injection.

**Client-side**
- [ ] XSS: raw output (`{!! !!}`, `|safe`, `mark_safe`, `dangerouslySetInnerHTML`, `v-html`, `innerHTML`, `html_safe`, `@Html.Raw`); markdown renderers without sanitiser; JSON embedded in HTML without escaping.
- [ ] CSRF: cookie-authenticated state-changing routes without CSRF tokens or SameSite; excluded routes lists.
- [ ] CORS: `Access-Control-Allow-Origin` reflecting origin with credentials; wildcard + credentials; overly broad regex.
- [ ] Security headers: CSP, HSTS, X-Content-Type-Options, frame-ancestors, Referrer-Policy (only if the app sets headers; note if a proxy is responsible and its config is absent → `ASSUMPTION`).
- [ ] Open redirects on `next`/`returnUrl` parameters.

**Server-side request & files**
- [ ] SSRF: outbound fetch of user-supplied URLs (webhook URLs, image fetchers, PDF renderers, import-from-URL); check allow-lists, DNS-rebinding protection, blocking of metadata IPs (169.254.169.254), redirect following.
- [ ] Path traversal: file paths built from input (`../`), zip-slip in archive extraction, download endpoints serving by filename.
- [ ] File upload: type validation by content not extension, size limits, storage outside web root, randomised names, no execution, image-processing library CVEs, SVG XSS.
- [ ] Insecure deserialisation: `unserialize`, `pickle.loads`, `yaml.load` (unsafe loader), Java native serialisation, `BinaryFormatter`, `Marshal.load`, polymorphic Jackson typing, `node-serialize`.
- [ ] XXE: XML parsers with external entities enabled.

**Authentication & session**
- [ ] Password storage: bcrypt/argon2id/scrypt/PBKDF2 with adequate cost; no MD5/SHA1/unsalted; legacy hash migration path.
- [ ] Login: rate limiting/lockout, user enumeration via messages/timing, MFA availability for admins.
- [ ] Password reset: token entropy, expiry, single use, not logged, host-header poisoning of reset links.
- [ ] Sessions: secure/HttpOnly/SameSite cookies, rotation on login and privilege change, server-side invalidation on logout/password change, idle and absolute timeouts.
- [ ] JWT: algorithm pinned (no `none`, no HS/RS confusion), signature verified (not just decoded), `exp`/`aud`/`iss` validated, secret strength, storage location (localStorage → XSS exposure), revocation strategy, refresh-token rotation and reuse detection.
- [ ] OAuth/OIDC: `state` and PKCE, redirect URI exact match, ID token validation, account linking by unverified email.
- [ ] API keys: hashed at rest, scoped, rotatable.

**Crypto & secrets**
- [ ] Algorithms: no ECB, static IVs, homemade crypto, `Math.random`/`rand()` for tokens; TLS verification not disabled (`verify=False`, `rejectUnauthorized: false`, `InsecureSkipVerify`).
- [ ] Secrets in repo: `.env` committed, keys in config, CI files, Docker images, test fixtures, **git history** (`git log -p -S` at L0, `gitleaks` at L1). Report location + type only; redact the value. A committed secret is CONFIRMED exposure even if "rotated" unless rotation evidence exists.
- [ ] Environment config: debug mode in production config, verbose errors, `APP_DEBUG=true`, Django `DEBUG=True`, Spring actuator exposure, stack traces returned to clients.

**API & abuse**
- [ ] Rate limiting on auth, expensive, and enumeration-prone endpoints.
- [ ] Unbounded page sizes, GraphQL depth/complexity limits, batch endpoints.
- [ ] Excessive data exposure: serialising whole entities (password hashes, internal flags) to clients.
- [ ] Webhook verification: HMAC signature check with constant-time compare, timestamp tolerance against replay, idempotent processing.

**Dependencies** (owner of version inventory is domain A; security impact owned here)
- [ ] Known CVEs via `osv-scanner`, `npm audit`, `composer audit`, `pip-audit`, `govulncheck`, `dotnet list package --vulnerable`, `bundle audit`, `trivy` (L1). At L0, flag versions you *know* are vulnerable as `RISK` with "confirm with scanner".
- [ ] Reachability: is the vulnerable function used? Unreachable → lower likelihood.

**Logging**
- [ ] Passwords, tokens, full card numbers, session IDs, PII written to logs or error trackers.

## 4. Data Privacy and Governance (§O)

- [ ] PII inventory: which tables/fields hold personal data (names, emails, phones, addresses, IDs, location, health, financial). Produce a table.
- [ ] Encryption in transit (TLS for DB/cache/queue connections, internal service calls) and at rest (DB/storage encryption flags in IaC; field-level encryption for highly sensitive fields).
- [ ] Data minimisation: collecting fields never used.
- [ ] Retention and deletion: account deletion actually removes/anonymises across DB, backups policy, search, caches, analytics, third parties; soft-delete-only for PII.
- [ ] Data export/subject-access capability (if regulated).
- [ ] Access policies: who can read production data; admin tooling audit trail.
- [ ] Backup exposure: public buckets, unencrypted dumps in repo or CI artefacts.
- [ ] Third-party sharing: analytics/tracking SDKs receiving PII.

Do not give legal conclusions ("GDPR compliant"). State technical facts and point to where legal review is needed.

## 5. Severity hints

CRITICAL candidates: unauthenticated RCE/SQLi, cross-tenant data access, authentication bypass, committed production secrets with live scope. Everything still must pass the confidence rules in `severity-risk-model.md`.
