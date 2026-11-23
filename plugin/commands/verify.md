---
description: "Re-verify an existing ArchProof audit (findings.json and report.md) against the repository and rebuild the PDF"
argument-hint: "[path to the audit output folder]"
---

Re-verify an existing ArchProof audit. Locate the output folder: the path the user gives, or by default the newest folder under `architecture-audit-output/`.

1. Run the independent verification pass in `${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/references/independent-verification.md` on `findings.json` (use the `independent-verifier` agent when available). If `meta.depth` is `"deep"`, also re-run the skeptical review (Lens 5) on the report.
2. Run the mechanical evidence check in `${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/references/verification-procedure.md` and fix every error until the ledger passes. If the user has installed the project's automated validator and asks you to use it, run that instead.
3. Rebuild the PDF to a **new** file name by following `${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/references/pdf-report-guide.md`, then report what changed.

User context: $ARGUMENTS
