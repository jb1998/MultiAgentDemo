#!/usr/bin/env bash
# Run all backend test suites with clear sections
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== Unit Tests ==="
python -m pytest tests/unit -m unit -q --tb=short

echo ""
echo "=== Integration Tests ==="
python -m pytest tests/integration -m integration -q --tb=short

echo ""
echo "=== API Tests ==="
python -m pytest tests/api -m api -q --tb=short

echo ""
echo "=== End-to-End Tests ==="
python -m pytest tests/e2e -m e2e -q --tb=short

echo ""
echo "=== Full suite ==="
python -m pytest tests/ -q --tb=short
