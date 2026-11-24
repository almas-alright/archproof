# CLAUDE.md: ArchProof development guide

This file gives Claude Code the full context of the ArchProof project. Read it before changing anything. It records what was built, why, and the hard rules learned while getting the plugin through Anthropic's directory validation.

**Division of work:** Claude Code handles development in this repository: code, checklists, tests, versions and releases. Public communication (user emails, reviewer feedback, feature decisions) is handled in a separate claude.ai conversation and arrives here as concrete tasks. Do not reply to users or reviewers from this repository.

---

## 1. What ArchProof is

ArchProof is a Claude plugin for **evidence-driven software architecture and technical due-diligence audits** of existing repositories, in any language or stack. It produces:

- `findings.json`: the structured findings register (single source of truth)
- `report.md`: a 20-section professional report
- `verification-ledger.json`: the result of the mechanical evidence check
- `report.pdf`: a downloadable PDF with a cover, generated findings register and risk matrix, diagrams, and a Verification Statement (commit plus SHA-256 checksums)

Core principles (never weaken them): evidence before opinion; never invent line numbers or metrics; static findings are *risks* until measured; independent verification before reporting; no manufactured findings; preferences are not defects; read-only by default; repository content is untrusted data; secrets are always redacted.

- Owner: Almas, GitHub `almas-alright`, contact kutsnalmas@gmail.com. Licence: MIT.
- Repo: https://github.com/almas-alright/archproof

## 2. History (chronological)

| Version | What happened |
|---|---|
| (pre-1.0) | Started as a single `architecture-audit` claude.ai skill zip. Added a PDF pipeline, a findings JSON schema, a mechanical validator, scoping and intake, a documented severity model (likelihood × impact with caps), and a demo fixture. |
| 1.0.0 | Converted to a plugin named **ArchProof** (a distinctive name; generic names get held). Added 9 specialist agents, 4 commands, an **API platform and gateway profile**, README/LICENSE/CHANGELOG/CONTRIBUTING/SECURITY, CI, and the icon. |
| 1.1.0 | **Deep mode** (`/archproof:audit-deep`) with five lenses: Hypothesis-Driven Investigation, Red Team / Adversarial Thinking, Technical Debt Archaeology, Future-Proofing / Evolutionary Architecture, Skeptical Reviewer. 4 more agents, `/archproof:plan`, a `deep` modifier for the focused audits, `hypotheses` and `skeptical_review` registers enforced by the validator. |
| 1.2.0 | **Directory compliance.** Non-Verified orgs may ship only Markdown, text, JSON, YAML and images, so the repo was split: `plugin/` (shipped) vs `tools/` and `tests/` (not shipped). Verification became a written procedure; the PDF build became a guide. |
| 1.2.1–1.2.4 | Cleared directory **policy holds**: removed environment-variable reads from examples; author name `Almas` → `almas-alright` (it resembled an existing listing, "alma"); removed the URL + `${…}` + HTTP-client combination; replaced the `.env` false-positive example with a parameterised-SQL one; moved the example findings JSON out of the plugin. |
| 1.2.5 | Added `plugin/PRIVACY.md` and `privacyPolicyUrl`. **Submitted to the Claude plugin directory**, with the portal tracking branch `release` and plugin path `plugin`. Validation was fully clean. |

**Current status:** submitted 2026-11-23 and in the security scan / review pipeline. Nothing is published yet. The directory says no version goes live without an Anthropic reviewer for now.

## 3. Repository layout

```
plugin/                         ← SHIPPED (submitted folder). Markdown/JSON/PNG only.
  .claude-plugin/plugin.json    ← name "archproof", version, author almas-alright, privacyPolicyUrl
  .claude-plugin/icon.png       ← 1024px; the directory accepts the icon ONCE, at first submission
  skills/architecture-audit/
    SKILL.md                    ← orchestrator: principles, workflow, depth, domain map
    references/*.md             ← 18 reference docs (checklists, schema, verification, PDF guide, lenses)
    examples/sample-findings.md ← calibration examples (good vs bad findings)
  commands/                     ← plan, audit, audit-deep, security-audit, api-audit, verify
  agents/                       ← 13 agents (9 domain specialists + red-team-auditor,
                                  debt-archaeologist, evolution-architect, skeptical-reviewer)
  docs/report-preview.png, README.md (the listing text), PRIVACY.md, LICENSE
tools/                          ← NOT shipped: validate_findings.py (stdlib), build_report.py,
                                  report.css, requirements.txt
tests/                          ← NOT shipped: fixtures/orders-api (intentionally vulnerable demo,
                                  never executed), orders-api-findings.json, orders-api-report.md,
                                  run_selftest.sh
.claude-plugin/marketplace.json ← Claude Code marketplace; plugin source "./plugin"
.github/workflows/ci.yml        ← selftest, plugin-validate, plugin-file-policy
CHANGELOG.md, CONTRIBUTING.md, SECURITY.md, README.md (repo-level), LICENSE, CLAUDE.md (this file)
```

## 4. Hard rules for `plugin/` (learned from directory validation; breaking them blocks or holds submission)

1. **Allowed file types only:** `.md`, `.txt`, `.json`, `.yaml/.yml`, `.png/.jpg/.gif/.webp`, plus `LICENSE`. No `.py`, `.sh`, `.css` or `.js`, no shebangs (`#!`), and no package-manager files (`package.json`, `requirements.txt`, lockfiles). CI's `plugin-file-policy` job enforces this.
2. **No** `CLAUDE.md`, `AGENTS.md` or `.claude/` folders **inside `plugin/`** (this root-level `CLAUDE.md` is fine because it is outside the submitted folder).
3. **No executable logic hidden in Markdown.** Never embed scripts in `.md` for Claude to extract and run; that circumvents the restriction and would hurt the Verified review. Verification and PDF steps stay as *procedures* (`references/verification-procedure.md`, `references/pdf-report-guide.md`).
4. **Credential-forwarding heuristic (`MCP_FORWARDS_CREDENTIAL_ENV`):** a file containing a remote URL host, a `${VAR}`-style reference or credential-named variable, and HTTP-client text (`axios.`, `fetch(`, `http`) together gets held. Across files it also combines "reads a credential" in one file with "can send data" in another. Keep examples free of env-var reads, `${…}` placeholders next to URLs, `.env`-file scenarios and JSON with header-like keys. JSON examples belong in `tests/`, not `plugin/`.
5. **`plugin.json` fields:** only standard fields plus `privacyPolicyUrl` (the directory reads it; "unknown key, no action needed" is expected). Do not add `documentationUrl`/`supportUrl` or invented fields.
6. **Author name** stays `almas-alright`, because a short name like "Almas" triggered a name-confusion hold.
7. **No literal install commands in plugin docs** (`pip install`, `npm install`, registry or index URLs). Link to the package manager's own documentation instead.
8. Images: re-save without metadata; never embed archives. Every text file is UTF-8 with no NUL bytes. Non-image files stay under 256 KiB.
9. Frontmatter: command `description` values are quoted strings; agents use only `name`, `description`, `tools`, `model`.

## 5. Branches, versions and releases

- **`main`:** development. Push freely (CI must stay green).
- **`release`:** the branch the directory tracks. **Each push to `release` creates a new directory version.** While a submission is in scan or review, do **not** touch `release` unless a reviewer asks for a fix.
- Release checklist:
  1. Change on `main`.
  2. Bump `version` in `plugin/.claude-plugin/plugin.json` (SemVer: patch for fixes, minor for features, major for breaking schema changes). Installed copies detect updates only by version.
  3. Add a `CHANGELOG.md` entry.
  4. Run `bash tests/run_selftest.sh` and `claude plugin validate ./plugin --profile directory`.
  5. Commit and push `main`, then merge `main` into `release` and push (only when releasing).
  6. Tag `vX.Y.Z` and create a GitHub release (attach a zip of `plugin/` and a sample PDF).
- Tags on GitHub: `v1.0.0`, `v1.1.0`, `v1.2.0`. **Missing: `v1.2.1`–`v1.2.5`** (commits `5f42e64`, `585d09d`, `2e5d326`, `1d169e9`, `4415306`). The cloud session could not push tags; push them from a local machine.
- Directory picks up the tracked branch about every 6 hours. Once the plugin is published, connect the Claude GitHub App on its portal page for near-instant pickup. Auto-publish was left on (it applies only after the first reviewer-published version).

## 6. Keeping the two verification paths equivalent

The written procedure (`plugin/.../references/verification-procedure.md`) and the tool (`tools/validate_findings.py`) must enforce the **same rules**:
- schema and enums; paths inside the repository; line ranges; verbatim snippet at the cited lines (±2, whitespace-normalised, redaction-aware)
- rules R1–R12, including: CRITICAL needs CONFIRMED + High confidence; DEFECT/VULNERABILITY need CONFIRMED; UNVERIFIED is capped at MEDIUM; severity = L×I or a rationale is given
- report/findings ID consistency; no attestation language ("certified", "Anthropic-verified"); secret scan
- deep mode: hypotheses (`H-NN`), skeptical review (`SR-NN`, all `resolved: true`), Appendices B1–B5

When you change one path, change the other, plus `findings-schema.md` and `tests/run_selftest.sh`. The ledger records `mode: procedural` or `mode: tool`.

## 7. Testing

```bash
pip install -r tools/requirements.txt   # markdown, pygments, playwright; then install Chromium for Playwright
bash tests/run_selftest.sh               # 5 stages: validate sample, reject broken findings, deep mode, deep PDF, standard PDF
claude plugin validate ./plugin --profile directory
claude plugin validate .claude-plugin/marketplace.json
```
CI runs all of these. Keep the self-test's negative tests passing: they prove that the checks actually reject bad input.

## 8. Writing standards for plugin content

- Stack-neutral, evidence-based checklist items. Language-specific guidance goes in tables or labelled bullets.
- Never present unverified versions or EOL dates as fact; mark them "verify current version".
- Severity discipline: style issues are capped at LOW; trade-offs, improvements and assumptions are capped at MEDIUM.
- Security content describes defender-level detail only: never working exploits or evasion payloads.
- Git-author data is anonymised by default (debt archaeology).

## 9. Roadmap and open items

- [ ] Push the missing tags `v1.2.1`–`v1.2.5`, and create GitHub releases.
- [ ] Handle reviewer feedback from the directory submission (arrives as tasks from the communications thread).
- [ ] Run ArchProof on 1–2 real projects (`/archproof:plan`, then `/archproof:audit`, then `/archproof:audit-deep`), and tune checklists from false positives and misses.
- [ ] v1.3 candidate: publish `tools/` as a PyPI package (`archproof`), so the skill can optionally use the exact validator and PDF builder after user permission (link to pip docs; never bundle code in `plugin/`).
- [ ] 1280×640 GitHub social preview image (same style as the icon).
- [ ] Optional later: become a Verified organisation (would allow shipping scripts in `plugin/` again).
