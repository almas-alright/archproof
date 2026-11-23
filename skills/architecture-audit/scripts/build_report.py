#!/usr/bin/env python3
"""Build the architecture audit PDF from report.md + findings.json + verification-ledger.json.

- Refuses to build if the ledger failed or if report/findings changed after validation.
- Inserts the generated findings register and risk matrix at their markers.
- Renders ```mermaid blocks with mmdc (Mermaid CLI) when available.
- Adds a cover page, a table of contents and the Verification Statement.
- PDF engines tried in order: Playwright Chromium, system Chrome/Chromium headless, WeasyPrint.
  If none is available, writes report.html and explains how to print it.

Dependencies: python 'markdown' (pip install markdown), optional 'pygments'.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSS_PATH = HERE.parent / "assets" / "report.css"
SEV_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
L_LABELS = {1: "Rare", 2: "Unlikely", 3: "Likely", 4: "Almost certain"}
I_LABELS = {1: "Minor", 2: "Moderate", 3: "Major", 4: "Severe"}


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def die(msg: str):
    print(f"ERROR: {msg}")
    sys.exit(1)


def md_escape(s: str) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def findings_register(findings: list[dict]) -> str:
    rows = [f for f in findings if f.get("verification_status") != "FALSE_POSITIVE"]
    rows.sort(key=lambda f: (SEV_ORDER.index(f.get("severity", "INFO")), f.get("id", "")))
    out = ["| ID | Domain | Finding | Type | Severity | Status | Confidence | Roadmap |",
           "|---|---|---|---|---|---|---|---|"]
    for f in rows:
        sev = f.get("severity", "")
        out.append(f"| <span class=\"fid\">{f['id']}</span> | {f.get('domain','')} | {md_escape(f.get('title',''))} | {f.get('type','')} | "
                   f"{sev} | {f.get('verification_status','').replace('_',' ')} | "
                   f"{f.get('confidence','')} | {f.get('roadmap','')} |")
    fp = [f for f in findings if f.get("verification_status") == "FALSE_POSITIVE"]
    if fp:
        out.append("")
        out.append(f"*{len(fp)} candidate finding(s) rejected as false positives during verification — see Appendix A.*")
    return "\n".join(out)


def risk_matrix(findings: list[dict]) -> str:
    cells: dict[tuple[int, int], list[str]] = {}
    for f in findings:
        if f.get("type") == "STRENGTH" or f.get("verification_status") == "FALSE_POSITIVE":
            continue
        cells.setdefault((f.get("likelihood", 1), f.get("impact", 1)), []).append(f["id"])
    h = ['<table class="risk-matrix"><thead><tr><th>Likelihood ↓ / Impact →</th>']
    for i in range(1, 5):
        h.append(f"<th>{i} · {I_LABELS[i]}</th>")
    h.append("</tr></thead><tbody>")
    for l in range(4, 0, -1):
        h.append(f"<tr><th>{l} · {L_LABELS[l]}</th>")
        for i in range(1, 5):
            s = l * i
            band = "critical" if s >= 12 else "high" if s >= 8 else "medium" if s >= 4 else "low" if s >= 2 else "info"
            ids = ", ".join(sorted(cells.get((l, i), [])))
            h.append(f'<td class="rm rm-{band}"><span class="score">{s}</span><br>{html.escape(ids)}</td>')
        h.append("</tr>")
    h.append("</tbody></table>")
    h.append('<p class="caption">Score = likelihood × impact. Bands: 12–16 Critical, 8–9 High, 4–6 Medium, 2–3 Low, 1 Info. '
             'Cell contents are generated from findings.json; strengths and false positives excluded.</p>')
    return "\n".join(h)


def render_mermaid(md: str, workdir: Path) -> tuple[str, dict[str, str]]:
    """Replace mermaid blocks with placeholders; return (md, {placeholder: html})."""
    mmdc = shutil.which("mmdc")
    repl: dict[str, str] = {}
    pat = re.compile(r"```mermaid[^\n]*\n(.*?)```", re.S)
    n = 0

    def sub(m):
        nonlocal n
        n += 1
        key = f"MERMAIDPLACEHOLDER{n}X"
        src = m.group(1)
        rendered = None
        if mmdc:
            inp, outp = workdir / f"d{n}.mmd", workdir / f"d{n}.svg"
            inp.write_text(src, encoding="utf-8")
            cfg = workdir / "puppeteer.json"
            if not cfg.exists():
                cfg.write_text(json.dumps({"args": ["--no-sandbox", "--disable-setuid-sandbox"]}))
            try:
                r = subprocess.run([mmdc, "-i", str(inp), "-o", str(outp), "-b", "white", "-p", str(cfg), "-q"],
                                   capture_output=True, text=True, timeout=120)
                if r.returncode == 0 and outp.exists():
                    b64 = base64.b64encode(outp.read_bytes()).decode()
                    rendered = f'<figure class="diagram"><img src="data:image/svg+xml;base64,{b64}" alt="diagram {n}"/></figure>'
                else:
                    print(f"WARN mermaid diagram {n} failed to render: {r.stderr.strip()[:300]}")
            except Exception as e:  # noqa: BLE001
                print(f"WARN mermaid diagram {n}: {e}")
        if rendered is None:
            rendered = ('<figure class="diagram diagram-src"><figcaption>Diagram source (Mermaid; renderer unavailable)'
                        f'</figcaption><pre>{html.escape(src)}</pre></figure>')
        repl[key] = rendered
        return f"\n\n{key}\n\n"

    return pat.sub(sub, md), repl


def md_to_html(md: str) -> str:
    try:
        import markdown  # type: ignore
    except ImportError:
        if shutil.which("pandoc"):
            r = subprocess.run(["pandoc", "-f", "gfm", "-t", "html5"], input=md, capture_output=True, text=True)
            if r.returncode == 0:
                return r.stdout
        die("python 'markdown' package not installed (pip install markdown) and pandoc unavailable")
    exts = ["tables", "fenced_code", "sane_lists", "attr_list", "toc", "md_in_html"]
    cfg = {"toc": {"permalink": False}}
    try:
        import pygments  # noqa: F401
        exts.append("codehilite")
        cfg["codehilite"] = {"guess_lang": False, "noclasses": True, "pygments_style": "friendly"}
    except ImportError:
        pass
    return markdown.markdown(md, extensions=exts, extension_configs=cfg, output_format="html5")


def build_toc(body_html: str) -> str:
    items = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body_html)
    lis = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in items)
    return f'<nav class="toc"><h2 class="toc-title">Contents</h2><ol class="toc-list">{lis}</ol></nav>'


def cover_html(meta: dict, ledger: dict, title: str) -> str:
    b = ledger.get("baseline", {})
    commit = b.get("commit") or "n/a"
    rows = [
        ("Application", meta.get("application", "")),
        ("Repository", meta.get("repository", "")),
        ("Baseline", f"{'commit' if b.get('type') == 'git' else 'file-tree SHA-256'} {commit[:12]}"
                     + (f" ({b.get('branch')})" if b.get("branch") else "")),
        ("Audit date", meta.get("audit_date", "")),
        ("Scope", meta.get("scope", "")),
        ("Authorisation level", meta.get("authorization_level", "")),
        ("Prepared by", meta.get("auditor", "Claude with the ArchProof plugin")),
        ("Classification", meta.get("classification", "Confidential")),
    ]
    trs = "".join(f"<tr><th>{html.escape(k)}</th><td>{html.escape(str(v))}</td></tr>" for k, v in rows)
    mode = "independent verifier agent" if ledger.get("verification_mode") == "independent-subagent" else "sequential self-review"
    return f"""
<section class="cover">
  <div class="cover-kicker">Software Architecture &amp; Engineering Audit</div>
  <h1 class="cover-title">{html.escape(title)}</h1>
  <table class="cover-meta">{trs}</table>
  <div class="verify-badge">
    <div class="vb-mark">✓</div>
    <div><strong>Evidence verified</strong><br>
    Findings re-checked by {mode} and mechanically validated against the source
    ({ledger['counts']['locations_checked']} code locations). See Verification Statement.</div>
  </div>
</section>"""


def verification_html(meta: dict, ledger: dict, report_sha: str, findings_sha: str) -> str:
    b = ledger["baseline"]
    c = ledger["counts"]
    st = c.get("by_status", {})
    sev = c.get("by_severity", {})
    mode = ("Independent verifier agent (fresh context; received only findings and repository access)"
            if ledger.get("verification_mode") == "independent-subagent"
            else "Sequential self-review by the auditing agent (no separate agent available)")
    checks = "".join(f"<li>{html.escape(x)}</li>" for x in ledger.get("checks", []))
    warns = ledger.get("warnings", [])
    warn_html = (f"<p><strong>Validator warnings ({len(warns)}):</strong></p><ul class='small'>"
                 + "".join(f"<li>{html.escape(w)}</li>" for w in warns[:25]) + "</ul>") if warns else "<p>No validator warnings.</p>"

    def kv(d):
        return ", ".join(f"{k.replace('_', ' ')}: {v}" for k, v in sorted(d.items())) or "—"

    return f"""
<section class="verification">
<h2 id="verification-statement">Verification Statement</h2>
<p>This report's findings were produced through a phased, evidence-driven audit and then verified in two layers:
(1) a semantic verification pass that re-inspected each cited source location, traced execution paths, searched for
mitigations and re-assessed severity; and (2) an automated evidence check confirming that every cited file and line range
exists at the audited baseline and contains the quoted evidence. Only findings marked <em>CONFIRMED</em> are presented as
confirmed defects or vulnerabilities.</p>
<table class="kv">
<tr><th>Audited baseline</th><td>{html.escape(b.get('type',''))}: <code>{html.escape(str(b.get('commit','')))}</code>
{('branch ' + html.escape(b['branch'])) if b.get('branch') else ''}
{'' if b.get('working_tree_clean') is None else ('— working tree clean' if b['working_tree_clean'] else '— working tree had uncommitted changes')}</td></tr>
<tr><th>Semantic verification</th><td>{html.escape(mode)}</td></tr>
<tr><th>Mechanical verification</th><td>{html.escape(ledger.get('tool',''))} v{html.escape(ledger.get('tool_version',''))},
run {html.escape(ledger.get('generated_at',''))} — <strong>{'PASSED' if ledger.get('passed') else 'FAILED'}</strong></td></tr>
<tr><th>Findings</th><td>{c.get('total',0)} total · status — {html.escape(kv(st))}</td></tr>
<tr><th>Severity distribution</th><td>{html.escape(kv(sev))}</td></tr>
<tr><th>Evidence locations checked</th><td>{c.get('locations_checked',0)}</td></tr>
<tr><th>SHA-256 report.md</th><td><code>{report_sha}</code></td></tr>
<tr><th>SHA-256 findings.json</th><td><code>{findings_sha}</code></td></tr>
</table>
<p><strong>Checks performed:</strong></p><ul class="small">{checks}</ul>
{warn_html}
<p><strong>How to re-verify:</strong> check out the baseline above, then run<br>
<code>python3 skills/architecture-audit/scripts/validate_findings.py --repo &lt;repo&gt; --findings findings.json --report report.md</code><br>
and compare the SHA-256 values. Matching checksums and a PASSED result confirm that the evidence cited in this report
is present in the audited source.</p>
<p class="disclaimer">Scope of this statement: it attests that cited evidence exists and that findings passed the documented
verification procedure. It is not a certification, a penetration test, a compliance attestation, or a guarantee that no
other defects exist. Runtime behaviour was verified only where stated in individual findings. Prepared with Claude
(Anthropic) using the ArchProof plugin; it is not an Anthropic endorsement.</p>
</section>"""


def find_chrome() -> str | None:
    for name in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge"]:
        p = shutil.which(name)
        if p:
            return p
    for p in ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "C:/Program Files/Google/Chrome/Application/chrome.exe",
              "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"]:
        if Path(p).exists():
            return p
    return None


def to_pdf(html_path: Path, pdf_path: Path, footer_text: str) -> str | None:
    footer = (f'<div style="font-size:8px;width:100%;padding:0 14mm;color:#666;display:flex;justify-content:space-between;">'
              f'<span>{html.escape(footer_text)}</span><span>Page <span class="pageNumber"></span> of '
              f'<span class="totalPages"></span></span></div>')
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page()
            page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
            page.pdf(path=str(pdf_path), format="A4", print_background=True, display_header_footer=True,
                     header_template="<div></div>", footer_template=footer,
                     margin={"top": "16mm", "bottom": "18mm", "left": "14mm", "right": "14mm"})
            browser.close()
        return "playwright-chromium"
    except Exception as e:  # noqa: BLE001
        print(f"INFO Playwright unavailable or failed ({type(e).__name__}); trying system Chrome")
    chrome = find_chrome()
    if chrome:
        r = subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                            f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri()],
                           capture_output=True, text=True, timeout=180)
        if r.returncode == 0 and pdf_path.exists():
            return "chrome-headless"
        print(f"INFO Chrome headless failed: {r.stderr.strip()[:200]}")
    try:
        from weasyprint import HTML  # type: ignore
        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        return "weasyprint"
    except Exception as e:  # noqa: BLE001
        print(f"INFO WeasyPrint unavailable ({type(e).__name__})")
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", required=True, type=Path)
    ap.add_argument("--findings", required=True, type=Path)
    ap.add_argument("--ledger", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path, help="output .pdf path")
    ap.add_argument("--force-draft", action="store_true",
                    help="build a watermarked DRAFT even if verification failed (never deliver as final)")
    a = ap.parse_args()

    for p in (a.report, a.findings, a.ledger):
        if not p.exists():
            die(f"missing {p}")
    if a.out.exists():
        die(f"{a.out} already exists — choose a new path (reports are never overwritten)")
    data = json.loads(a.findings.read_text(encoding="utf-8"))
    ledger = json.loads(a.ledger.read_text(encoding="utf-8"))
    meta, findings = data.get("meta", {}), data.get("findings", [])
    report_sha, findings_sha = sha256(a.report), sha256(a.findings)

    draft = False
    problems = []
    if not ledger.get("passed"):
        problems.append(f"verification ledger shows {len(ledger.get('errors', []))} error(s)")
    if ledger.get("checksums", {}).get("findings.json") != findings_sha:
        problems.append("findings.json changed after validation — rerun validate_findings.py")
    if ledger.get("checksums", {}).get("report.md") != report_sha:
        problems.append("report.md changed after validation (or was not validated) — rerun validate_findings.py with --report")
    if problems:
        if not a.force_draft:
            die("; ".join(problems))
        draft = True
        print("WARN building DRAFT: " + "; ".join(problems))

    md = a.report.read_text(encoding="utf-8")
    title_m = re.match(r"\s*#\s+(.+)", md)
    title = title_m.group(1).strip() if title_m else f"{meta.get('application', 'Application')} — Architecture Audit"
    if title_m:
        md = md[title_m.end():]
    reg, rm = findings_register(findings), risk_matrix(findings)
    md = md.replace("<!-- FINDINGS_REGISTER -->", reg) if "<!-- FINDINGS_REGISTER -->" in md else md + "\n\n## Findings Register\n\n" + reg
    rm_key = "RISKMATRIXPLACEHOLDERX"
    md = md.replace("<!-- RISK_MATRIX -->", f"\n\n{rm_key}\n\n") if "<!-- RISK_MATRIX -->" in md else md + f"\n\n## Risk Matrix\n\n{rm_key}\n\n"

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        md, diagrams = render_mermaid(md, tdp)
        body = md_to_html(md)
        for k, v in {**diagrams, rm_key: rm}.items():
            body = body.replace(f"<p>{k}</p>", v).replace(k, v)
        body = re.sub(r">(CRITICAL|HIGH|MEDIUM|LOW|INFO)<", lambda m: f'><span class="sev sev-{m.group(1).lower()}">{m.group(1)}</span><', body)
        css = CSS_PATH.read_text(encoding="utf-8") if CSS_PATH.exists() else ""
        doc = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>{css}</style></head><body class="{'draft' if draft else ''}">
{cover_html(meta, ledger, title)}
{build_toc(body)}
<main>{body}</main>
{verification_html(meta, ledger, report_sha, findings_sha) if not draft else '<section class="verification"><h2>Verification Statement</h2><p><strong>DRAFT — verification did not pass. Not for distribution.</strong></p></section>'}
</body></html>"""
        out_html = a.out.with_suffix(".html")
        out_html.write_text(doc, encoding="utf-8")
        footer = f"{meta.get('application', '')} — Architecture Audit — {meta.get('classification', 'Confidential')}" + (" — DRAFT" if draft else "")
        engine = to_pdf(out_html, a.out, footer)
    if engine:
        print(f"PDF written: {a.out} (engine: {engine}); HTML: {out_html}")
    else:
        print(f"No PDF engine available. HTML written: {out_html}. Open it in a browser and use Print → Save as PDF "
              "(enable 'Background graphics'), or install one of: pip install playwright && playwright install chromium; "
              "pip install weasyprint.")
        sys.exit(2)


if __name__ == "__main__":
    main()
