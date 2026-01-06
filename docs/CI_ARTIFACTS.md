# CI Artifacts Guide

**TL;DR:** Go to Actions → Workflow Run → Artifacts to download coverage and benchmark results for each commit.

## Where to Find CI Artifacts

CI artifacts are uploaded after each workflow run. Here's how to access them:

### Step-by-Step

1. **Go to your GitHub repository**
2. **Click the "Actions" tab** (top navigation)
3. **Click on a workflow run** (from the list)
4. **Scroll down to the "Artifacts" section** (at the bottom of the run page)
5. **Download the artifacts** you need

### Available Artifacts

#### 1. Coverage Report (`coverage-<sha>`)

- **What it contains:** HTML coverage report
- **When uploaded:** After every test run
- **Retention:** 30 days
- **How to use:** Download and open `htmlcov/index.html` in a browser

#### 2. Benchmark Results (`benchmarks-<sha>`)

- **What it contains:**
  - `results.json` - Machine-readable benchmark data
  - `results.md` - Summary table showing per-contract median runtime, baseline comparison, and regression warnings (if any)
- **When uploaded:** Only on main branch merges (not PRs)
- **Why not on PRs:** Benchmarks are skipped on pull requests to avoid noisy timing results and unnecessary CI cost
- **Retention:** 30 days
- **Baseline comparison:** Benchmarks are compared against the committed baseline in `benchmarks/baseline.json`. See [benchmarks/README.md](../benchmarks/README.md) for baseline update procedures.
- **How to use:**
  - Download the artifact
  - Open `results.md` for a quick summary
  - Use `results.json` for programmatic analysis

### Artifact Naming

Artifacts are named with the commit SHA for traceability:
- `coverage-abc123def456...`
- `benchmarks-abc123def456...`

This allows you to:
- Track performance over time
- Compare results across commits
- Identify when regressions occurred

### Viewing Artifacts Without Download

You can also view artifact contents directly in GitHub:
1. Click on the artifact name
2. Browse files in the artifact
3. View text files inline

### Troubleshooting

**"No artifacts found"**
- Artifacts only appear after workflow completion
- Check if the workflow step that uploads artifacts succeeded
- PRs don't upload benchmark artifacts (only main branch does)

**"Artifact expired"**
- Artifacts are retained for 30 days
- After expiration, they're automatically deleted
- Download important artifacts before they expire

### When to Use Which Artifact

**Coverage report:**
- Verify test completeness
- Identify untested code paths
- Track coverage trends over time

**Benchmark results:**
- Check for performance regressions or improvements after changes
- Compare performance across commits
- Validate that optimizations had the intended effect

**results.json:**
- Programmatic comparison or historical analysis
- Building performance dashboards
- Automated regression detection

**results.md:**
- Quick human-readable performance summary
- Sharing results with team members
- Reviewing performance changes in PRs

### Best Practices

1. **Download important artifacts** before they expire (30 days)
2. **Compare artifacts** across commits to track trends
3. **Use results.md** for quick performance overview
4. **Use results.json** for detailed analysis
5. **Note:** Benchmark timings are influenced by CI runner variability. Median-based comparisons and large regression thresholds are used to minimize noise.

---

**Note:** CI artifacts contain timing history per commit. See [benchmarks/README.md](../benchmarks/README.md) for detailed benchmark documentation.
