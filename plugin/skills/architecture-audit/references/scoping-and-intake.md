# Phase 0 — Scoping and Intake

The purpose is to establish business context and authority *before* judging anything. Recommendations that ignore context (team size, stage, regulatory exposure) are the most common reason audits are dismissed.

## 1. Questions to ask (batch them; ask at most once)

Ask only what you cannot infer from the repository. If the user is unavailable or says "just run it", proceed with the defaults in brackets and record them as assumptions in the report.

| # | Question | Default if unanswered |
|---|---|---|
| 1 | Full audit or specific domains? Which? | Full audit |
| 2 | What does the application do and for whom? Revenue-critical flows? | Infer from code/README; mark as inferred |
| 3 | Audit purpose: internal health check, pre-scale readiness, due diligence (acquisition/investment), security assurance, modernisation planning? | Internal health check |
| 4 | Expected scale: current users/traffic (if known), growth target in 12–24 months | Unknown — 10x/100x scenarios become qualitative |
| 5 | Team size and seniority; who will maintain it | Unknown |
| 6 | Regulatory/data context: PII, payments (PCI DSS), health data, GDPR/local data-protection law, multi-tenant SaaS | Assume PII present if user/account tables exist |
| 7 | Deployment target: cloud provider, on-prem, Kubernetes, serverless | Infer from IaC/CI |
| 8 | Out-of-scope areas (vendored code, legacy modules, generated code) | Vendored + generated code excluded |
| 9 | Runtime authorisation: may the auditor run tests, linters, dependency scanners, the app locally, profilers? Against which environment? | Static only; no execution of project code |
| 10 | Report audience and confidentiality (internal team / board / third party) | Engineering leadership, confidential |
| 11 | Output location | `architecture-audit-output/<YYYY-MM-DD>/` |

## 2. Authorisation levels

Record exactly one level in the report metadata.

| Level | Allowed | Not allowed |
|---|---|---|
| **L0 Static** (default) | Read files, git history, grep, parse manifests | Executing any project code or tools that resolve dependencies over the network |
| **L1 Tooling** | L0 + run read-only analysers that do not execute project code (e.g. `semgrep`, `gitleaks`, `osv-scanner`, `npm audit --omit=dev`, `pip-audit -r`, `trivy fs`, `cloc`/`scc`, complexity tools) | Installing deps into the project, modifying lockfiles |
| **L2 Local runtime** | L1 + run the test suite, start the app locally/in a container, profile (heap snapshots, pprof, tracemalloc, JFR), small controlled benchmarks | Any shared/staging/production environment |
| **L3 Staging runtime** | L2 against a named non-production environment, with agreed limits on load and duration | Production; destructive tests; data exfiltration |

Production is never in scope for active testing from this skill.

## 3. Pin the audit baseline

- Record `git rev-parse HEAD`, branch, and `git status --porcelain` (uncommitted changes must be noted — findings refer to the working tree).
- If not a git repo, record a SHA-256 over the sorted file list + sizes (the validator does this automatically) and say so.
- Record the audit date (local timezone) and the auditor identity: "Claude (model name if known) using the ArchProof plugin".

## 4. Scope statement (write this into `inventory.md` and report §1)

```
Scope: <full | domains A,F,O>
Purpose: <...>
Baseline: <repo> @ <commit> (<branch>), working tree <clean|dirty>
Authorisation: <L0..L3> — <details>
Included paths: <...>
Excluded paths: <vendor/, node_modules/, generated/, ...> — reason
Assumptions: <numbered list, each later confirmed or left as ASSUMPTION>
```

## 5. Audit plan (present before large work)

Include: domains and order, partitioning (by service/bounded context), subagent plan or sequential, tools to run at the authorised level, expected deliverables, known limitations. Wait for approval unless the request is small and explicit.
