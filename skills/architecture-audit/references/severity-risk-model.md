# Severity and Risk Model

Severity, likelihood, impact, confidence and verification status are **independent fields**. Do not let a high-impact theory turn into a high-confidence claim.

## 1. Severity levels

| Severity | Definition |
|---|---|
| **CRITICAL** | Immediately exploitable or highly consequential issue with severe security, data-integrity or business impact (e.g. unauthenticated data access, cross-tenant leakage, auth bypass, silent financial data corruption on the main path). |
| **HIGH** | Significant security, availability, reliability, data-integrity or architectural risk (e.g. authenticated IDOR, missing timeouts on the critical path that can exhaust workers, dual-write losing orders). |
| **MEDIUM** | Material engineering weakness creating measurable or plausible maintenance, performance or operational risk. |
| **LOW** | Limited-impact issue: maintainability, consistency, localised improvement. |
| **INFO** | Observation, positive practice (`STRENGTH`), or optional improvement. |

## 2. Likelihood (1–4)

| Score | Label | Meaning |
|---|---|---|
| 1 | Rare | Needs unusual preconditions (insider + specific config + timing). |
| 2 | Unlikely | Plausible but needs specific conditions or authenticated privileged access. |
| 3 | Likely | Will occur under normal usage/growth or by any authenticated user. |
| 4 | Almost certain | Occurs on the normal path today, or exploitable anonymously with public knowledge. |

## 3. Impact (1–4)

| Score | Label | Meaning |
|---|---|---|
| 1 | Minor | Localised inconvenience; no data or revenue effect. |
| 2 | Moderate | Degraded feature, slower delivery, limited data exposure of non-sensitive data. |
| 3 | Major | Outage of a key flow, exposure of personal data for some users, data corruption recoverable from backups, significant rework. |
| 4 | Severe | Broad sensitive-data breach, cross-tenant exposure, unrecoverable data loss, regulatory/financial consequences, prolonged outage of the core product. |

## 4. Deriving severity (documented scoring model)

Risk score = Likelihood × Impact (1–16).

| Score | Baseline severity |
|---|---|
| 12–16 | CRITICAL |
| 8–9 | HIGH |
| 4–6 | MEDIUM |
| 2–3 | LOW |
| 1 | INFO |

Then apply the **adjustment rules**, recording any deviation in `severity_rationale`:

1. **Confidence cap**: `CRITICAL` requires `verification_status = CONFIRMED` **and** `confidence = High`. Otherwise cap at `HIGH` (the validator enforces this).
2. **Unverified cap**: `UNVERIFIED` findings are capped at `MEDIUM` in the main register, with the potential severity noted in `severity_rationale` and listed under "Requires verification".
3. **Type rules**: `STRENGTH` is always `INFO`. `TRADE_OFF` and `IMPROVEMENT` are at most `MEDIUM`. `ASSUMPTION` is at most `MEDIUM`.
4. **Context override**: Phase 0 context may raise or lower by one level (e.g. internal tool with 5 users lowers availability findings) — state the reason.

## 5. Confidence

| Level | Requires |
|---|---|
| **High** | Code path fully read and traced; no unexamined mitigation could plausibly exist; for runtime claims, measured. |
| **Medium** | Pattern clearly present; some link (config elsewhere, framework default, infra layer) not verifiable from the repo. |
| **Low** | Indicative signal only; significant unknowns. Use sparingly; usually pair with `ASSUMPTION` or `RISK`. |

## 6. Verification status

`CONFIRMED` · `PARTIALLY_CONFIRMED` (core issue real, but scope, severity or path differs from the draft) · `FALSE_POSITIVE` (kept in the appendix only, with the reason) · `UNVERIFIED` (could not be checked; stated what is needed).

Only `CONFIRMED` findings may use the words "confirmed defect" or "confirmed vulnerability", or have type `DEFECT`/`VULNERABILITY`.

## 7. Remediation complexity

| Code | Meaning |
|---|---|
| S | < 1 day, local change, low risk |
| M | 1–5 days, a few modules, needs tests |
| L | 1–4 weeks, cross-cutting or needs a migration |
| XL | > 1 month, architectural change, phased rollout |

## 8. Roadmap bucket

`Immediate` (0–7 days): CRITICAL, and HIGH with complexity S. `Short-term` (1–4 weeks): remaining HIGH, and MEDIUM with complexity S. `Medium-term` (1–3 months). `Long-term` (3–6 months): XL architecture evolution. Dependencies between items override the defaults (e.g. add observability before a risky refactor).

## 9. Risk matrix

`build_report.py` generates a 4×4 likelihood/impact matrix listing finding IDs per cell from `findings.json` (excluding `STRENGTH` and `FALSE_POSITIVE`). Do not draw it by hand.
