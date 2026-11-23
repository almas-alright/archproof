# Report Template

Write `report.md` with exactly these 20 numbered sections, in this order. `build_report.py` adds a cover page and the Verification Statement; you write everything else. Use the two generator markers exactly as shown, and the script replaces them with tables built from `findings.json`.

## Writing rules

- Audience: CTOs, architects, engineering directors, due-diligence reviewers. Use professional, specific, plain language. No filler such as "it is important to note" or "robust", and no generic observations that would fit any repository.
- Facts first, then recommendations. Label sections or sentences "Observation" and "Recommendation" where the two could be confused.
- Reference finding IDs (`F-003`) instead of re-explaining a finding in several sections. Each root cause is described in full once, in §14.
- Include positive observations (`STRENGTH` findings) where they are earned.
- Do not recommend a rewrite unless the evidence shows incremental change is infeasible, and say why.
- A section with nothing material says so in one sentence. Out-of-scope sections read: "Out of scope for this audit (see §1)."
- Mermaid diagrams go in fenced ```` ```mermaid ```` blocks. Quote labels that contain symbols, avoid semicolons in sequence-diagram messages, keep each diagram to 25 nodes or fewer, and add a legend where *observed* and *inferred* elements are mixed.
- Never include secrets, raw PII, or real customer data.
- Never invent metrics. Every number comes from a tool you ran (name it), from configuration, or from the user.

---

```markdown
# <Application Name> — Software Architecture & Engineering Audit

## 1. Cover and Audit Metadata
| Item | Value |
|---|---|
| Application | |
| Repository | <url/path> @ <commit> (<branch>), working tree <clean/dirty> |
| Audit date | |
| Scope | Full / domains … ; included and excluded paths |
| Audit purpose | |
| Languages & technologies | |
| Authorisation level | L0–L3 and what was executed |
| Methodology | Phased (recon → discovery → specialised audits → devil's advocate → independent verification → risk assessment); <independent subagents / sequential single-agent> |
| Standards applied | name + version for each (e.g. OWASP ASVS 5.0, chapters V1–V8 assessed) |
| Limitations (summary) | 2–4 bullets; full list in §19 |

## 2. Executive Summary
- **Overall engineering assessment**: 3–5 sentences, a reasoned judgement.
- **Key strengths**: 3–5 bullets with IDs.
- **Major risks**: 3–5 bullets with IDs, ordered by risk.
- **Critical findings**: list, or "None confirmed".
- **High-priority recommendations**: 3–5, each linked to IDs and a roadmap bucket.
- **Overall technical readiness**: one paragraph covering readiness for the purpose stated in Phase 0 (scale, due diligence, production launch).

## 3. Application Overview
Business purpose (state whether identified or inferred), application structure, technology stack table (from domain A), major components, external dependencies, deployment architecture.

## 4. Architecture Assessment
Current architecture (observed vs intended), architecture diagram, component boundaries, dependency direction, data flow (sequence diagram for a critical flow), design quality, strengths, weaknesses (with IDs).

## 5. Database Assessment
Schema design (ER diagram of the core aggregates), relationships, indexing, constraints, transaction management, query efficiency, data integrity, migration strategy.

## 6. Design Pattern Assessment
Existing patterns table (pattern | where | verdict: correct / misapplied / unnecessary / inconsistent), missing abstractions only where justified, overengineering, SOLID assessment with concrete examples.

## 7. Security Assessment
Attack-surface summary table, authentication, authorisation, data protection & privacy (domain O), vulnerability findings (IDs), dependency security, security limitations (what static review cannot establish, and recommended penetration-test scope).

### 7a. API Platform Assessment (only when the API platform/gateway profile is active)
Endpoint inventory summary, sampled conformance table, gateway responsibility matrix, timeout-budget diagram. See `api-platform-review.md` §11. An optional "Proposed API Standard" appendix may follow Appendix A, but only on request.

## 8. Performance and Memory Assessment
Performance risks, memory risks, resource management, database bottlenecks, scalability limits (10x/100x analysis where meaningful), and a **runtime verification plan** table (hypothesis | tool | procedure | metric | threshold | environment).

## 9. Reliability and Distributed Systems
Dependency failure table (dependency | failure mode | behaviour | blast radius | mitigation), fault tolerance, failure propagation, concurrency, integration reliability, recovery capability.

## 10. Code Quality and Maintainability
Code organisation, complexity (tool + command + top hotspots), duplication, technical debt overview, maintainability risks.

## 11. DevOps and Operational Readiness
Deployment, CI/CD, infrastructure, configuration and secrets, observability (domain N), backup and recovery.

## 12. Testing Assessment
Existing strategy, coverage (measured or "not measured"), critical-flow coverage table, gaps, QA recommendations.

## 13. Findings Register
<!-- FINDINGS_REGISTER -->

## 14. Detailed Technical Findings
One subsection per finding that is not a false positive, ordered by severity then ID:

### F-003 — <Title>
| Domain | Type | Severity | Status | Likelihood × Impact | Confidence | Complexity | Roadmap |
|---|---|---|---|---|---|---|---|
**Component / location**: `path/file.ext:120-134`
**Evidence**: description, followed by the redacted snippet in a code block
**Root cause** · **Scenario** · **Business impact** · **Technical impact** · **Existing mitigations** · **Attack path** (security) · **Recommended remediation** · **Runtime verification needed** · **Verification notes** · **References**

## 15. Risk Matrix
<!-- RISK_MATRIX -->
Short commentary on clusters, for example "most HIGH risks concentrate in the billing integration".

## 16. Technical Debt Register
| Debt item | Root cause | Business impact | Engineering impact | Remediation strategy | Priority | Related IDs |

## 17. Architecture Improvement Recommendations
### 17.1 Immediate corrective changes
### 17.2 Incremental architectural improvements
### 17.3 Long-term evolution opportunities
Each item gives the rationale, trade-offs, prerequisites and related IDs.

## 18. Prioritised Remediation Roadmap
| Bucket | Item | IDs | Depends on | Complexity | Expected outcome |
Buckets: Immediate (0–7 days), Short-term (1–4 weeks), Medium-term (1–3 months), Long-term (3–6 months).

## 19. Audit Limitations
- Coverage register (area | status | notes)
- Unavailable source areas
- Runtime evidence not available
- Unverified assumptions (list ASSUMPTION/UNVERIFIED IDs)
- Test coverage not measured, if applicable
- External systems not inspected
- Areas that need specialist penetration testing or performance testing

## 20. Final Architecture Verdict
A reasoned paragraph for each: architectural maturity, maintainability, security posture, performance readiness, operational readiness, scalability readiness, and overall technical risks. Use the ISO/IEC 25010 characteristics as a lens. Do not give a numeric maturity score.

## Appendix A — False Positives Rejected During Verification
| ID | Original claim | Reason rejected |
```

### Deep-mode appendices (only when `meta.depth` is `deep`)

Add these after Appendix A, using exactly these headings so the validator can find them. Their content is specified in `deep-audit-lenses.md`:

- `## Appendix B1 — Hypothesis Log`: a table of ID, statement, prior, method, status and conclusion, with related findings
- `## Appendix B2 — Red-Team Scenarios`
- `## Appendix B3 — Skeptical Review`
- `## Appendix B4 — Evolutionary Architecture`
- `## Appendix B5 — Technical Debt Archaeology`

Also add a "What the deep lenses changed" paragraph to the executive summary (§2).

The Verification Statement is appended automatically. Do not write one yourself.
