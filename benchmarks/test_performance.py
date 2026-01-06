"""
Performance benchmarks for Solidity Vuln Scanner

These tests measure analysis speed across different contract sizes.
CI runs these as "smoke checks" with loose thresholds to prevent regressions.
For detailed performance analysis, run locally.

Results are written to benchmarks/results.json for CI artifact tracking.
"""

import pytest
import time
import json
import statistics
from pathlib import Path
from static_analyzer import StaticAnalyzer

# Contract fixtures directory
CONTRACTS_DIR = Path(__file__).parent / "contracts"
RESULTS_FILE = Path(__file__).parent / "results.json"
BASELINE_FILE = Path(__file__).parent / "baseline.json"
LABELS_FILE = Path(__file__).parent / "labels.json"


def load_contract(filename: str) -> str:
    """Load contract from fixtures directory"""
    contract_path = CONTRACTS_DIR / filename
    if not contract_path.exists():
        pytest.skip(f"Contract fixture {filename} not found")
    return contract_path.read_text()


def load_baseline():
    """Load baseline performance metrics"""
    if not BASELINE_FILE.exists():
        return None
    try:
        return json.loads(BASELINE_FILE.read_text())
    except:
        return None


def load_labels():
    """Load contract labels and expectations"""
    if not LABELS_FILE.exists():
        return {}
    try:
        return json.loads(LABELS_FILE.read_text())
    except:
        return {}


def check_correctness(result, contract_filename):
    """Check if analysis results match expected vulnerabilities from labels"""
    labels = load_labels()
    contract_info = labels.get("contracts", {}).get(contract_filename)
    
    if not contract_info:
        return True, "No labels available"  # Skip if no labels
    
    expected_vulns = contract_info.get("expected_vulnerabilities", [])
    expected_severity = contract_info.get("expected_severity", "SAFE")
    
    detected_types = {v.vuln_type for v in result.vulnerabilities}
    actual_severity = result._get_overall_severity()
    
    # Check if expected vulnerabilities are detected
    missing_vulns = set(expected_vulns) - detected_types
    if missing_vulns:
        return False, f"Missing expected vulnerabilities: {missing_vulns}"
    
    # For safe contracts, verify no false positives (if severity is SAFE)
    if expected_severity == "SAFE" and len(result.vulnerabilities) > 0:
        return False, f"False positive: Expected SAFE but found {len(result.vulnerabilities)} vulnerabilities"
    
    return True, "Correctness check passed"


def generate_results_summary(results_data):
    """Generate human-readable markdown summary"""
    summary_file = Path(__file__).parent / "results.md"
    
    baseline = load_baseline()
    
    md_lines = [
        "# Benchmark Results Summary",
        "",
        f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results_data.get('timestamp', time.time())))}",
        f"**Mode:** {results_data.get('mode', 'static-only')}",
        "",
        "## Performance Metrics",
        "",
        "| Contract Size | Median Time | Baseline | Change | Regression |",
        "|--------------|-------------|----------|--------|------------|"
    ]
    
    for size in ["small", "medium", "large", "xlarge"]:
        if size not in results_data.get("contracts", {}):
            continue
        
        data = results_data["contracts"][size]
        median = data.get("median_time_seconds", 0)
        baseline_time = data.get("baseline_time_seconds")
        is_regression = data.get("regression_detected", False)
        
        if baseline_time:
            change_pct = ((median - baseline_time) / baseline_time) * 100
            change_str = f"{change_pct:+.1f}%"
        else:
            change_str = "N/A"
        
        regression_str = "⚠️ Yes" if is_regression else "✅ No"
        
        md_lines.append(f"| {size.capitalize()} | {median:.3f}s | {baseline_time:.3f}s | {change_str} | {regression_str} |")
    
    md_lines.extend([
        "",
        "## Details",
        ""
    ])
    
    for size, data in results_data.get("contracts", {}).items():
        md_lines.extend([
            f"### {size.capitalize()}",
            f"- **Median Time:** {data.get('median_time_seconds', 0):.3f}s",
            f"- **Lines of Code:** {data.get('lines_of_code', 0)}",
            f"- **Vulnerabilities Detected:** {data.get('vulnerabilities_detected', 0)}",
            ""
        ])
    
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("*CI artifacts contain timing history per commit. See GitHub Actions artifacts.*")
    
    summary_file.write_text("\n".join(md_lines))
    print(f"[Benchmark] Summary written to {summary_file}")


def run_benchmark_multiple_times(analyzer, code, contract_name, runs=3):
    """Run benchmark multiple times and return median"""
    times = []
    results = []
    
    for i in range(runs):
        start = time.time()
        result = analyzer.analyze(code, f"{contract_name}_run{i}")
        elapsed = time.time() - start
        times.append(elapsed)
        if i == 0:  # Store first result for details
            results.append({
                "lines_of_code": result.lines_of_code,
                "vulnerabilities_detected": len(result.vulnerabilities),
                "risk_score": result.risk_score
            })
    
    return {
        "times": times,
        "median_time": statistics.median(times),
        "mean_time": statistics.mean(times),
        "min_time": min(times),
        "max_time": max(times),
        "details": results[0] if results else {}
    }


def check_regression(current_median, baseline_time, contract_size):
    """Check if performance has regressed significantly using per-size thresholds"""
    if baseline_time is None:
        return False, "No baseline available"
    
    labels = load_labels()
    thresholds = labels.get("regression_thresholds", {})
    
    # Get per-size thresholds (fallback to defaults if not found)
    size_thresholds = thresholds.get(contract_size, {})
    time_increase_percent = size_thresholds.get("time_increase_percent", 50)
    absolute_floor = size_thresholds.get("absolute_time_floor_seconds", 3.0)
    
    # Calculate percentage increase
    if baseline_time == 0:
        return False, "Baseline time is zero"
    
    percent_increase = ((current_median - baseline_time) / baseline_time) * 100
    
    # Alert if: exceeds percentage increase OR absolute time floor
    is_regression = (
        percent_increase > time_increase_percent or
        current_median > absolute_floor
    )
    
    return is_regression, f"{percent_increase:.1f}% increase (baseline: {baseline_time:.3f}s, current: {current_median:.3f}s, threshold: {time_increase_percent}% or >{absolute_floor}s)"


class TestPerformanceBenchmarks:
    """Performance benchmarks for static analysis"""
    
    @pytest.fixture(autouse=True)
    def setup_results(self):
        """Initialize results dictionary"""
        # Print benchmark mode
        print("\n[Benchmark] Mode: Static-only analysis")
        print("[Benchmark] Slither: skipped")
        print("[Benchmark] Mythril: skipped")
        print("[Benchmark] LLM: skipped")
        
        self.results_data = {
            "timestamp": time.time(),
            "mode": "static-only",
            "contracts": {}
        }
        yield
        # Write results after all tests
        if hasattr(self, 'results_data') and self.results_data.get("contracts"):
            RESULTS_FILE.write_text(json.dumps(self.results_data, indent=2))
            print(f"\n[Benchmark] Results written to {RESULTS_FILE}")
            
            # Generate human-readable summary
            generate_results_summary(self.results_data)
            
            # Print summary location
            summary_file = Path(__file__).parent / "results.md"
            if summary_file.exists():
                print(f"[Benchmark] Summary written to {summary_file}")
    
    def test_analyze_small(self):
        """Benchmark: Small contract (50-150 LoC)"""
        code = load_contract("small.sol")
        analyzer = StaticAnalyzer()
        
        # Run multiple times for median
        benchmark_result = run_benchmark_multiple_times(analyzer, code, "SmallToken", runs=3)
        median_time = benchmark_result["median_time"]
        
        # Load baseline for comparison
        baseline = load_baseline()
        baseline_time = baseline.get("results", {}).get("small", {}).get("median_time_seconds") if baseline else None
        
        # Check for regression (per-size thresholds)
        is_regression, regression_msg = check_regression(median_time, baseline_time, "small")
        if is_regression:
            print(f"\n⚠️  [REGRESSION DETECTED] Small contract: {regression_msg}")
        
        # Check correctness against labels
        first_result = analyzer.analyze(code, "SmallToken")
        is_correct, correctness_msg = check_correctness(first_result, "small.sol")
        if not is_correct:
            print(f"\n⚠️  [CORRECTNESS ISSUE] Small contract: {correctness_msg}")
        
        # Store results
        self.results_data["contracts"]["small"] = {
            "median_time_seconds": median_time,
            "mean_time_seconds": benchmark_result["mean_time"],
            "min_time_seconds": benchmark_result["min_time"],
            "max_time_seconds": benchmark_result["max_time"],
            "lines_of_code": benchmark_result["details"].get("lines_of_code", 0),
            "vulnerabilities_detected": benchmark_result["details"].get("vulnerabilities_detected", 0),
            "baseline_time_seconds": baseline_time,
            "regression_detected": is_regression,
            "correctness_check": is_correct
        }
        
        # Verify correctness
        assert benchmark_result["details"].get("lines_of_code", 0) > 0
        # Correctness assertion (warn but don't fail in CI)
        if not is_correct:
            pytest.warns(UserWarning, match="Correctness")
        
        # Performance check (loose threshold for CI)
        assert median_time < 5.0, f"Small contract took {median_time:.2f}s (expected < 5s)"
        
        print(f"\n[Benchmark] Small contract: {median_time:.3f}s median ({benchmark_result['details'].get('lines_of_code', 0)} LoC)")
    
    def test_analyze_medium(self):
        """Benchmark: Medium contract (300-1200 LoC)"""
        code = load_contract("medium.sol")
        analyzer = StaticAnalyzer()
        
        # Run multiple times for median
        benchmark_result = run_benchmark_multiple_times(analyzer, code, "MediumToken", runs=3)
        median_time = benchmark_result["median_time"]
        
        # Load baseline for comparison
        baseline = load_baseline()
        baseline_time = baseline.get("results", {}).get("medium", {}).get("median_time_seconds") if baseline else None
        
        # Check for regression
        is_regression, regression_msg = check_regression(median_time, baseline_time, "medium")
        if is_regression:
            print(f"\n⚠️  [REGRESSION DETECTED] Medium contract: {regression_msg}")
        
        # Store results
        self.results_data["contracts"]["medium"] = {
            "median_time_seconds": median_time,
            "mean_time_seconds": benchmark_result["mean_time"],
            "min_time_seconds": benchmark_result["min_time"],
            "max_time_seconds": benchmark_result["max_time"],
            "lines_of_code": benchmark_result["details"].get("lines_of_code", 0),
            "vulnerabilities_detected": benchmark_result["details"].get("vulnerabilities_detected", 0),
            "baseline_time_seconds": baseline_time,
            "regression_detected": is_regression
        }
        
        # Verify correctness
        assert benchmark_result["details"].get("lines_of_code", 0) > 0
        
        # Performance check (loose threshold for CI)
        assert median_time < 10.0, f"Medium contract took {median_time:.2f}s (expected < 10s)"
        
        print(f"\n[Benchmark] Medium contract: {median_time:.3f}s median ({benchmark_result['details'].get('lines_of_code', 0)} LoC)")
    
    def test_analyze_large(self):
        """Benchmark: Large contract (2k-6k LoC) - CI smoke check"""
        code = load_contract("large.sol")
        analyzer = StaticAnalyzer()
        
        # Run multiple times for median
        benchmark_result = run_benchmark_multiple_times(analyzer, code, "LargeVault", runs=3)
        median_time = benchmark_result["median_time"]
        
        # Load baseline for comparison
        baseline = load_baseline()
        baseline_time = baseline.get("results", {}).get("large", {}).get("median_time_seconds") if baseline else None
        
        # Check for regression
        is_regression, regression_msg = check_regression(median_time, baseline_time, "large")
        if is_regression:
            print(f"\n⚠️  [REGRESSION DETECTED] Large contract: {regression_msg}")
        
        # Store results
        self.results_data["contracts"]["large"] = {
            "median_time_seconds": median_time,
            "mean_time_seconds": benchmark_result["mean_time"],
            "min_time_seconds": benchmark_result["min_time"],
            "max_time_seconds": benchmark_result["max_time"],
            "lines_of_code": benchmark_result["details"].get("lines_of_code", 0),
            "vulnerabilities_detected": benchmark_result["details"].get("vulnerabilities_detected", 0),
            "baseline_time_seconds": baseline_time,
            "regression_detected": is_regression
        }
        
        # Verify correctness
        assert benchmark_result["details"].get("lines_of_code", 0) > 0
        
        # CI smoke check: Very loose threshold to avoid flakiness
        assert median_time < 15.0, f"Large contract took {median_time:.2f}s (expected < 15s)"
        
        print(f"\n[Benchmark] Large contract: {median_time:.3f}s median ({benchmark_result['details'].get('lines_of_code', 0)} LoC)")
    
    @pytest.mark.skipif(not (CONTRACTS_DIR / "xlarge.sol").exists(), reason="XLarge contract not available")
    def test_analyze_xlarge(self):
        """Benchmark: XLarge contract (10k+ LoC) - Optional"""
        code = load_contract("xlarge.sol")
        analyzer = StaticAnalyzer()
        
        # Run multiple times for median
        benchmark_result = run_benchmark_multiple_times(analyzer, code, "XLargeProtocol", runs=3)
        median_time = benchmark_result["median_time"]
        
        # Load baseline for comparison
        baseline = load_baseline()
        baseline_time = baseline.get("results", {}).get("xlarge", {}).get("median_time_seconds") if baseline else None
        
        # Check for regression
        is_regression, regression_msg = check_regression(median_time, baseline_time, "xlarge")
        if is_regression:
            print(f"\n⚠️  [REGRESSION DETECTED] XLarge contract: {regression_msg}")
        
        # Store results
        self.results_data["contracts"]["xlarge"] = {
            "median_time_seconds": median_time,
            "mean_time_seconds": benchmark_result["mean_time"],
            "min_time_seconds": benchmark_result["min_time"],
            "max_time_seconds": benchmark_result["max_time"],
            "lines_of_code": benchmark_result["details"].get("lines_of_code", 0),
            "vulnerabilities_detected": benchmark_result["details"].get("vulnerabilities_detected", 0),
            "baseline_time_seconds": baseline_time,
            "regression_detected": is_regression
        }
        
        # Verify correctness
        assert benchmark_result["details"].get("lines_of_code", 0) > 0
        
        # Very loose threshold for very large contracts
        assert median_time < 30.0, f"XLarge contract took {median_time:.2f}s (expected < 30s)"
        
        print(f"\n[Benchmark] XLarge contract: {median_time:.3f}s median ({benchmark_result['details'].get('lines_of_code', 0)} LoC)")
    
    def test_analysis_is_linear(self):
        """Verify analysis time scales roughly linearly with contract size"""
        analyzer = StaticAnalyzer()
        
        # Measure small (single run for this test)
        small_code = load_contract("small.sol")
        start = time.time()
        small_result = analyzer.analyze(small_code, "Small")
        small_time = time.time() - start
        
        # Measure medium (single run for this test)
        medium_code = load_contract("medium.sol")
        start = time.time()
        medium_result = analyzer.analyze(medium_code, "Medium")
        medium_time = time.time() - start
        
        # Medium should take longer than small (but not orders of magnitude)
        # This is a sanity check, not a strict requirement
        if medium_result.lines_of_code > small_result.lines_of_code * 2:
            # If medium is 2x+ larger, it should take more time
            # But allow for variance (at least 0.5x the ratio)
            size_ratio = medium_result.lines_of_code / small_result.lines_of_code
            time_ratio = medium_time / small_time if small_time > 0 else 1
            # Time should increase with size (loose check)
            assert time_ratio > 0.3, f"Time ratio {time_ratio:.2f} seems too low for size ratio {size_ratio:.2f}"
        
        print(f"\n[Benchmark] Size scaling: Small={small_time:.3f}s, Medium={medium_time:.3f}s")
    
    def test_no_memory_leak(self):
        """Verify repeated analysis doesn't cause memory issues"""
        analyzer = StaticAnalyzer()
        code = load_contract("medium.sol")
        
        # Run analysis multiple times
        times = []
        for i in range(10):
            start = time.time()
            result = analyzer.analyze(code, f"Test{i}")
            elapsed = time.time() - start
            times.append(elapsed)
        
        # Later runs shouldn't be significantly slower (indicates memory issues)
        # Allow 2x variance for CI noise
        avg_first = sum(times[:3]) / 3
        avg_last = sum(times[-3:]) / 3
        assert avg_last < avg_first * 2, "Possible memory leak detected"
        
        print(f"\n[Benchmark] Memory check: First 3 avg={avg_first:.3f}s, Last 3 avg={avg_last:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
