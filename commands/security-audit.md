---
description: "Run an ArchProof security and data-privacy audit (domains F and O, plus security aspects of A and M); add 'deep' for red-team and skeptical-review lenses"
argument-hint: "[scope] [deep]"
---

Run a **security-focused** ArchProof audit using the `architecture-audit` skill (`${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/SKILL.md`).

**Scope:** domains F (application security) and O (data privacy), plus the dependency-security and secrets/container aspects of A and M.

**Phases:** Phase 0, a light Phase 1, the security domains, devil's advocate on HIGH and CRITICAL findings, full independent verification, then the report and PDF. Mark the other report sections "Out of scope". Static analysis only, unless the user authorises more.

If the arguments contain the word `deep`, also apply the relevant deep lenses from `${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/references/deep-audit-lenses.md`: Red Team and Skeptical Reviewer always, plus Hypothesis-Driven Investigation for the in-scope domains. Set `meta.depth` to `"deep"` and add the matching Appendix B sections.

User context: $ARGUMENTS
