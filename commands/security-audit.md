---
description: Run an ArchProof security and data-privacy audit only (domains F and O, plus the security aspects of A and M)
argument-hint: "[scope, e.g. a module or path]"
---

Run a **security-focused** ArchProof audit using the `architecture-audit` skill (`${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/SKILL.md`). Scope: domains F (application security) and O (data privacy), plus the dependency-security and secrets/container aspects of A and M. Do Phase 0, a light Phase 1, the security domains, devil's advocate on HIGH/CRITICAL findings, the full independent verification, and the report with the PDF. Mark the other report sections "Out of scope". Static analysis only unless the user authorises more.

User context: $ARGUMENTS
