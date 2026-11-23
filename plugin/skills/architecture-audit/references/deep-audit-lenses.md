# Deep Audit Lenses

A deep audit (`/archproof:audit-deep`, or `meta.depth: "deep"`) runs the standard methodology **plus** five investigative lenses. The lenses do not add new domains. They change *how* the domains are investigated and challenged, and they add five appendices to the report.

| Lens | Question it answers | When in the workflow | Agent (Claude Code / Cowork) |
|---|---|---|---|
| 1. Hypothesis-Driven Investigation | "What do we believe is wrong, and what evidence would prove or refute it?" | Phase 1b, after reconnaissance; drives Phase 3 | Orchestrator (no separate agent) |
| 2. Red Team / Adversarial Thinking | "How would a motivated adversary or abuser actually hurt this business?" | Phase 3, alongside the security domains | `red-team-auditor` |
| 3. Technical Debt Archaeology | "How did the code get this way, and where is debt accumulating fastest?" | Phase 3, in parallel | `debt-archaeologist` |
| 4. Future-Proofing / Evolutionary Architecture | "Which likely changes will be cheap, and which will be expensive or blocked?" | Phase 4, with devil's advocate | `evolution-architect` |
| 5. Skeptical Reviewer | "Would a hostile due-diligence reviewer accept this report?" | Phase 5b, after independent verification and before risk assessment | `skeptical-reviewer` |

**The lenses do not lower the evidence bar.** Every finding a lens produces goes through the same schema, verification and validator as any other finding. Set the optional `lens` field on findings a lens originated. A lens that finds nothing material says so in its appendix; never pad.

Run time and cost are roughly 1.5–2.5× a standard audit. Tell the user this in the audit plan.

---

## Lens 1: Hypothesis-Driven Investigation

Checklists find what you look for. Hypotheses make you look for what *matters for this system* and make it explicit when you were wrong.

### Procedure

1. **Form hypotheses (Phase 1b)** from reconnaissance signals and the Phase 0 context: stack, growth target, domain, git history, size of the riskiest components. Aim for 8–20 hypotheses in a full deep audit. Each one must be falsifiable. Good: "H-03: tenant isolation depends on developers remembering a `where tenant_id` clause; at least one query path omits it." Bad: "Security might be weak."
2. **For each hypothesis, write down before investigating:** the prior (`High`/`Medium`/`Low`, and why), the evidence that would *support* it, the evidence that would *refute* it, and the investigation method (files to read, greps, git queries, tools at the authorised level).
3. **Prioritise** by prior × impact-if-true, and investigate in that order. Assign each hypothesis to the domain agent best placed to test it.
4. **Investigate, and actively seek the refuting evidence first.** This counters confirmation bias.
5. **Conclude** each as `SUPPORTED`, `REFUTED` or `INCONCLUSIVE`. A supported hypothesis produces or links to findings (`related_findings`). A refuted one is recorded with the evidence that refuted it; refuted hypotheses are valuable evidence of what is sound. An inconclusive one names what would settle it.
6. **Add emergent hypotheses** during the audit when evidence suggests something new, and mark them `origin: "emergent"`.

### Output

The `hypotheses` array in `findings.json` (schema in `findings-schema.md`), rendered in report **Appendix B1: Hypothesis Log**. The executive summary may cite the most consequential refuted hypotheses as strengths.

---

## Lens 2: Red Team / Adversarial Thinking

The security domain checks controls one by one. The red team thinks in *goals and chains*: how small weaknesses combine, and how legitimate features get abused. It is **thought-experiment only**: no exploitation, no live traffic, no credential use, no production access, whatever the authorisation level.

### Procedure

1. **Assets and adversary goals.** List the 5–10 most valuable assets (money movement, PII, tenant data, admin capability, availability of a core flow, reputation surfaces such as outbound email or notifications), and what an adversary would want with each.
2. **Personas.** Consider each, and skip the irrelevant ones with a reason:
   - Anonymous internet user
   - Registered or free-tier user
   - Paying customer or a malicious **tenant** (multi-tenant systems)
   - A marketplace counter-party (buyer vs seller, freelancer vs client)
   - A compromised or malicious insider or admin
   - A compromised dependency or CI pipeline (supply chain)
   - An abusive automation (scraper, credential stuffer, promo or referral farmer)
   - A compromised third-party integration (webhook sender, OAuth provider)
3. **Abuse cases, not just vulnerabilities.** For each persona and goal, examine:
   - **Business-logic abuse:** race conditions on balances or coupons, negative quantities, price or currency manipulation, state-machine skipping (pay → refund → deliver), replay of one-time actions, quota evasion with multiple accounts, abuse of invitations or referrals.
   - **Trust-boundary crossings:** client-trusted fields, headers trusted from behind the gateway, internal endpoints reachable externally, webhooks without signatures, tenant ID taken from the request.
   - **Feature abuse:** file upload as a hosting or malware channel, email or SMS sending as spam relay or cost attack, exports as data exfiltration, search as an enumeration oracle, password reset as account takeover.
   - **Resource and cost attacks:** expensive endpoints without limits, unbounded queues, paid third-party APIs triggered by anonymous users.
   - **Supply chain:** install scripts, unpinned actions, typosquat-prone dependencies, broad CI secrets on fork PRs.
4. **Build attack chains.** Combine findings that are individually LOW or MEDIUM into end-to-end paths. Example: "user enumeration via signup (LOW) + no login rate limit (MEDIUM) + no MFA for admins (MEDIUM) → admin account takeover (HIGH)". Draw a Mermaid flowchart for the top 1–3 chains. A chain is a finding in its own right (`type: RISK`, `lens: "red-team"`, `related_findings` listing the links) whose likelihood and impact are those of the *chain*. It is confirmed only if every link is CONFIRMED.
5. **Detection and response.** For each top chain, ask: would the current logging, alerting and audit trail detect it, and how quickly? Cross-reference domain N.

### Guardrails

- Never write working exploit code, payloads designed for evasion, or step-by-step attack instructions against third parties. Describe each scenario at the level a defender needs to prioritise and fix it.
- No attack chain may rest on an unverified link while being presented as confirmed.

### Output

Report **Appendix B2: Red-Team Scenarios**: an asset and persona table, the abuse-case table (persona | goal | scenario | enabling findings | detectability | severity), and the chain diagrams.

---

## Lens 3: Technical Debt Archaeology

Debt is not just "bad code". It has a history, a growth rate and owners. Archaeology mines the version history to explain *why* the code is the way it is and *where* debt will hurt next. It needs git history (L0 is enough: these are read-only git commands). If the clone is shallow, ask before deepening it, or report on the available window.

### Procedure (git commands are read-only)

1. **Timeline:** first commit, active period, commit cadence over time, major restructurings, framework upgrades (`git log --reverse --format='%ad %s' --date=short | head`; dependency manifest history via `git log -p -- package.json`, and the equivalents for other stacks).
2. **Hotspots (churn × complexity):** churn per file over the last 12 months (`git log --since=12.months --format= --name-only | sort | uniq -c | sort -rn | head -40`), combined with size or complexity. The top 10 hotspots usually hold most of the defect risk.
3. **Temporal (change) coupling:** files that change together in the same commits but live in different modules. This reveals hidden dependencies the import graph does not show. Compute co-change counts for the hotspots. Report pairs above about 30% co-change with at least 5 shared commits.
4. **Defect density signals:** commits whose messages match `fix|bug|hotfix|revert|regression` per file, and reverted commits. This is a proxy, so label it as such.
5. **Knowledge distribution (bus factor):** the number of distinct authors per hotspot and per module, and modules where one author wrote most of the recent changes. **Anonymise by default** ("Author A", "Author B"). Name people only if the user explicitly asks and it is appropriate. This is a property of the system, not a judgement of individuals.
6. **Debt markers with age:** `TODO/FIXME/HACK/XXX` with `git blame` dates; suppressed linter or type warnings; skipped tests and how long they have been skipped.
7. **Decision archaeology:** for the 3–5 most significant architectural weaknesses, find when and how they were introduced (`git log -S`, `git log -L`, PR or commit messages, ADRs). Classify each as *deliberate and prudent*, *deliberate and reckless*, *inadvertent and prudent*, or *inadvertent and reckless* (the technical debt quadrant), based on the evidence available. This turns blame into understanding and tells the organisation which process to fix.
8. **Interest rate:** debt in high-churn areas costs interest on every change; debt in stable, rarely touched code may not be worth paying down. Prioritise accordingly. This often *downgrades* code-quality findings in dormant code.

### Output

Report **Appendix B5: Technical Debt Archaeology**: a timeline, the hotspot table (file | churn | size/complexity | fix-commit ratio | authors), the temporal-coupling table, the bus-factor summary (anonymised), and a decision-archaeology narrative. These feed and refine the §16 Technical Debt Register. Findings use domain E or B with `lens: "debt-archaeology"` and `evidence_kind: "HISTORY"`. For HISTORY evidence, `locations` cite the current file, and `evidence_description` cites the commit hashes.

---

## Lens 4: Future-Proofing / Evolutionary Architecture

The aim is to judge the architecture by how well it absorbs *likely* change, and to make important qualities *continuously testable* (fitness functions), not to predict the future.

### Procedure

1. **Change scenarios.** Derive 6–12 concrete, plausible change scenarios from the Phase 0 business context, the domain and the industry. Examples: 10x users, a new country or currency, a mobile app, a public API for partners, a second product line, enterprise SSO, data-residency requirements, replacing the payment provider, splitting out a team. For each, mark likelihood (from the user's stated plans where possible; otherwise marked as inferred).
2. **Impact analysis** per scenario: which modules, tables, contracts and deployment units must change; whether the change is local or crosses many boundaries; and the blockers. A scenario that touches many modules, or requires a data migration of core tables, means the architecture resists that change. Use the temporal-coupling data from Lens 3 where available.
3. **Decision reversibility.** Classify the key architectural decisions as one-way doors (hard to reverse: the data model, tenancy model, ID strategy, primary datastore, synchronous coupling, public API contracts) or two-way doors. Flag one-way doors made implicitly. Recommend making them explicit (ADRs) before they calcify further.
4. **Fitness functions.** For the 3–6 qualities that matter most (dependency direction, layering, performance budgets, security baselines, API compatibility, coupling limits), propose automatable checks in the stack's own tooling: ArchUnit / NetArchTest / deptrac / dependency-cruiser / import-linter / go-arch-lint rules, `oasdiff`/`buf breaking` in CI, bundle-size budgets, k6 thresholds, Semgrep rules, SLO alerts. Give each a concrete rule sketch. These become `IMPROVEMENT` findings or roadmap items, not defects.
5. **Evolution path.** For the scenarios most likely to be blocked, outline the *smallest* incremental path (for example: a modular-monolith boundary, then an anti-corruption layer, then extraction only if needed). Explicitly reject premature decomposition when evidence does not justify it. Simplicity before complexity still applies.
6. **Optionality cost check.** Challenge existing "future-proofing" too: abstractions, plugin systems or microservices built for changes that never came are over-engineering debt (cross-reference domain D).

### Output

Report **Appendix B4: Evolutionary Architecture**: a change-scenario table (scenario | likelihood | impacted areas | cost: low/medium/high | blockers | related IDs), the one-way-door decision list, the proposed fitness functions table (quality | rule | tool | where in CI), and the incremental evolution path. Feeds §17.3 and the long-term roadmap.

---

## Lens 5: Skeptical Reviewer

The independent verifier checks findings *one by one* against the code. The skeptical reviewer checks the *report as a whole*, as a hostile due-diligence reviewer or a sceptical CTO would read it, before the risk assessment is finalised.

### Procedure (run by a fresh agent that sees `findings.json`, the draft `report.md` and the repository)

1. **Claim audit.** Every sentence in the executive summary, the verdict and §2–§12 that states a fact must trace to a finding, a table, or cited evidence. List any unsupported claims.
2. **Severity calibration.** Look for inflation (alarming language or a high severity on a theoretical issue) and deflation (a real, confirmed risk buried at LOW). Compare similar findings for consistency.
3. **Counter-evidence search.** For the top 5 findings by severity, try to argue the opposite. Is there a mitigation, a context or a business reason the auditors missed? Check that each was genuinely ruled out.
4. **Coverage honesty.** Do the coverage register and the limitations match what was actually examined? Flag any implication of completeness that is not earned.
5. **Recommendation scrutiny.** Is each major recommendation proportionate, costed (complexity), sequenced correctly, and free of fashion-driven advice (unjustified microservices, rewrites, patterns)? Would the recommended fix introduce new risk?
6. **Bias check.** Look for anchoring on the first issues found, an over-represented domain because of agent enthusiasm, recency bias from git history, and stack bias (judging one ecosystem by another's conventions).
7. **"So what?" test.** For each HIGH or CRITICAL finding, can a non-engineering executive understand the business consequence from the text?

### Output

A list of challenges, each with: target (finding ID or report section), issue, evidence, and required action (`revise`, `downgrade`, `upgrade`, `add evidence`, `remove claim`, `no change` with a justification). The orchestrator must resolve every challenge, and repeat the mechanical evidence check (`verification-procedure.md`) afterwards. Record the challenges and their resolutions in the `skeptical_review` array of `findings.json`, rendered as report **Appendix B3: Skeptical Review**. Unresolved challenges block the final report.

---

## Deep-mode report additions

After Appendix A, add:

- **Appendix B1: Hypothesis Log**
- **Appendix B2: Red-Team Scenarios**
- **Appendix B3: Skeptical Review**
- **Appendix B4: Evolutionary Architecture**
- **Appendix B5: Technical Debt Archaeology**

The executive summary should add one paragraph, "What the deep lenses changed", covering, for example, hypotheses refuted, chains discovered, severities recalibrated by the skeptical review, and the most expensive future changes.
