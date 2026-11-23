---
description: "Re-verify an existing ArchProof audit (findings.json and report.md) against the repository and rebuild the PDF"
argument-hint: "[path to the audit output folder]"
---

Re-verify an existing ArchProof audit. Locate the output folder: the path the user gives, or by default the newest folder under `architecture-audit-output/`.

1. Run the independent verification pass in `${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/references/independent-verification.md` on `findings.json` (use the `independent-verifier` agent when available). If `meta.depth` is `"deep"`, also re-run the skeptical review (Lens 5) on the report.
2. Run the validator and fix every error it reports:
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/scripts/validate_findings.py --repo <repo> --findings <out>/findings.json --report <out>/report.md --ledger <out>/verification-ledger.json`
3. Rebuild the PDF to a **new** file name with `${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/scripts/build_report.py`, then report what changed.

User context: $ARGUMENTS
