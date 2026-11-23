---
description: Run a full ArchProof architecture audit of the current repository (all relevant domains, independent verification, PDF report)
argument-hint: "[focus, context or constraints]"
---

Run a **full** ArchProof audit of the current repository using the `architecture-audit` skill (`${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/SKILL.md`). Follow every phase in order: intake and scoping, reconnaissance, architecture discovery, specialised audits across all relevant domains (including the API platform and gateway profile if it applies), devil's advocate, independent verification, risk assessment, then the report and the PDF.

Present the audit plan and wait for approval before the large investigation. Use the plugin's specialist agents and the `independent-verifier` agent when the agent tool is available.

User context: $ARGUMENTS
