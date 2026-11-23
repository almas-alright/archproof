#!/usr/bin/env bash
# ArchProof self-test: validates the sample findings against the demo fixture,
# checks that broken findings are rejected, and builds the demo PDF.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL="$ROOT/skills/architecture-audit"
FIX="$ROOT/tests/fixtures"
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT

echo "1/3 validating sample findings against the fixture repository"
python3 "$SKILL/scripts/validate_findings.py" --repo "$FIX/orders-api" \
  --findings "$SKILL/examples/sample-findings.json" --report "$FIX/orders-api-report.md" \
  --ledger "$OUT/ledger.json"

echo "2/3 checking that the validator rejects broken findings"
python3 - "$SKILL/examples/sample-findings.json" "$OUT/broken.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
f = d["findings"]
f[1]["locations"][0]["start_line"] = f[1]["locations"][0]["end_line"] = 25   # wrong line numbers
f[2]["severity"] = "CRITICAL"                                                 # severity without rationale
f[4]["verification_status"] = "UNVERIFIED"; f[4]["severity"] = "HIGH"         # unverified above the cap
f[0]["evidence_description"] += ' password = "S3cretValue123"'                # leaked secret
json.dump(d, open(sys.argv[2], "w"))
PY
if python3 "$SKILL/scripts/validate_findings.py" --repo "$FIX/orders-api" --findings "$OUT/broken.json" \
     --report "$FIX/orders-api-report.md" --ledger "$OUT/broken-ledger.json" > "$OUT/broken.log"; then
  echo "FAIL: validator accepted broken findings"; exit 1
fi
for expect in "evidence_snippet not found" "add severity_rationale" "capped at MEDIUM" "unredacted secret"; do
  grep -q "$expect" "$OUT/broken.log" || { echo "FAIL: missing expected error: $expect"; cat "$OUT/broken.log"; exit 1; }
done
echo "    broken findings correctly rejected"

echo "3/3 building the demo PDF"
python3 "$SKILL/scripts/build_report.py" --report "$FIX/orders-api-report.md" \
  --findings "$SKILL/examples/sample-findings.json" --ledger "$OUT/ledger.json" --out "$OUT/report.pdf"
[ -s "$OUT/report.pdf" ] || { echo "FAIL: PDF not produced"; exit 1; }
if [ -n "${ARCHPROOF_KEEP_PDF:-}" ]; then cp "$OUT/report.pdf" "$ARCHPROOF_KEEP_PDF"; echo "    copied to $ARCHPROOF_KEEP_PDF"; fi
echo "ALL CHECKS PASSED"
