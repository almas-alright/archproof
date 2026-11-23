#!/usr/bin/env bash
# ArchProof self-test: validates the sample findings against the demo fixture,
# checks that broken findings are rejected, and builds the demo PDF.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL="$ROOT/plugin/skills/architecture-audit"
SAMPLE="$ROOT/tests/fixtures/orders-api-findings.json"
TOOLS="$ROOT/tools"
FIX="$ROOT/tests/fixtures"
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT

echo "1/5 validating sample findings against the fixture repository"
python3 "$TOOLS/validate_findings.py" --repo "$FIX/orders-api" \
  --findings "$SAMPLE" --report "$FIX/orders-api-report.md" \
  --ledger "$OUT/ledger.json"

echo "2/5 checking that the validator rejects broken findings"
python3 - "$SAMPLE" "$OUT/broken.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
f = d["findings"]
f[1]["locations"][0]["start_line"] = f[1]["locations"][0]["end_line"] = 25   # wrong line numbers
f[2]["severity"] = "CRITICAL"                                                 # severity without rationale
f[4]["verification_status"] = "UNVERIFIED"; f[4]["severity"] = "HIGH"         # unverified above the cap
f[0]["evidence_description"] += ' password = "S3cretValue123"'                # leaked secret
json.dump(d, open(sys.argv[2], "w"))
PY
if python3 "$TOOLS/validate_findings.py" --repo "$FIX/orders-api" --findings "$OUT/broken.json" \
     --report "$FIX/orders-api-report.md" --ledger "$OUT/broken-ledger.json" > "$OUT/broken.log"; then
  echo "FAIL: validator accepted broken findings"; exit 1
fi
for expect in "evidence_snippet not found" "add severity_rationale" "capped at MEDIUM" "unredacted secret"; do
  grep -q "$expect" "$OUT/broken.log" || { echo "FAIL: missing expected error: $expect"; cat "$OUT/broken.log"; exit 1; }
done
echo "    broken findings correctly rejected"

echo "3/5 deep mode: hypotheses, red-team chain, skeptical review, Appendices B1-B5"
python3 - "$SAMPLE" "$FIX/orders-api-report.md" "$OUT" <<'PY'
import json, sys
src, report, out = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(src))
d["meta"]["depth"] = "deep"
d["findings"].append({
  "id": "F-005", "title": "Attack chain: enumerable IDs + missing ownership check enable bulk order scraping",
  "domain": "F", "type": "RISK", "severity": "HIGH", "verification_status": "CONFIRMED",
  "likelihood": 3, "impact": 3, "confidence": "High", "component": "Orders API",
  "locations": [{"file": "src/routes/orders.js", "start_line": 19, "end_line": 19},
                {"file": "migrations/001_init.sql", "start_line": 2, "end_line": 2}],
  "evidence_snippet": "const { rows } = await pool.query('SELECT * FROM orders WHERE id = $1', [req.params.id]);",
  "evidence_description": "BIGSERIAL ids (001_init.sql:2) are sequential; F-002 lets any user read any id; no rate limiting exists on the router.",
  "evidence_kind": "STATIC", "root_cause": "Absent object-level authorisation combined with predictable identifiers and no abuse controls.",
  "scenario": "A single free account iterates ids 1..N and exfiltrates every order in hours.",
  "business_impact": "Full customer order dataset exposed; competitor intelligence and privacy breach.",
  "technical_impact": "Bulk data exfiltration with no alerting.", "mitigations": "None found (searched for rate limiting and anomaly alerts).",
  "remediation": "Fix F-002 first; add per-user rate limits and alerting on sequential access patterns; consider opaque ids.",
  "remediation_complexity": "S", "roadmap": "Immediate", "lens": "red-team",
  "attack_path": {"entry_point": "GET /orders/:id", "attacker_input": "sequential req.params.id values",
    "validation": "None", "authorization": "Authentication only (F-002)", "sink": "SELECT * FROM orders WHERE id = $1",
    "mitigations": "None; no rate limiting or alerting", "preconditions": "Any free account",
    "impact": "Bulk read of all orders"}, "related_findings": ["F-002", "G-001"],
  "verification_notes": "Each link confirmed: F-002 CONFIRMED, sequential PK in migration, no limiter middleware.",
  "verified_by": "independent-subagent", "source": "auditor"})
d["hypotheses"] = [
  {"id": "H-01", "statement": "Ownership is enforced per query, so at least one read path omits it.", "prior": "High",
   "prior_rationale": "No central policy layer seen during recon.", "supporting_evidence_sought": "A query by id without user_id.",
   "refuting_evidence_sought": "Router-level ownership middleware.", "method": "Read src/routes/*.js, grep for user_id.",
   "status": "SUPPORTED", "conclusion": "GET /orders/:id omits user_id (src/routes/orders.js:19).", "related_findings": ["F-002", "F-005"], "origin": "planned"},
  {"id": "H-02", "statement": "JWT validation is vulnerable to algorithm confusion.", "prior": "Medium",
   "prior_rationale": "Common in hand-rolled Express auth.", "supporting_evidence_sought": "jwt.verify without algorithms option.",
   "refuting_evidence_sought": "Explicit algorithms allow-list.", "method": "Read src/middleware/auth.js.",
   "status": "REFUTED", "conclusion": "algorithms: ['RS256'] pinned with aud/iss (src/middleware/auth.js:9).", "related_findings": ["F-003"], "origin": "planned"}]
d["skeptical_review"] = [
  {"id": "SR-01", "target": "G-001", "issue": "Severity could be read as a confirmed leak.", "evidence": "No runtime measurement was authorised.",
   "required_action": "revise", "resolution": "Wording changed to 'leak-like retention risk'; runtime test retained.", "resolved": True}]
json.dump(d, open(f"{out}/deep.json", "w"), indent=1)
r = open(report).read().replace("### L-001", "### F-005 — Attack chain: bulk order scraping\nSee Appendix B2.\n\n### L-001")
r += """
## Appendix B1 — Hypothesis Log
| ID | Statement | Status |
|---|---|---|
| H-01 | Ownership enforced per query | SUPPORTED (F-002, F-005) |
| H-02 | JWT algorithm confusion | REFUTED (F-003) |

## Appendix B2 — Red-Team Scenarios
Chain F-005: enumerable ids + F-002 + no rate limit, leading to bulk scraping.

## Appendix B3 — Skeptical Review
SR-01 on G-001: wording revised.

## Appendix B4 — Evolutionary Architecture
Fitness function: dependency-cruiser rule forbidding routes from querying orders without the ownership helper.

## Appendix B5 — Technical Debt Archaeology
Single-commit history; archaeology window too short for hotspot analysis.
"""
open(f"{out}/deep-report.md", "w").write(r)
d["skeptical_review"][0]["resolved"] = False
json.dump(d, open(f"{out}/deep-unresolved.json", "w"), indent=1)
PY
python3 "$TOOLS/validate_findings.py" --repo "$FIX/orders-api" --findings "$OUT/deep.json" \
  --report "$OUT/deep-report.md" --ledger "$OUT/deep-ledger.json"
if python3 "$TOOLS/validate_findings.py" --repo "$FIX/orders-api" --findings "$OUT/deep-unresolved.json" \
     --report "$OUT/deep-report.md" --ledger "$OUT/deep-bad-ledger.json" > "$OUT/deep-bad.log"; then
  echo "FAIL: unresolved skeptical-review challenge accepted"; exit 1
fi
grep -q "unresolved" "$OUT/deep-bad.log" || { echo "FAIL: unresolved challenge not reported"; exit 1; }
echo "    deep mode validated; unresolved challenge correctly blocks"

echo "4/5 building the deep demo PDF"
python3 "$TOOLS/build_report.py" --report "$OUT/deep-report.md" \
  --findings "$OUT/deep.json" --ledger "$OUT/deep-ledger.json" --out "$OUT/deep-report.pdf"
[ -s "$OUT/deep-report.pdf" ] || { echo "FAIL: deep PDF not produced"; exit 1; }

echo "5/5 building the standard demo PDF"
python3 "$TOOLS/build_report.py" --report "$FIX/orders-api-report.md" \
  --findings "$SAMPLE" --ledger "$OUT/ledger.json" --out "$OUT/report.pdf"
[ -s "$OUT/report.pdf" ] || { echo "FAIL: PDF not produced"; exit 1; }
if [ -n "${ARCHPROOF_KEEP_PDF:-}" ]; then cp "$OUT/report.pdf" "$ARCHPROOF_KEEP_PDF"; cp "$OUT/deep-report.pdf" "${ARCHPROOF_KEEP_PDF%.pdf}-deep.pdf"; echo "    copied to $ARCHPROOF_KEEP_PDF (+ -deep)"; fi
echo "ALL CHECKS PASSED"
