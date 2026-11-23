# Security Policy

## Reporting a vulnerability in ArchProof

If you find a security issue in ArchProof itself, please report it privately using GitHub's **Report a vulnerability** (Security Advisories) on this repository, rather than in a public issue. Examples include the scripts writing outside the output folder, secrets leaking into reports despite redaction, or prompt-injection paths that make the audit modify a repository.

Please include steps to reproduce, the affected version, and the impact. You can expect an acknowledgement within 7 days.

## Scope notes

- `tests/fixtures/orders-api/` contains **intentional** vulnerabilities for testing. These are not security issues in ArchProof.
- ArchProof reports describe vulnerabilities in *audited* codebases. Do not publish reports about systems you do not own or have permission to assess.
