---
description: "Scope an ArchProof audit without running it: intake questions, repository reconnaissance, system inventory and a costed audit plan (no findings)"
argument-hint: "[context: purpose, growth, constraints]"
---

Prepare an ArchProof audit **plan only**, using the `architecture-audit` skill (`${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/SKILL.md`). Do not produce findings.

1. Run Phase 0 intake (`${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/references/scoping-and-intake.md`): ask only what the repository cannot tell you.
2. Run Phase 1 reconnaissance and write `architecture-audit-output/<date>/inventory.md` (system inventory and coverage register).
3. Present the plan:
   - the detected stack
   - the recommended mode (`/archproof:audit`, `/archproof:audit-deep`, `/archproof:security-audit` or `/archproof:api-audit`) and why
   - the domains, and whether the API platform profile applies
   - partitioning for large repositories
   - the agents to be used, and the tools needed at each authorisation level
   - the expected effort (relative; deep is roughly 1.5 to 2.5 times standard)
   - the known limitations

Use this before a large or deep audit so the user can approve the scope cheaply.

User context: $ARGUMENTS
