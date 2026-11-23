# Changelog

All notable changes to ArchProof are documented here. The project follows [Semantic Versioning](https://semver.org/). Raise `version` in `.claude-plugin/plugin.json` with every release.

## [1.0.0] - 2026-11-23

### Added
- `architecture-audit` skill: a phased methodology (intake, reconnaissance, discovery, specialised audits, devil's advocate, independent verification, risk assessment, reporting) across 16 audit domains.
- An API platform and gateway profile (contract governance, error model, versioning, idempotency, limits, gateway responsibilities, GraphQL/gRPC/BFF specifics).
- Nine specialist agents, including a fresh-context `independent-verifier`.
- Commands: `audit`, `security-audit`, `api-audit`, `verify`.
- `validate_findings.py`: a mechanical evidence check (files, line ranges, verbatim snippets, severity rules, report/data consistency, secret scan) that writes a verification ledger.
- `build_report.py`: a PDF builder with a cover, contents, generated findings register and risk matrix, Mermaid rendering, and a Verification Statement with checksums.
- A self-test with a deliberately flawed fixture repository, plus CI.
