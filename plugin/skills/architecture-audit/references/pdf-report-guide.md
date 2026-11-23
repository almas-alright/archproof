# PDF Report Guide

This guide turns `report.md`, `findings.json` and a **passing** `verification-ledger.json` into a professional, downloadable `report.pdf`. It uses the document and PDF capabilities already available in the environment; the plugin ships no rendering code.

**Preconditions (stop if any fails):**
- `verification-ledger.json` has `passed: true`.
- Its checksums still equal the current SHA-256 of `report.md` and `findings.json`. If they don't, the files changed after verification: re-run `verification-procedure.md`.
- The output file does not exist yet. Never overwrite a report; use `report-2.pdf` and so on.

If the user needs a draft before verification passes, label every page "DRAFT — NOT VERIFIED", omit the Verification Statement, and never deliver it as final.

## 1. Document structure (in this order)

1. **Cover page**:
   - kicker "Software Architecture & Engineering Audit"
   - the title from the report's `#` heading
   - a metadata table: application, repository, baseline (commit, first 12 characters, plus branch), audit date, scope, authorisation level, depth, prepared by ("Claude with the ArchProof plugin"), classification (default "Confidential")
   - the verification badge: "✓ Evidence verified — findings re-checked by <independent verifier agent | sequential self-review> and validated against the source (<locations_checked> code locations). See Verification Statement."
2. **Contents**: the list of `##` headings, without extra numbering (the headings already carry numbers).
3. **Body**: `report.md` from §1 onwards, with the two markers replaced (§3 below) and the diagrams rendered (§4).
4. **Verification Statement**: the final section (§5).

Page setup: A4 (Letter if the user is in North America or asks for it); margins 16 mm top, 18 mm bottom, 14 mm sides. The footer reads "<application> — Architecture Audit — <classification>" on the left and "Page N of M" on the right. Start each `##` section on a new page.

## 2. Visual design

| Element | Specification |
|---|---|
| Fonts | Sans-serif body (Inter, Segoe UI, Helvetica or Arial, whichever is available) at 10.5 pt, line height 1.5; monospace code (JetBrains Mono, Consolas or Menlo) at about 8.8 pt |
| Colours | Ink #1b1f24 · muted #5b6470 · rule lines #d9dee4 · accent #1f4e79 (headings, table headers) · light panel #f6f8fa · verification green #2f6f4f |
| Headings | Accent colour. `##` at 16 pt with a 2 pt accent underline; `###` at 12.5 pt |
| Tables | Full width, 9 pt, 1 px #d9dee4 borders, header row white on accent, zebra striping #fbfcfd, rows never split across pages |
| Code blocks | Light panel background, 3 px accent left border, wrapped lines, never split across pages |
| Severity badges | Rounded pill, white bold 7.8 pt text: CRITICAL #8b0000 · HIGH #c2410c · MEDIUM #b7791f · LOW #2f6f4f · INFO #4a5568 |
| Finding IDs | Never wrapped across lines; semi-bold |
| Cover | Vertically centred; title 26 pt with a 4 px accent rule beneath; the verification badge is a green-bordered panel on a pale green background |
| Verification Statement | Starts on a new page; green heading underline; the disclaimer at 8.5 pt in the muted colour |

Keep it restrained and consistent. No decorative imagery, no photos and no logos other than the user's own, if they provide one.

## 3. Generated tables (derive mechanically from `findings.json`)

Never write these by hand or from memory. Read `findings.json` and transform it with exact rules.

**Findings register** (replaces `<!-- FINDINGS_REGISTER -->`):
- Rows: every finding with `verification_status ≠ FALSE_POSITIVE`.
- Order: severity (CRITICAL, HIGH, MEDIUM, LOW, INFO), then `id`.
- Columns: ID | Domain | Finding (the title) | Type | Severity (as a badge) | Status (underscores replaced by spaces) | Confidence | Roadmap.
- If any false positives exist, add this line after the table: "*N candidate finding(s) rejected as false positives during verification — see Appendix A.*"

**Risk matrix** (replaces `<!-- RISK_MATRIX -->`):
- A 4×4 grid. Rows show likelihood from 4 (Almost certain) at the top down to 1 (Rare); columns show impact from 1 (Minor) to 4 (Severe).
- Each cell shows the score (likelihood × impact) in small text, plus the IDs of the findings with that likelihood and impact, excluding `STRENGTH` and `FALSE_POSITIVE`, sorted.
- Cell shading by score: 12–16 #f4c7c3 · 8–9 #f9d9b8 · 4–6 #fcefc2 · 2–3 #d9efe2 · 1 #eef1f4.
- Caption: "Score = likelihood × impact. Bands: 12–16 Critical, 8–9 High, 4–6 Medium, 2–3 Low, 1 Info. Generated from findings.json; strengths and false positives excluded."

After building both tables, count the findings again from `findings.json` and confirm that the register's row count and every matrix cell match. A mismatch means the table is wrong: rebuild it.

## 4. Diagrams

Render each ```` ```mermaid ```` block as an image when a renderer is available, such as the Mermaid CLI (`mmdc`), or a diagram or rendering tool or connector in the environment. Do not load scripts from the internet into the report without the user's consent. If no renderer is available, print the diagram source as a captioned code block ("Diagram source (Mermaid)"). Never silently drop a diagram.

## 5. Verification Statement (final section; fill from the ledger)

Use this text, substituting values from `verification-ledger.json` and `meta`:

> **Verification Statement**
>
> This report's findings were produced through a phased, evidence-driven audit and then verified in two layers: (1) a semantic verification pass that re-inspected each cited source location, traced execution paths, searched for mitigations and re-assessed severity; and (2) a mechanical evidence check confirming that every cited file and line range exists at the audited baseline and contains the quoted evidence. Only findings marked CONFIRMED are presented as confirmed defects or vulnerabilities.

Then a two-column table:

| Item | Value |
|---|---|
| Audited baseline | type, commit (full), branch, working-tree state |
| Audit depth | "Standard", or "Deep: five lenses (...)". For deep audits also show hypotheses by status, and skeptical-review challenges resolved/total |
| Semantic verification | "Independent verifier agent (fresh context; received only findings and repository access)" **or** "Sequential self-review by the auditing agent (no separate agent available)" |
| Mechanical verification | "ArchProof verification procedure v<tool_version>, performed by Claude (mode: procedural)" **or** "ArchProof automated validator (mode: tool)", with the time and PASSED |
| Findings | total, plus counts by status |
| Severity distribution | counts by severity |
| Evidence locations checked | `counts.locations_checked` |
| SHA-256 report.md / findings.json | the two checksums |

Then the list of checks performed (`checks` from the ledger), any warnings (or "No warnings"), and this paragraph:

> **How to re-verify:** check out the baseline commit, repeat the ArchProof verification procedure (or run the project's automated validator) against the same `findings.json` and `report.md`, and compare the SHA-256 values. Matching checksums and a passing result confirm that the evidence cited in this report is present in the audited source.

End with the disclaimer, in small muted text:

> Scope of this statement: it attests that cited evidence exists and that findings passed the documented verification procedure. It is not a certification, a penetration test, a compliance attestation, or a guarantee that no other defects exist. Runtime behaviour was verified only where stated in individual findings. Prepared with Claude (Anthropic) using the ArchProof plugin; it is not an Anthropic endorsement.

## 6. Rendering, in order of preference

1. **The environment's own PDF or document capability.** On claude.ai and in Cowork, use the built-in PDF or document creation skill or tool if one is available. Give it the assembled content and the design in §2.
2. **A local renderer that is already installed.** Build one self-contained HTML file (inline styles, images embedded) and convert it with a tool that is already present: headless Chrome, Chromium or Edge (`--headless --print-to-pdf`), WeasyPrint, wkhtmltopdf, or pandoc with a PDF engine. Check with `which` or `where` first. Ask before installing anything on the user's machine; installing into a disposable sandbox is acceptable.
3. **Fallback.** Deliver the self-contained `report.html` and tell the user: "Open in a browser → Print → Save as PDF, with background graphics enabled."

## 7. Quality check before delivery

- [ ] Open or inspect the PDF. If possible, render the cover, the register, the matrix and the Verification Statement pages as images and look at them.
- [ ] The page count is plausible, nothing is cut off, no table runs off the page, and no diagram is missing.
- [ ] The register and matrix match `findings.json` (the count check from §3).
- [ ] The checksums and commit printed in the statement are identical to the ledger.
- [ ] No secrets appear. Search the final text for the Step 5 patterns in `verification-procedure.md`.
- [ ] The file name is new; nothing was overwritten.

Deliver `report.pdf`, together with `report.md`, `findings.json` and `verification-ledger.json`, so the reader can re-verify.
