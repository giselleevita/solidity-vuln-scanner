# SARIF Example Workflow

This repository includes a reusable workflow template at:

- `.github/workflow-templates/solidity-sarif-gate.yml`

Use it as a baseline for projects that want:

- Solidity scan execution in CI
- SARIF upload to GitHub Code Scanning
- Severity gate enforcement (`high` by default)

## Quick Start

1. Copy the template into your repository workflows.
2. Ensure your contracts are under `contracts/**/*.sol` (or adjust path).
3. Add `SOLIDITY_SCANNER_API_KEY` to repository secrets.

## Minimal Example

```yaml
name: Solidity SARIF

on:
  pull_request:
  push:
    branches: [main]

jobs:
  scan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@v6
      - uses: ./.github/actions/solidity-scan
        with:
          api-key: ${{ secrets.SOLIDITY_SCANNER_API_KEY }}
          paths: contracts/**/*.sol
          report-format: sarif
          severity-gate: high
```
