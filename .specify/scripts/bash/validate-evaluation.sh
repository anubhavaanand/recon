#!/usr/bin/env bash
# RECON Evaluation Validation Script
# Integrated into CI/pre-commit workflows.
set -euo pipefail

RECON_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$RECON_ROOT"

VENV_PYTHON="${VENV_PYTHON:-python3}"
PYTEST="${VENV_PYTHON} -m pytest"

echo "=== RECON Evaluation Validation ==="
echo ""

# ── Phase A: Foundation ──────────────────────────────────
echo "─── Phase A: Foundation ───────────────────────────────"
echo ""

echo "[1/6] Import Validation..."
$PYTEST tests/test_imports.py -q --tb=short 2>&1 | tail -5

echo ""
echo "[2/6] Health Check..."
$VENV_PYTHON tests/health_check.py --format=critical 2>&1

echo ""
# ── Phase B: Component Testing ────────────────────────────
echo "─── Phase B: Component Testing ─────────────────────────"
echo ""

echo "[3/6] Widget & Tab Tests..."
$PYTEST tests/test_tui_components.py tests/test_tab_integration.py -q --tb=short 2>&1 | tail -5

echo ""
echo "[4/6] Scoring & Search Tests..."
$PYTEST tests/test_scoring.py tests/test_search.py -q --tb=short 2>&1 | tail -5

echo ""
# ── Phase C: Advanced ─────────────────────────────────────
echo "─── Phase C: Advanced Tests ────────────────────────────"
echo ""

echo "[5/6] Cache, Performance & Error Handling..."
$PYTEST tests/test_cache_validation.py tests/test_performance.py tests/test_error_handling.py tests/test_error_voice.py -q --tb=short 2>&1 | tail -5

echo ""
# ── Phase D: Reporting ────────────────────────────────────
echo "─── Phase D: Reporting ─────────────────────────────────"
echo ""

echo "[6/6] Evaluation Report..."
$VENV_PYTHON tests/evaluation_report.py --format=json 2>&1 | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"Tests: {d['test_summary']['passed']} passed / {d['test_summary']['failed']} failed / {d['test_summary']['skipped']} skipped\"); print(f\"Coverage: {d.get('coverage_pct', 'N/A')}%\")"

echo ""
echo "=== Validation Complete ==="

# ── Exit code determination ──────────────────────────────
$PYTEST tests/test_imports.py tests/test_tui_components.py tests/test_tab_integration.py tests/test_scoring.py tests/test_search.py -q --tb=short > /dev/null 2>&1
RESULT=$?
if [ $RESULT -eq 0 ]; then
    echo "Status: ALL CHECKS PASSED"
    exit 0
else
    echo "Status: SOME CHECKS FAILED (exit code: $RESULT)"
    exit $RESULT
fi
