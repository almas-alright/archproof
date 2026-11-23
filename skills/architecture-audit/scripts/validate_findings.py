#!/usr/bin/env python3
"""Mechanical verification for architecture-audit findings.

Checks findings.json against the audited repository and report.md, then writes
verification-ledger.json. Exit 0 = passed (warnings allowed), 1 = errors.

Read-only with respect to the repository. Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

DOMAINS = set("ABCDEFGHIJKLMNOP")
TYPES = {"DEFECT", "VULNERABILITY", "RISK", "WEAKNESS", "TRADE_OFF", "IMPROVEMENT", "ASSUMPTION", "STRENGTH"}
SEVERITIES = ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
STATUSES = {"CONFIRMED", "PARTIALLY_CONFIRMED", "FALSE_POSITIVE", "UNVERIFIED"}
CONFIDENCE = {"High", "Medium", "Low"}
EVIDENCE_KINDS = {"STATIC", "RUNTIME", "CONFIG", "HISTORY"}
COMPLEXITY = {"S", "M", "L", "XL"}
ROADMAP = {"Immediate", "Short-term", "Medium-term", "Long-term", "None"}
VERIFIERS = {"independent-subagent", "sequential-self-review"}
DEPTHS = {"standard", "deep"}
LENSES = {"hypothesis", "red-team", "debt-archaeology", "evolution", "skeptical-review"}
SOURCES = {"auditor", "verifier", "devils-advocate", "skeptical-reviewer"}
HYP_STATUSES = {"SUPPORTED", "REFUTED", "INCONCLUSIVE"}
SR_ACTIONS = {"revise", "downgrade", "upgrade", "add evidence", "remove claim", "no change"}
HYP_RE = re.compile(r"^H-\d{2}$")
SR_RE = re.compile(r"^SR-\d{2,3}$")
DEEP_APPENDICES = ["Appendix B1", "Appendix B2", "Appendix B3", "Appendix B4", "Appendix B5"]
ATTACK_KEYS = ["entry_point", "attacker_input", "validation", "authorization", "sink", "mitigations", "preconditions", "impact"]
REQUIRED = [
    "id", "title", "domain", "type", "severity", "verification_status", "likelihood", "impact",
    "confidence", "component", "locations", "evidence_snippet", "evidence_description", "evidence_kind",
    "root_cause", "scenario", "business_impact", "technical_impact", "mitigations", "remediation",
    "remediation_complexity", "roadmap", "verification_notes", "verified_by",
]
ID_RE = re.compile(r"^[A-P]-\d{3}$")
REPORT_ID_RE = re.compile(r"\b([A-P]-\d{3})\b")
REDACT_RE = re.compile(r"<REDACTED:[^>]*>")
LINE_TOLERANCE = 2

SECRET_PATTERNS = [
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("Stripe live key", re.compile(r"\b[sr]k_live_[A-Za-z0-9]{16,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("credentialed connection string", re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s:/@<>]+:[^\s@<>]{3,}@[^\s]+", re.I)),
    ("bearer token", re.compile(r"\bBearer\s+[A-Za-z0-9\-._~+/]{20,}=*", re.I)),
    ("assigned secret", re.compile(
        r"(?i)\b(?:password|passwd|pwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret)\b"
        r"\s*[:=]\s*['\"]?(?!<REDACTED)(?!\$\{)(?!\{\{)(?!env\()(?!process\.env)(?!os\.environ)(?!getenv)"
        r"(?!null\b)(?!None\b)(?!true\b)(?!false\b)(?!changeme\b)(?!example\b)(?!xxx+)(?!\*{3,})"
        r"([^\s'\",;)<]{8,})")),
]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def git(repo: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=30)
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def tree_hash(repo: Path) -> str:
    skip = {".git", "node_modules", "vendor", ".venv", "venv", "__pycache__", "architecture-audit-output", "dist", "build", "target"}
    h = hashlib.sha256()
    for root, dirs, files in os.walk(repo):
        dirs[:] = sorted(d for d in dirs if d not in skip)
        for fn in sorted(files):
            p = Path(root) / fn
            try:
                rel = p.relative_to(repo).as_posix()
                h.update(f"{rel}\0{p.stat().st_size}\n".encode())
            except OSError:
                continue
    return h.hexdigest()


def safe_resolve(repo: Path, rel: str) -> Path | None:
    if not rel or rel.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", rel):
        return None
    p = (repo / rel).resolve()
    try:
        p.relative_to(repo.resolve())
    except ValueError:
        return None
    return p


def snippet_matches(snippet: str, window: str) -> bool:
    parts = [norm(x) for x in REDACT_RE.split(snippet)]
    parts = [x for x in parts if x]
    if not parts:
        return False
    hay = norm(window)
    pos = 0
    for part in parts:
        i = hay.find(part, pos)
        if i < 0:
            return False
        pos = i + len(part)
    return True


def expected_severity(l: int, i: int) -> str:
    s = l * i
    if s >= 12:
        return "CRITICAL"
    if s >= 8:
        return "HIGH"
    if s >= 4:
        return "MEDIUM"
    if s >= 2:
        return "LOW"
    return "INFO"


def scan_secrets(text: str, label: str, errors: list):
    for name, rx in SECRET_PATTERNS:
        for m in rx.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            errors.append(f"{label}:{line}: possible unredacted secret ({name}). Redact as <REDACTED:type>.")


def validate(repo: Path, findings_path: Path, report_path: Path | None):
    errors: list[str] = []
    warnings: list[str] = []
    data = json.loads(findings_path.read_text(encoding="utf-8"))
    meta = data.get("meta", {})
    findings = data.get("findings")
    if not isinstance(findings, list):
        errors.append("findings.json: top-level 'findings' must be an array")
        findings = []
    for k in ["application", "repository", "audit_date", "scope", "authorization_level", "verification_mode", "standards"]:
        if not meta.get(k):
            errors.append(f"meta.{k} is missing")
    if meta.get("verification_mode") and meta["verification_mode"] not in VERIFIERS:
        errors.append(f"meta.verification_mode must be one of {sorted(VERIFIERS)}")
    depth = meta.get("depth", "standard")
    if "depth" not in meta:
        warnings.append("meta.depth missing; assuming 'standard'")
    if depth not in DEPTHS:
        errors.append(f"meta.depth must be one of {sorted(DEPTHS)}")

    seen = set()
    file_cache: dict[Path, list[str]] = {}
    for idx, f in enumerate(findings):
        fid = f.get("id", f"#{idx}")
        tag = f"[{fid}]"
        for k in REQUIRED:
            if k not in f or f[k] is None or (isinstance(f[k], str) and k != "evidence_snippet" and not f[k].strip()):
                errors.append(f"{tag} missing required field '{k}'")
        if not ID_RE.match(str(f.get("id", ""))):
            errors.append(f"{tag} id must match <DomainLetter>-NNN")
        if fid in seen:
            errors.append(f"{tag} duplicate id")
        seen.add(fid)
        if f.get("domain") not in DOMAINS:
            errors.append(f"{tag} invalid domain")
        elif ID_RE.match(str(fid)) and fid[0] != f["domain"]:
            warnings.append(f"{tag} id prefix does not match domain {f['domain']}")
        for key, allowed in [("type", TYPES), ("verification_status", STATUSES), ("confidence", CONFIDENCE),
                             ("evidence_kind", EVIDENCE_KINDS), ("remediation_complexity", COMPLEXITY),
                             ("roadmap", ROADMAP), ("verified_by", VERIFIERS)]:
            if key in f and f[key] not in allowed:
                errors.append(f"{tag} {key}='{f[key]}' not in {sorted(allowed)}")
        if f.get("lens") is not None and f.get("lens") not in LENSES:
            errors.append(f"{tag} lens='{f.get('lens')}' not in {sorted(LENSES)}")
        if f.get("source") is not None and f.get("source") not in SOURCES:
            errors.append(f"{tag} source='{f.get('source')}' not in {sorted(SOURCES)}")
        if f.get("lens") and depth != "deep":
            warnings.append(f"{tag} has lens '{f['lens']}' but meta.depth is not 'deep'")
        sev = f.get("severity")
        if sev not in SEVERITIES:
            errors.append(f"{tag} invalid severity")
            continue
        l, i = f.get("likelihood"), f.get("impact")
        if not (isinstance(l, int) and isinstance(i, int) and 1 <= l <= 4 and 1 <= i <= 4):
            errors.append(f"{tag} likelihood and impact must be integers 1-4")
            l, i = 1, 1
        status, typ, conf = f.get("verification_status"), f.get("type"), f.get("confidence")

        # Severity / status rules
        if sev == "CRITICAL" and not (status == "CONFIRMED" and conf == "High"):
            errors.append(f"{tag} CRITICAL requires verification_status CONFIRMED and confidence High")
        if typ in {"DEFECT", "VULNERABILITY"} and status != "CONFIRMED":
            errors.append(f"{tag} type {typ} requires CONFIRMED status (use RISK otherwise)")
        if status == "UNVERIFIED" and SEVERITIES.index(sev) > SEVERITIES.index("MEDIUM"):
            errors.append(f"{tag} UNVERIFIED findings are capped at MEDIUM (note potential severity in severity_rationale)")
        if typ == "STRENGTH" and sev != "INFO":
            errors.append(f"{tag} STRENGTH must be INFO")
        if typ in {"TRADE_OFF", "IMPROVEMENT", "ASSUMPTION"} and SEVERITIES.index(sev) > SEVERITIES.index("MEDIUM"):
            errors.append(f"{tag} {typ} is capped at MEDIUM")
        exp = expected_severity(l, i)
        if typ != "STRENGTH" and exp != sev and not str(f.get("severity_rationale", "")).strip():
            errors.append(f"{tag} severity {sev} differs from likelihood x impact baseline {exp}; add severity_rationale")
        if typ == "VULNERABILITY" or (f.get("domain") == "F" and typ == "RISK" and SEVERITIES.index(sev) >= 3):
            ap = f.get("attack_path") or {}
            missing = [k for k in ATTACK_KEYS if not str(ap.get(k, "")).strip()]
            if missing:
                (errors if typ == "VULNERABILITY" else warnings).append(f"{tag} attack_path missing: {', '.join(missing)}")
        if f.get("evidence_kind") == "RUNTIME" and not str(f.get("runtime_evidence", "")).strip():
            errors.append(f"{tag} evidence_kind RUNTIME requires runtime_evidence")
        if (f.get("domain") in {"G", "H", "K"} or status == "UNVERIFIED") and f.get("evidence_kind") != "RUNTIME" \
                and typ != "STRENGTH" and not str(f.get("runtime_verification_needed", "")).strip():
            errors.append(f"{tag} runtime_verification_needed required (domain G/H/K or UNVERIFIED without runtime evidence)")
        if f.get("domain") == "G" and typ == "DEFECT" and f.get("evidence_kind") != "RUNTIME":
            warnings.append(f"{tag} memory DEFECT without RUNTIME evidence — consider type RISK")
        if typ == "STRENGTH" and status == "FALSE_POSITIVE":
            warnings.append(f"{tag} STRENGTH marked FALSE_POSITIVE")

        # Location / evidence checks
        locs = f.get("locations") or []
        if not isinstance(locs, list) or not locs:
            errors.append(f"{tag} locations must be a non-empty array")
            locs = []
        for n, loc in enumerate(locs):
            rel = (loc or {}).get("file", "")
            p = safe_resolve(repo, rel)
            if p is None:
                errors.append(f"{tag} location[{n}] path '{rel}' is invalid or outside the repository")
                continue
            if not p.exists():
                errors.append(f"{tag} location[{n}] file not found: {rel}")
                continue
            if p.is_dir():
                if loc.get("start_line") is not None:
                    errors.append(f"{tag} location[{n}] '{rel}' is a directory but has line numbers")
                continue
            if p not in file_cache:
                try:
                    file_cache[p] = p.read_text(encoding="utf-8", errors="replace").splitlines()
                except OSError as e:
                    errors.append(f"{tag} cannot read {rel}: {e}")
                    continue
            lines = file_cache[p]
            s, e = loc.get("start_line"), loc.get("end_line")
            if s is None:
                if n == 0 and str(f.get("evidence_snippet", "")).strip():
                    warnings.append(f"{tag} snippet given but location has no line numbers; snippet not checked")
                continue
            if not isinstance(s, int) or (e is not None and not isinstance(e, int)):
                errors.append(f"{tag} location[{n}] line numbers must be integers")
                continue
            e = e if e is not None else s
            if s < 1 or e < s or e > len(lines):
                errors.append(f"{tag} location[{n}] lines {s}-{e} out of range for {rel} ({len(lines)} lines)")
                continue
            if n == 0:
                snip = f.get("evidence_snippet", "")
                if not str(snip).strip():
                    errors.append(f"{tag} evidence_snippet empty although line numbers are cited")
                else:
                    lo, hi = max(0, s - 1 - LINE_TOLERANCE), min(len(lines), e + LINE_TOLERANCE)
                    if not snippet_matches(snip, "\n".join(lines[lo:hi])):
                        whole = snippet_matches(snip, "\n".join(lines))
                        errors.append(f"{tag} evidence_snippet not found at {rel}:{s}-{e}"
                                      + (" (it exists elsewhere in the file — fix the line numbers)" if whole else
                                         " (not found anywhere in the file — re-copy it verbatim)"))
                    if len(str(snip).splitlines()) > 15:
                        warnings.append(f"{tag} evidence_snippet longer than 15 lines")

        # Secret scan of finding text
        def strings(o):
            if isinstance(o, str):
                yield o
            elif isinstance(o, dict):
                for v in o.values():
                    yield from strings(v)
            elif isinstance(o, list):
                for v in o:
                    yield from strings(v)
        scan_secrets("\n".join(strings(f)), f"findings.json{tag}", errors)

    # Deep-mode registers
    hyps = data.get("hypotheses") or []
    srs = data.get("skeptical_review") or []
    if depth == "deep":
        if not hyps:
            errors.append("deep audit requires a non-empty 'hypotheses' array (Lens 1)")
        if not srs:
            errors.append("deep audit requires a 'skeptical_review' array (Lens 5); record 'no change' entries if the review raised nothing")
        if not any(f.get("lens") == "red-team" for f in findings) and "red-team" not in json.dumps(meta).lower():
            warnings.append("deep audit has no red-team findings; state in Appendix B2 that the lens found nothing material")
    hyp_ids = set()
    for h in hyps:
        hid = h.get("id", "?")
        tag = f"[{hid}]"
        if not HYP_RE.match(str(hid)):
            errors.append(f"{tag} hypothesis id must match H-NN")
        if hid in hyp_ids:
            errors.append(f"{tag} duplicate hypothesis id")
        hyp_ids.add(hid)
        for k in ["statement", "prior", "prior_rationale", "supporting_evidence_sought", "refuting_evidence_sought", "method", "status", "conclusion"]:
            if not str(h.get(k, "")).strip():
                errors.append(f"{tag} hypothesis missing '{k}'")
        if h.get("prior") and h["prior"] not in CONFIDENCE:
            errors.append(f"{tag} prior must be High/Medium/Low")
        if h.get("status") and h["status"] not in HYP_STATUSES:
            errors.append(f"{tag} status must be one of {sorted(HYP_STATUSES)}")
        rel = h.get("related_findings") or []
        if h.get("status") == "SUPPORTED" and not rel:
            errors.append(f"{tag} SUPPORTED hypothesis must list related_findings")
        for r in rel:
            if r not in seen:
                errors.append(f"{tag} related finding {r} does not exist")
    sr_ids = set()
    for c in srs:
        cid = c.get("id", "?")
        tag = f"[{cid}]"
        if not SR_RE.match(str(cid)):
            errors.append(f"{tag} skeptical-review id must match SR-NN")
        if cid in sr_ids:
            errors.append(f"{tag} duplicate skeptical-review id")
        sr_ids.add(cid)
        for k in ["target", "issue", "evidence", "required_action", "resolution"]:
            if not str(c.get(k, "")).strip():
                errors.append(f"{tag} skeptical-review entry missing '{k}'")
        if c.get("required_action") and c["required_action"] not in SR_ACTIONS:
            errors.append(f"{tag} required_action must be one of {sorted(SR_ACTIONS)}")
        if c.get("resolved") is not True:
            errors.append(f"{tag} skeptical-review challenge is unresolved; resolve it before building the report")
    for f in findings:
        for r in f.get("related_findings") or []:
            if r not in seen:
                warnings.append(f"[{f.get('id')}] related finding {r} does not exist")

    # Report cross-check
    report_ids = set()
    if report_path:
        if not report_path.exists():
            errors.append(f"report not found: {report_path}")
        else:
            text = report_path.read_text(encoding="utf-8")
            report_ids = set(REPORT_ID_RE.findall(text))
            for f in findings:
                if f.get("verification_status") != "FALSE_POSITIVE" and f.get("id") not in report_ids and f.get("type") != "STRENGTH":
                    errors.append(f"[{f.get('id')}] not referenced in report.md")
            unknown = sorted(report_ids - seen)
            if unknown:
                errors.append(f"report.md references IDs not in findings.json: {', '.join(unknown)}")
            for marker in ["<!-- FINDINGS_REGISTER -->", "<!-- RISK_MATRIX -->"]:
                if marker not in text:
                    warnings.append(f"report.md lacks marker {marker} (table will be appended at the end)")
            for n in range(1, 21):
                if not re.search(rf"^##\s+{n}\.\s", text, re.M):
                    warnings.append(f"report.md: section '## {n}.' not found")
            if re.search(r"(?i)\b(certified|anthropic[- ]verified|guaranteed secure|fully compliant)\b", text):
                errors.append("report.md uses attestation language (certified / Anthropic-verified / guaranteed / fully compliant) — not permitted")
            scan_secrets(text, "report.md", errors)
            if depth == "deep":
                for ap in DEEP_APPENDICES:
                    if not re.search(rf"^##\s+{ap}\b", text, re.M):
                        errors.append(f"deep audit report.md lacks '## {ap} ...' section")
                for hid in hyp_ids:
                    if hid not in text:
                        warnings.append(f"hypothesis {hid} not mentioned in report.md (Appendix B1)")

    # Baseline
    commit = git(repo, "rev-parse", "HEAD")
    dirty = git(repo, "status", "--porcelain")
    baseline = {
        "type": "git" if commit else "file-tree-sha256",
        "commit": commit or tree_hash(repo),
        "branch": git(repo, "rev-parse", "--abbrev-ref", "HEAD") if commit else None,
        "working_tree_clean": (dirty == "") if commit else None,
    }
    if meta.get("commit") not in (None, "", "auto") and commit and not commit.startswith(str(meta["commit"])) \
            and not str(meta["commit"]).startswith(commit[:7]):
        errors.append(f"meta.commit {meta['commit']} does not match repository HEAD {commit}")

    def count(key):
        c: dict[str, int] = {}
        for f in findings:
            c[str(f.get(key))] = c.get(str(f.get(key)), 0) + 1
        return c

    ledger = {
        "tool": "ArchProof validate_findings.py",
        "tool_version": "1.1.0",
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "passed": not errors,
        "repository_path": str(repo.resolve()),
        "baseline": baseline,
        "verification_mode": meta.get("verification_mode"),
        "depth": depth,
        "checksums": {
            "findings.json": sha256_file(findings_path),
            **({"report.md": sha256_file(report_path)} if report_path and report_path.exists() else {}),
        },
        "counts": {
            "total": len(findings),
            "by_status": count("verification_status"),
            "by_severity": count("severity"),
            "by_type": count("type"),
            "hypotheses": {s_: sum(1 for h in hyps if h.get("status") == s_) for s_ in sorted(HYP_STATUSES)} if hyps else {},
            "skeptical_challenges": len(srs),
            "skeptical_challenges_resolved": sum(1 for c in srs if c.get("resolved") is True),
            "lens_findings": {l: sum(1 for f in findings if f.get("lens") == l) for l in sorted(LENSES) if any(f.get("lens") == l for f in findings)},
            "locations_checked": sum(len(f.get("locations") or []) for f in findings),
            "snippets_matched": sum(1 for f in findings if (f.get("locations") or [{}])[0].get("start_line") is not None) - sum(1 for x in errors if "evidence_snippet not found" in x),
        },
        "checks": [
            "schema and enum validation", "file existence within repository root", "line ranges within file length",
            "verbatim evidence snippet at cited lines (±2, whitespace-normalised, redaction-aware)",
            "severity = likelihood x impact or documented rationale", "CRITICAL requires CONFIRMED + High confidence",
            "DEFECT/VULNERABILITY require CONFIRMED", "UNVERIFIED capped at MEDIUM",
            "attack path completeness for vulnerabilities", "runtime evidence/verification fields",
            "report <-> findings ID consistency", "secret-pattern scan of report and findings",
            "no attestation language",
            "deep mode: hypothesis register, resolved skeptical-review challenges, Appendices B1-B5",
        ],
        "errors": errors,
        "warnings": warnings,
    }
    return ledger


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--findings", required=True, type=Path)
    ap.add_argument("--report", type=Path)
    ap.add_argument("--ledger", type=Path)
    a = ap.parse_args()
    try:
        ledger = validate(a.repo, a.findings, a.report)
    except json.JSONDecodeError as e:
        print(f"ERROR: findings.json is not valid JSON: {e}")
        sys.exit(1)
    out = a.ledger or a.findings.with_name("verification-ledger.json")
    out.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    for w in ledger["warnings"]:
        print("WARN ", w)
    for e in ledger["errors"]:
        print("ERROR", e)
    c = ledger["counts"]
    print(f"\n{'PASSED' if ledger['passed'] else 'FAILED'}: {c['total']} findings, "
          f"{len(ledger['errors'])} errors, {len(ledger['warnings'])} warnings. Ledger: {out}")
    sys.exit(0 if ledger["passed"] else 1)


if __name__ == "__main__":
    main()
