# Changelog

All notable changes to ArchProof are documented here. The project follows [Semantic Versioning](https://semver.org/). Raise `version` in `.claude-plugin/plugin.json` with every release.

## [1.1.0] - 2026-11-23

### Added
- **Deep audit mode** (`/archproof:audit-deep`) with five investigative lenses (`references/deep-audit-lenses.md`):
  - Hypothesis-Driven Investigation: a falsifiable hypothesis register formed in Phase 1b
  - Red Team / Adversarial Thinking: personas, business-logic abuse, attack chains (thought-experiment only)
  - Technical Debt Archaeology: git hotspots, temporal coupling, anonymised bus factor, decision archaeology
  - Future-Proofing / Evolutionary Architecture: change scenarios, one-way doors, fitness functions
  - Skeptical Reviewer: a fresh-context challenge of the whole report before it is finalised
- Four agents: `red-team-auditor`, `debt-archaeologist`, `evolution-architect`, `skeptical-reviewer`.
- `/archproof:plan`: scope and cost an audit (intake, reconnaissance, plan) without producing findings.
- A `deep` modifier for `/archproof:security-audit` and `/archproof:api-audit`.
- Schema: `meta.depth`, a `lens` field on findings, and the `hypotheses` and `skeptical_review` registers.
- Validator: deep-mode checks (hypothesis register, Appendices B1–B5, every skeptical-review challenge resolved), lens and source enums, and related-finding integrity.
- The PDF Verification Statement now reports the audit depth, hypothesis outcomes and skeptical-review resolution.
- Self-test: a deep-mode scenario, and a negative test confirming an unresolved challenge blocks the build.

## [1.0.0] - 2026-11-23

### Added
- `architecture-audit` skill: a phased methodology (intake, reconnaissance, discovery, specialised audits, devil's advocate, independent verification, risk assessment, reporting) across 16 audit domains.
- An API platform and gateway profile (contract governance, error model, versioning, idempotency, limits, gateway responsibilities, GraphQL/gRPC/BFF specifics).
- Nine specialist agents, including a fresh-context `independent-verifier`.
- Commands: `audit`, `security-audit`, `api-audit`, `verify`.
- `validate_findings.py`: a mechanical evidence check (files, line ranges, verbatim snippets, severity rules, report/data consistency, secret scan) that writes a verification ledger.
- `build_report.py`: a PDF builder with a cover, contents, generated findings register and risk matrix, Mermaid rendering, and a Verification Statement with checksums.
- A self-test with a deliberately flawed fixture repository, plus CI.
