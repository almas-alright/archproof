# ArchProof Privacy Policy

_Last updated: 23 November 2026_

ArchProof is a Claude plugin made of written instructions, agent definitions and examples. It has no server, no account system and no analytics, so the ArchProof project receives none of your data.

## What ArchProof reads

When you run an audit, Claude reads the repository you point it at, inside your own Claude session. This can include source code, configuration, documentation and git history. Git history can contain personal data, such as commit author names and email addresses.

## What ArchProof stores

ArchProof writes audit results only to a local folder you control (`architecture-audit-output/` by default), or delivers them to you in your Claude session. These outputs are designed to minimise personal data:

- Commit authors are anonymised by default (shown as "Author A", "Author B"), unless you explicitly ask otherwise.
- Secrets and credentials found during an audit are redacted (`<REDACTED:type>`). The report is blocked if anything that looks like a credential would leak into it.
- Raw personal data from your codebase, such as customer records in fixtures or database dumps, is not copied into reports.

## What ArchProof sends

Nothing. ArchProof makes no network calls, has no connectors and contains no telemetry. Any web lookups (for example, checking a framework's end-of-life date) are made by Claude's own web search tool, under your Claude settings.

## Retention

The ArchProof project retains no data, because it never receives any. Your audit outputs stay where they were written until you delete them. How your Claude conversations are handled is governed by Anthropic's own terms and privacy policy.

## Contact

Questions or concerns: open an issue at https://github.com/almas-alright/archproof/issues. For security matters, use GitHub's private vulnerability reporting on the same repository.
