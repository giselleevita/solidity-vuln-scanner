# Installing Slither & Mythril

## Quick Installation

### Option 1: Automated Script (Recommended)

```bash
chmod +x install_tools.sh
./install_tools.sh
```

### Option 2: Manual Installation

**Slither:**
```bash
pip install slither-analyzer
```

**Mythril:**
```bash
# Option A: pip
pip install mythril

# Option B: Homebrew (macOS)
brew install mythril
```

## Verify Installation

```bash
# Check Slither
slither --version

# Check Mythril  
myth version
```

## Troubleshooting

**"Command not found" after installation:**
- Add Python scripts to PATH: `export PATH="$HOME/.local/bin:$PATH"`
- Or use: `python -m slither` instead of `slither`

**Installation fails:**
- Update pip: `pip install --upgrade pip`
- Install system dependencies (Linux):
  ```bash
  sudo apt-get update
  sudo apt-get install python3-dev python3-pip
  ```

**Mythril requires Solidity compiler:**
```bash
# Install solc-select (recommended)
pip install solc-select
solc-select install 0.8.0
solc-select use 0.8.0
```

## Why Install These Tools?

- **Slither:** Industry-standard static analyzer, finds 100+ vulnerability types
- **Mythril:** Symbolic execution tool, finds logic-level vulnerabilities
- **Cross-validation:** Compare results across multiple tools for better accuracy

## Using in the Scanner

1. Install tools (see above)
2. Go to "Cross-Validate" tab in the UI
3. Check "Run Slither" and/or "Run Mythril"
4. Click "Run Cross-Validation"

The scanner will automatically detect if tools are installed and show status in the UI.

