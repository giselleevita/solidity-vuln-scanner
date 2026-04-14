# Performance Benchmarks

**TL;DR:** This benchmark suite measures static-analysis performance across contract sizes, detects regressions safely in CI, and uploads per-commit results as artifacts.

This directory contains performance benchmarks for Solidity Vuln Scanner.

## Overview

Benchmarks measure analysis speed across different contract sizes to:
- Track performance regressions
- Establish baseline expectations
- Validate scalability

**Mode:** Static-only analysis (Slither, Mythril, and LLM are disabled in benchmarks by default)

## Structure

```
benchmarks/
├── contracts/          # Test contracts of varying sizes
│   ├── small.sol      # 50-150 LoC
│   ├── medium.sol     # 300-1200 LoC
│   ├── large.sol       # 2k-6k LoC
│   └── xlarge.sol      # 10k+ LoC
├── baseline.json       # Baseline performance metrics (committed)
├── labels.json         # Contract metadata and thresholds
├── test_performance.py # Performance test suite
├── run_benchmarks.sh  # Convenience runner
└── README.md          # This file
```

## Running Benchmarks

### Local Development

```bash
# Run all benchmarks
python -m pytest benchmarks/test_performance.py -v

# Run with timing details
python -m pytest benchmarks/test_performance.py -v -s

# Run specific size
python -m pytest benchmarks/test_performance.py::test_analyze_small -v
```

### Using Runner Script

```bash
chmod +x benchmarks/run_benchmarks.sh
./benchmarks/run_benchmarks.sh
```

## Performance Expectations

**Baseline (developer-grade laptop or GitHub CI runner, static-only analysis):**

| Contract Size | Expected Time | Notes |
|--------------|---------------|-------|
| Small (50-150 LoC) | < 0.5s | Simple contracts |
| Medium (300-1200 LoC) | < 1.5s | Typical production contracts |
| Large (2k-6k LoC) | < 3s | Complex contracts |
| XLarge (10k+ LoC) | < 10s | Very large contracts |

**Note:** These are approximate. Actual times depend on:
- Hardware performance
- System load
- Contract complexity (not just LoC)

**Complexity expectation:** The static analyzer is expected to scale approximately linearly with source size (O(n) over lines of code). Benchmarks are designed to catch accidental quadratic behavior.

## CI Integration

### When Benchmarks Run

- **PRs:** Smoke check only (small contract, no artifact upload)
- **Main branch merges:** Full benchmark suite + artifact upload
- **Manual:** `workflow_dispatch` trigger for full suite anytime

### CI Artifacts

Every CI run on main branch:
1. Runs benchmarks in static-only mode
2. Writes results to `benchmarks/results.json` and `benchmarks/results.md`
3. Uploads as workflow artifact named `benchmarks-${{ github.sha }}`

**CI artifacts contain timing history per commit.** Artifacts are retained for 30 days.

**Artifact contents:**
- `results.json` - Intended for automated comparison and tooling
- `results.md` - Human-readable summary for reviewers

See [docs/CI_ARTIFACTS.md](../docs/CI_ARTIFACTS.md) for detailed guide on accessing artifacts.

### Regression Detection

CI checks for performance regressions using:
- **Median of 3 runs** (reduces noise)
  - Median is used instead of mean to reduce sensitivity to transient CI noise and cold-start effects
- **Baseline comparison** from `benchmarks/baseline.json`
- **Per-size thresholds:**
  - Small: >100% increase OR >1s absolute
  - Medium: >75% increase OR >2s absolute
  - Large: >50% increase OR >3s absolute
  - XLarge: >35% increase OR >5s absolute

This avoids false alarms on noisy CI runners while catching real O(n²) regressions.

## Baseline Management

**Who updates baseline:** Maintainer only

**When to update:**
- After intentional performance improvement
- After accepting a known performance regression
- When baseline becomes stale (>6 months old)

**How to update baseline:**

1. **Confirm CI runner type** (ubuntu-latest)
2. **Ensure static-only mode** (no LLM, no external tools)
3. **Run benchmarks 3-5 times locally:**
   ```bash
   pytest benchmarks/test_performance.py -v
   ```
4. **Review `benchmarks/results.json`** - use median values
5. **Update `benchmarks/baseline.json`** with new median times
6. **Commit the updated baseline**

**Baseline Update Checklist:**
- [ ] Confirmed runner type matches CI
- [ ] Verified static-only mode (no LLM/Slither/Mythril)
- [ ] Ran benchmarks 3-5 times
- [ ] Used median values (not single run)
- [ ] Updated all contract sizes in baseline.json
- [ ] Committed with clear message

## What's NOT Benchmarked

- **LLM analysis** - Too variable (API latency, rate limits)
- **Slither/Mythril** - External tools, not core scanner performance
- **Network requests** - Focus on static analysis speed

## Correctness Checks

Benchmarks also verify correctness:
- Expected vulnerabilities are detected for vulnerable fixtures
- No false positives for safe fixtures
- Severity levels match expectations

Benchmarks intentionally avoid probabilistic components to ensure deterministic results across runs.

See `labels.json` for expected findings per contract.

## Adding New Benchmarks

1. Add contract to `contracts/` folder
2. Add entry to `labels.json` with:
   - Size range
   - Expected vulnerabilities (if any)
   - Expected severity
3. Add test case in `test_performance.py`
4. Update baseline.json after establishing performance
5. Update this README with expected performance

## Next Steps

- **Installation**: See [docs/INSTALL.md](../docs/INSTALL.md)
- **Usage**: See [docs/USAGE.md](../docs/USAGE.md)
- **Architecture**: See [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)
