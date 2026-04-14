#!/bin/bash

# Convenience script to run performance benchmarks
# Usage: ./benchmarks/run_benchmarks.sh

set -e

echo "🔬 Running Performance Benchmarks"
echo "=================================="
echo ""

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Install with: pip install pytest"
    exit 1
fi

# Run benchmarks with verbose output
pytest benchmarks/test_performance.py -v -s

echo ""
echo "✅ Benchmarks complete!"
echo ""
echo "Note: These are performance measurements, not strict pass/fail tests."
echo "For CI, thresholds are intentionally loose to avoid flakiness."
