---
description: "Run an ArchProof API platform, API engine or gateway audit (contract governance, error model, versioning, idempotency, limits, gateway responsibilities); add 'deep' for the adversarial lenses"
argument-hint: "[spec path, gateway or focus] [deep]"
---

Run an **API platform audit** using the `architecture-audit` skill (`${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/SKILL.md`), with the API platform and gateway profile (`${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/references/api-platform-review.md`) active.

**Scope:** Domain I, the API-relevant parts of F (OWASP API Security Top 10) and K (timeouts, retries and failure modes at the gateway). Audit against the organisation's API style guide if one exists; otherwise use the ArchProof baseline. Sample endpoints as the profile specifies.

**Phases:** run the full independent verification, then produce the report (with §7a) and the PDF.

If the arguments contain the word `deep`, also apply the relevant deep lenses from `${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/references/deep-audit-lenses.md`: Red Team and Skeptical Reviewer always, plus Hypothesis-Driven Investigation for the in-scope domains. Set `meta.depth` to `"deep"` and add the matching Appendix B sections. For API audits in deep mode, also apply Lens 4 (evolutionary architecture), focused on contract evolution and versioning.

User context: $ARGUMENTS
