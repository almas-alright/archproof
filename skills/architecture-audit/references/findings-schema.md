# findings.json Schema

`findings.json` is the single source of truth. `report.md` narrates it; `build_report.py` generates the register and risk matrix from it; `validate_findings.py` checks it against the repository.

## Top level

```json
{
  "meta": {
    "application": "Acme Orders",
    "repository": "github.com/acme/orders (local path ./)",
    "commit": "auto",
    "depth": "standard",
    "audit_date": "2026-11-23",
    "scope": "Full audit (domains A–P)",
    "authorization_level": "L1",
    "verification_mode": "independent-subagent",
    "standards": ["ISO/IEC 25010:2023", "OWASP ASVS 5.0", "OWASP Top 10 (edition stated)", "NIST SP 800-218 v1.1", "CWE"],
    "auditor": "Claude with the ArchProof plugin"
  },
  "findings": [ { ... } ]
}
```

`commit: "auto"` lets the validator fill it in from `git rev-parse HEAD`.

## Finding object

| Field | Req | Type / enum | Notes |
|---|---|---|---|
| `id` | ✔ | `^[A-P]-\d{3}$` | Domain letter + sequence, e.g. `F-003` |
| `title` | ✔ | string ≤ 120 chars | States the problem, not the fix |
| `domain` | ✔ | `A`…`P` | Owning domain (one root cause → one owner) |
| `type` | ✔ | `DEFECT` `VULNERABILITY` `RISK` `WEAKNESS` `TRADE_OFF` `IMPROVEMENT` `ASSUMPTION` `STRENGTH` | |
| `severity` | ✔ | `CRITICAL` `HIGH` `MEDIUM` `LOW` `INFO` | |
| `severity_rationale` | cond. | string | Required when severity deviates from L×I or a cap applies |
| `verification_status` | ✔ | `CONFIRMED` `PARTIALLY_CONFIRMED` `FALSE_POSITIVE` `UNVERIFIED` | |
| `likelihood` | ✔ | int 1–4 | |
| `impact` | ✔ | int 1–4 | |
| `confidence` | ✔ | `High` `Medium` `Low` | |
| `component` | ✔ | string | From the system inventory |
| `locations` | ✔ | array of `{file, start_line, end_line}` | Repo-relative paths; lines 1-based, inclusive; `start_line`/`end_line` may be `null` only for whole-file/absence findings |
| `evidence_snippet` | ✔* | string | Verbatim code from `locations[0]` lines (≤ 15 lines). Secrets → `<REDACTED:type>`. *May be `""` only when `start_line` is null |
| `evidence_description` | ✔ | string | What the evidence shows |
| `evidence_kind` | ✔ | `STATIC` `RUNTIME` `CONFIG` `HISTORY` | `HISTORY` = git history |
| `root_cause` | ✔ | string | |
| `scenario` | ✔ | string | Execution or failure scenario, concrete |
| `business_impact` | ✔ | string | |
| `technical_impact` | ✔ | string | |
| `mitigations` | ✔ | string | Existing controls, or "None found (searched: …)" |
| `remediation` | ✔ | string | Root-cause fix; proportionate; may include a short code sketch |
| `remediation_complexity` | ✔ | `S` `M` `L` `XL` | |
| `roadmap` | ✔ | `Immediate` `Short-term` `Medium-term` `Long-term` `None` | `None` for STRENGTH/INFO |
| `runtime_verification_needed` | cond. | string | Required for domains G/H/K and for UNVERIFIED |
| `runtime_evidence` | cond. | string | Required when `evidence_kind = RUNTIME`: tool, procedure, numbers |
| `attack_path` | cond. | object with keys `entry_point`, `attacker_input`, `validation`, `authorization`, `sink`, `mitigations`, `preconditions`, `impact` | Required for `VULNERABILITY`, recommended for any F risk |
| `references` | opt. | array of strings | e.g. `CWE-639`, `ASVS V8.2.2`, `OWASP A01` |
| `related_findings` | opt. | array of IDs | Cross-domain links instead of duplicates |
| `verification_notes` | ✔ | string | What the verifier checked |
| `verified_by` | ✔ | `independent-subagent` `sequential-self-review` | |
| `source` | opt. | `auditor` `verifier` `devils-advocate` `skeptical-reviewer` | |
| `lens` | opt. | `hypothesis` `red-team` `debt-archaeology` `evolution` `skeptical-review` | Set on findings a deep lens originated |

`meta.depth` is `standard` (the default) or `deep`. Deep audits must also include the two arrays below.

## Deep-mode arrays (top level, alongside `findings`)

**`hypotheses`**: Lens 1 register.

| Field | Req | Type / enum |
|---|---|---|
| `id` | ✔ | `^H-\d{2}$` (two digits, so it is never confused with domain-H finding IDs) |
| `statement` | ✔ | falsifiable claim |
| `prior` | ✔ | `High` `Medium` `Low` |
| `prior_rationale` | ✔ | string |
| `supporting_evidence_sought` | ✔ | string |
| `refuting_evidence_sought` | ✔ | string |
| `method` | ✔ | string (files, greps, git queries, tools) |
| `status` | ✔ | `SUPPORTED` `REFUTED` `INCONCLUSIVE` |
| `conclusion` | ✔ | string with evidence (file:line or commit) |
| `related_findings` | cond. | array of finding IDs; required when `SUPPORTED` |
| `origin` | opt. | `planned` `emergent` |

**`skeptical_review`**: Lens 5 challenges and their resolutions.

| Field | Req | Type / enum |
|---|---|---|
| `id` | ✔ | `^SR-\d{2,3}$` |
| `target` | ✔ | finding ID or report section |
| `issue` | ✔ | string |
| `evidence` | ✔ | string |
| `required_action` | ✔ | `revise` `downgrade` `upgrade` `add evidence` `remove claim` `no change` |
| `resolution` | ✔ | what the orchestrator changed, or why no change was needed |
| `resolved` | ✔ | boolean; every entry must be `true` before the PDF is built |

## Snippet rules

- Copy the lines **exactly** from the file (indentation may differ; whitespace is normalised when matching).
- Keep it short: the smallest excerpt that proves the point.
- Redact secrets in the snippet: `DB_PASSWORD=<REDACTED:password>`. The validator matches the non-redacted parts in order.
- Never paste customer data from fixtures or dumps; redact it as `<REDACTED:pii>`.

## Absence findings

For "no rate limiting on login" there is no line that proves the absence. Cite the place where the control *should* be (the route definition or login handler), quote that line, and in `mitigations` list what you searched for (e.g. "Searched for throttle/RateLimiter/limiter middleware across routes/ and app/Http/Kernel.php; none applied to POST /login").
