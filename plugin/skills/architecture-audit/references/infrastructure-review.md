# Technology Stack, DevOps and Infrastructure (Domains A and M)

## §A Technology Stack and Dependency Audit

### Inventory table (required output)

| Component | Technology | Declared version | Resolved version (lockfile) | Support status | EOL date | Source checked | Notes |
|---|---|---|---|---|---|---|---|

- Support status: `SUPPORTED`, `SECURITY_ONLY`, `EOL`, `UNKNOWN`. Confirm EOL dates against official sources or endoflife.date when web access exists; otherwise mark "unverified — auditor knowledge" and never state a specific date as fact.
- Cover: languages/runtimes, frameworks, databases and engines, brokers, caches, base Docker images, OS images, major libraries (ORM, auth, HTTP, serialization), build tools, frontend frameworks.

### Checklist

- [ ] Lockfiles present and committed for every package manager, and CI installs strictly from them: npm's clean-install mode, Composer installing from the lock, pip hash-checking mode or uv/Poetry frozen sync, Go module checksums (`go.sum`), .NET locked-mode restore, Bundler frozen mode.
- [ ] Deprecated/abandoned packages (registry deprecation flags, archived repos, no releases > 2 years — verify before claiming).
- [ ] Known vulnerabilities — run scanners at L1 (see security-review §3 Dependencies); security impact is owned by domain F, inventory here.
- [ ] Duplicated libraries solving the same problem (two HTTP clients, three date libraries, moment + dayjs).
- [ ] Version conflicts / multiple major versions in lockfile; peer dependency warnings; framework-plugin compatibility.
- [ ] Unused dependencies (`depcheck`/`knip`, `composer-unused`, `deptry`, `go mod tidy -diff`).
- [ ] Dev dependencies shipped to production images.
- [ ] Licences: copyleft (GPL/AGPL) in proprietary distributed or SaaS products (AGPL network clause), unknown licences. Tools: `license-checker`, `pip-licenses`, `go-licenses`, `trivy fs --scanners license`. Not legal advice — flag for legal review.
- [ ] Build tooling health (outdated bundlers, custom unmaintained scripts).
- [ ] Technology complexity: number of languages/datastores/frameworks relative to team size (Phase 0); unnecessary polyglot.
- [ ] Obsolescence trajectory: what becomes EOL in the next 12 months.

## §M DevOps and Infrastructure

**Containers**
- [ ] Base images pinned (tag + ideally digest), minimal (distroless/alpine/slim), not EOL.
- [ ] Multi-stage builds; no build tools/secrets in final image; `.dockerignore` excludes `.env`, `.git`.
- [ ] Runs as non-root; read-only filesystem where possible; no `--privileged`; dropped capabilities.
- [ ] Healthcheck defined; one process per container (or proper init).
- [ ] Secrets passed via build args or baked `ENV` (visible in image history) — flag.

**Orchestration / runtime config**
- [ ] Kubernetes: resource requests/limits, liveness/readiness/startup probes, PodDisruptionBudgets, HPA, securityContext, NetworkPolicies, secrets via external secret store, image pull policy.
- [ ] Serverless: timeouts, memory, concurrency limits, cold-start-sensitive paths, IAM least privilege.
- [ ] Environment management: dev/staging/prod parity; config per environment via env vars or config service, not code branches.

**Infrastructure as Code**
- [ ] Present for all environments? Manual (ClickOps) resources inferred from references to unknown hosts → `ASSUMPTION`.
- [ ] State management (remote state, locking), modules versioned.
- [ ] Security: public buckets, open security groups (0.0.0.0/0 on DB ports), unencrypted storage, wildcard IAM, missing logging. Tools at L1: `checkov`, `tfsec`/`trivy config`, `kube-linter`, `hadolint`.
- [ ] Drift risk: IaC vs documented architecture.

**CI/CD**
- [ ] Pipeline stages: lint, test, build, scan (SAST/SCA/secrets/container), deploy.
- [ ] Tests actually block merges/deploys (not `continue-on-error`, not `|| true`).
- [ ] Pipeline security: pinned third-party actions (by SHA), least-privilege tokens (`permissions:` in GitHub Actions), secrets not echoed, `pull_request_target` misuse, self-hosted runner exposure.
- [ ] Artifact provenance/signing (SLSA, cosign) — improvement unless regulated.
- [ ] Deployment strategy: rolling/blue-green/canary; automated rollback; deploy frequency evidence from git tags.
- [ ] Database deployment coordination: migrations run before/after deploy, backward-compatible (expand/contract), locks on large tables (cross-reference C).
- [ ] Rollback procedure exists and is compatible with migrations.
- [ ] Branch protection/CODEOWNERS (if visible).

**Secrets management**
- [ ] Secret store (Vault, AWS/GCP/Azure secret managers, SOPS, sealed-secrets) vs env files on servers vs committed values.
- [ ] Rotation capability; per-environment separation.

Infrastructure not present in the repository is out of view: record it as `ASSUMPTION` with "verify in cloud console/IaC repo", not as a defect.
