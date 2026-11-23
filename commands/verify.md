---
description: Re-verify an existing ArchProof findings.json and report against the repository and rebuild the PDF
argument-hint: "[path to the audit output folder]"
---

Re-verify an existing ArchProof audit. Locate the output folder (default: the newest folder under `architecture-audit-output/`, or the path the user gives).

1. Run the independent verification pass in `${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/references/independent-verification.md` on `findings.json` (use the `independent-verifier` agent when available).
2. Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/scripts/validate_findings.py --repo <repo> --findings <out>/findings.json --report <out>/report.md --ledger <out>/verification-ledger.json` and fix every error.
3. Rebuild the PDF to a **new** file name with `${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/scripts/build_report.py`, and report what changed.

User context: $ARGUMENTS
