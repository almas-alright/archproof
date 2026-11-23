---
description: Run an ArchProof API platform, API engine or gateway audit (contract governance, error model, versioning, idempotency, limits, gateway responsibilities)
argument-hint: "[spec path, gateway, or focus]"
---

Run an **API platform audit** using the `architecture-audit` skill (`${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/SKILL.md`) with the API platform and gateway profile (`${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/references/api-platform-review.md`) active. Include Domain I, the API-relevant parts of F (OWASP API Security Top 10) and K (timeouts, retries, failure modes at the gateway). Audit against the organisation's API style guide if one exists, otherwise the ArchProof baseline. Sample endpoints as the profile specifies, run the full independent verification, and produce the report (with §7a) and the PDF.

User context: $ARGUMENTS
