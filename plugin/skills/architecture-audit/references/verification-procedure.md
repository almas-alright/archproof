# Mechanical Evidence Verification Procedure

This procedure is Layer 2 of `independent-verification.md`. It checks, without judgement calls, that every citation in the audit is real and that every rule holds. It produces `verification-ledger.json`, the input to the PDF's Verification Statement.

Run it with the tools already present in the environment: a file reader that shows line numbers, text search (`grep -n`, or the Grep tool), `git`, and a SHA-256 utility (`shasum -a 256` on macOS/Linux, `sha256sum` on Linux, `Get-FileHash -Algorithm SHA256` in PowerShell). Do not write or install a program to do it. Where possible, it is run by the fresh `independent-verifier` agent, not by the agent that wrote the findings.

The procedure is **all-or-nothing**: the ledger's `passed` is `true` only if every check below passes. Warnings are allowed; errors are not.

## Step 0: Freeze the inputs

1. `report.md` and `findings.json` must be final. Any edit after this step means starting again at Step 0.
2. Record the baseline:
   - `git -C <repo> rev-parse HEAD` → `baseline.commit`, `baseline.type = "git"`
   - `git -C <repo> rev-parse --abbrev-ref HEAD` → `baseline.branch`
   - `git -C <repo> status --porcelain` is empty → `baseline.working_tree_clean = true`
   - Not a git repository: set `baseline.type = "file-list"`, and list the cited files with their SHA-256 values in `baseline.files`.
   - If `meta.commit` is set to anything other than `"auto"`, it must match `HEAD` (a prefix match is fine). Otherwise this is an error.
3. Compute the SHA-256 of `findings.json` and `report.md` → `checksums`.

## Step 1: Schema checks (every finding)

Error unless each of the following holds:

- [ ] Every required field in `findings-schema.md` is present and non-empty. `evidence_snippet` may be `""` only when `locations[0].start_line` is null.
- [ ] `id` matches `^[A-P]-\d{3}$` and is unique. A prefix letter that differs from `domain` is a warning.
- [ ] Every enum value is valid: `domain`, `type`, `severity`, `verification_status`, `confidence`, `evidence_kind`, `remediation_complexity`, `roadmap`, `verified_by`, plus the optional `lens` and `source`.
- [ ] `likelihood` and `impact` are integers from 1 to 4.
- [ ] `meta` has `application`, `repository`, `audit_date`, `scope`, `authorization_level`, `verification_mode` and `standards`. `meta.depth` is `standard` or `deep`; if it is missing, record a warning and assume `standard`.

## Step 2: Evidence checks (every location of every finding)

For each `locations[n]`:

1. **The path is safe and exists.** It is repo-relative: no leading `/`, no drive letter, and it does not resolve outside the repository root through `..`. The file exists at the baseline. Otherwise this is an error.
2. **The line range exists.** `1 ≤ start_line ≤ end_line ≤` the number of lines in the file. A directory location must not have line numbers. A null `start_line` is allowed for whole-file and absence findings (a snippet given in that case is a warning: "not checked").
3. **The snippet matches** (only for `locations[0]` with line numbers). Open lines `start_line − 2` to `end_line + 2`. Collapse all runs of whitespace to a single space in both the snippet and that window, then confirm the snippet text appears in the window.
   - If the snippet contains `<REDACTED:…>` markers, split it on them. Each non-empty piece must appear in the window, in order.
   - If it does not match, search the whole file. If it appears elsewhere, the error is "wrong line numbers"; if it appears nowhere, the error is "snippet not in file; re-copy it verbatim".
   - A snippet longer than 15 lines is a warning.
4. **Record** one entry per location in `evidence_records`: `{"finding": "F-001", "file": "...", "lines": "8-12", "exists": true, "range_ok": true, "snippet_match": true, "method": "read lines 6-14, whitespace-normalised substring"}`.

Re-read the file for each check. Never rely on memory of what a file contains.

## Step 3: Rule checks (every finding)

These are errors unless marked as warnings:

| # | Rule |
|---|---|
| R1 | `CRITICAL` requires `verification_status = CONFIRMED` **and** `confidence = High` |
| R2 | `type` `DEFECT` or `VULNERABILITY` requires `CONFIRMED` |
| R3 | `UNVERIFIED` is at most `MEDIUM` |
| R4 | `STRENGTH` is `INFO` |
| R5 | `TRADE_OFF`, `IMPROVEMENT` and `ASSUMPTION` are at most `MEDIUM` |
| R6 | `severity` equals the baseline from likelihood × impact (12–16 CRITICAL, 8–9 HIGH, 4–6 MEDIUM, 2–3 LOW, 1 INFO), or `severity_rationale` explains the difference (not required for `STRENGTH`) |
| R7 | A `VULNERABILITY` has all eight `attack_path` fields non-empty (for a domain-F `RISK` of HIGH or above, missing fields are a warning) |
| R8 | `evidence_kind = RUNTIME` requires `runtime_evidence` |
| R9 | Domains G, H and K, and any `UNVERIFIED` finding, need `runtime_verification_needed` unless the evidence is RUNTIME (`STRENGTH` excepted) |
| R10 | A domain-G `DEFECT` without RUNTIME evidence is a warning ("consider RISK") |
| R11 | Every ID in `related_findings` exists (warning) |
| R12 | A `lens` value while `meta.depth` is not `deep` is a warning |

## Step 4: Report cross-check

1. List every match of `\b[A-P]-\d{3}\b` in `report.md` (for example `grep -noE '\b[A-P]-[0-9]{3}\b' report.md`).
2. Every finding that is not `FALSE_POSITIVE` and not `STRENGTH` must appear in the report. Otherwise this is an error.
3. Every ID in the report must exist in `findings.json`. Otherwise this is an error.
4. Sections `## 1.` to `## 20.` should all be present (warning), and the markers `<!-- FINDINGS_REGISTER -->` and `<!-- RISK_MATRIX -->` should be present (warning).
5. Attestation language is an error. Search case-insensitively for `certified`, `anthropic-verified`, `anthropic verified`, `guaranteed secure` and `fully compliant`.

## Step 5: Secret scan (`report.md` and every string in `findings.json`)

Search with these patterns (extended regex, case-insensitive where noted). Any match that is not inside a `<REDACTED:…>` marker is an error; replace the value with `<REDACTED:type>`.

| Secret type | Pattern |
|---|---|
| Private key | `-----BEGIN (RSA \|EC \|OPENSSH \|DSA \|PGP )?PRIVATE KEY-----` |
| AWS access key | `\b(AKIA\|ASIA)[0-9A-Z]{16}\b` |
| GitHub token | `\bgh[pousr]_[A-Za-z0-9]{36,}` |
| Slack token | `\bxox[abprs]-[A-Za-z0-9-]{10,}` |
| Stripe live key | `\b[sr]k_live_[A-Za-z0-9]{16,}` |
| Google API key | `\bAIza[0-9A-Za-z_-]{35}` |
| JWT | `\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}` |
| Credentialed URL (case-insensitive) | `[a-z][a-z0-9+.-]*://[^ :/@]+:[^ @]{3,}@` |
| Bearer token (case-insensitive) | `Bearer +[A-Za-z0-9._~+/-]{20,}` |
| Assigned secret (case-insensitive) | `(password\|passwd\|pwd\|secret\|api[_-]?key\|access[_-]?token\|auth[_-]?token\|client[_-]?secret) *[:=] *['"]?[^ '",;)<]{8,}` |

For the last pattern, ignore obvious non-values: template placeholders such as `${…}` or `{{…}}`, lookups of a named setting through the language's configuration or environment API (the value itself is not present), `null`, `None`, `true`, `false`, `changeme`, `example`, runs of `x` and runs of `*`. Record each match you dismiss, with the reason, as a warning.

## Step 6: Deep-mode checks (only when `meta.depth` is `deep`)

These are errors unless marked as warnings:

- [ ] `hypotheses` is non-empty. Each entry has an `id` matching `^H-\d{2}$` (unique), all the required fields from `findings-schema.md`, `prior` in High/Medium/Low, and `status` in SUPPORTED/REFUTED/INCONCLUSIVE. A `SUPPORTED` entry lists `related_findings`, all of which exist.
- [ ] `skeptical_review` is non-empty. Each entry has an `id` matching `^SR-\d{2,3}$` (unique), all the required fields, a valid `required_action`, and **`resolved: true`**. One unresolved challenge blocks the report.
- [ ] `report.md` contains the headings `## Appendix B1` to `## Appendix B5`.
- [ ] Every hypothesis ID is mentioned in `report.md` (warning).
- [ ] At least one `lens: "red-team"` finding exists, or Appendix B2 states that the lens found nothing material (warning).

## Step 7: Write `verification-ledger.json`

```json
{
  "tool": "ArchProof verification procedure",
  "tool_version": "1.2.0",
  "mode": "procedural",
  "generated_at": "<ISO-8601 UTC>",
  "passed": true,
  "verifier": "independent-subagent | sequential-self-review",
  "baseline": {"type": "git", "commit": "<sha>", "branch": "<branch>", "working_tree_clean": true},
  "verification_mode": "<meta.verification_mode>",
  "depth": "standard | deep",
  "checksums": {"findings.json": "<sha256>", "report.md": "<sha256>"},
  "counts": {
    "total": 0, "by_status": {}, "by_severity": {}, "by_type": {},
    "locations_checked": 0, "snippets_matched": 0,
    "hypotheses": {}, "skeptical_challenges": 0, "skeptical_challenges_resolved": 0, "lens_findings": {}
  },
  "evidence_records": [],
  "checks": ["schema and enums", "paths inside repository", "line ranges", "verbatim snippets (±2 lines, whitespace-normalised, redaction-aware)", "severity rules R1–R12", "report/findings ID consistency", "no attestation language", "secret scan", "deep-mode registers and appendices"],
  "errors": [],
  "warnings": []
}
```

- `passed` is `true` only when `errors` is empty.
- The counts are computed by counting, never estimated.
- Every error names the finding or file and gives the exact reason, so it can be fixed.

## Step 8: Fix and repeat

If anything failed, fix it at its cause in `findings.json` or `report.md`, then repeat from **Step 0**, because the checksums change. Never edit the ledger to make it pass, and never weaken a rule.

## Honesty in the Verification Statement

The PDF states `mode: procedural`: the evidence check was performed by Claude following this documented procedure, not by an automated program. With the optional project tooling (`mode: tool`), say so instead. Both are reproducible: a reader can repeat the steps at the same commit and compare the checksums.
