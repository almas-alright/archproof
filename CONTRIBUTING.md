# Contributing to ArchProof

Thanks for helping improve ArchProof. Contributions that make audits more accurate, more evidence-based or more broadly applicable are very welcome.

## Ground rules

- **Evidence over opinion.** New checklist items should describe what to look for in code or configuration, and which evidence confirms or refutes it.
- **Stack-neutral.** Language-specific guidance goes in tables or clearly labelled bullets, never as the only option.
- **No fabricated standards.** Cite public standards by name and version. If you are unsure of a version, say "verify current version".
- **Keep it readable.** Plain Markdown, Python standard library where possible, and no minified or compiled code (the directory security scan requires readable source).
- **Keep files small.** Every non-image file must stay under 256 KiB, and the plugin under 512 files.

## Workflow

1. Fork the repository and create a branch.
2. Make your change. If you change the findings schema or validator rules, update `references/findings-schema.md`, `examples/sample-findings.json` and `tests/run_selftest.sh` together.
3. Run `bash tests/run_selftest.sh` and `claude plugin validate . --profile directory`.
4. Add a line to `CHANGELOG.md` under an "Unreleased" heading.
5. Open a pull request that explains the motivation and shows before/after output where relevant.

## Reporting audit-quality problems

If ArchProof produced a false positive, missed an issue, or gave a disproportionate recommendation, open an issue with the stack, the (sanitised) code pattern, what ArchProof said, and what you expected. Please never include secrets or proprietary code.
