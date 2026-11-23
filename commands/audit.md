---
description: "Run a standard ArchProof architecture audit of the current repository (all relevant domains, devil's advocate, independent verification, PDF report)"
argument-hint: "[context, focus or constraints]"
---

Run a **standard full** ArchProof audit of the current repository using the `architecture-audit` skill (`${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/SKILL.md`). Follow every phase in order:

1. Intake and scoping
2. Reconnaissance
3. Architecture discovery
4. Specialised audits across all relevant domains (including the API platform and gateway profile if it applies)
5. Devil's advocate
6. Independent verification
7. Risk assessment
8. Report and PDF

Present the audit plan and wait for approval before the large investigation. Use the plugin's specialist agents and the `independent-verifier` agent when the agent tool is available. Set `meta.depth` to `"standard"`.

For red-teaming, hypothesis testing, debt archaeology, evolutionary-architecture analysis and a skeptical review of the report, suggest `/archproof:audit-deep` instead.

User context: $ARGUMENTS
