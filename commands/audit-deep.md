---
description: "Run a deep ArchProof audit: the full audit plus five investigative lenses (hypothesis-driven investigation, red team, technical debt archaeology, evolutionary architecture, skeptical reviewer)"
argument-hint: "[context: purpose, growth plans, constraints]"
---

Run a **deep** ArchProof audit of the current repository using the `architecture-audit` skill (`${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/SKILL.md`) together with **all five lenses** in `${CLAUDE_PLUGIN_ROOT}/skills/architecture-audit/references/deep-audit-lenses.md`. Set `meta.depth` to `"deep"`.

Workflow (the lens phases are in bold):
1. Phase 0: intake. Gather the business context in more depth than usual (growth plans, likely product changes, regulatory direction), because the evolution lens depends on it.
2. Phase 1: reconnaissance. **Phase 1b: form the hypothesis register (Lens 1).**
3. Phase 2: architecture discovery.
4. Phase 3: specialised audits driven by the hypotheses, plus **the red team (Lens 2, `red-team-auditor`)** and **technical debt archaeology (Lens 3, `debt-archaeologist`)** in parallel.
5. Phase 4: devil's advocate, plus **evolutionary architecture (Lens 4, `evolution-architect`)**.
6. Phase 5: independent verification (`independent-verifier`, fresh context). **Phase 5b: skeptical review of the whole draft (Lens 5, `skeptical-reviewer`, fresh context).** Resolve every challenge, then re-verify.
7. Phases 6–7: risk assessment, then the report with Appendices B1–B5 and the PDF.

Present the audit plan first, including the expected extra effort, and wait for approval. When the agent tool is unavailable, run the lenses sequentially and say so in the report. Never claim independent agents ran when they did not.

User context: $ARGUMENTS
