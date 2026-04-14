# How to Use Solidity Vuln Scanner

A complete guide to using the scanner in different ways.

---

## 🚀 Method 1: Web UI (Easiest - Recommended for Beginners)

### Step 1: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt
```

### Step 2: Start the Services

**Terminal 1 - Start API:**
```bash
python fastapi_api.py
```
You should see: `Uvicorn running on http://0.0.0.0:8000`

**Terminal 2 - Start UI:**
```bash
streamlit run streamlit_ui.py
```
You should see: `You can now view your Streamlit app in your browser.`

### Step 3: Open the Web Interface

1. Open your browser to: **http://localhost:8501**
2. You'll see the scanner interface with tabs:
   - **Analyze** - Main scanning interface
   - **Documentation** - Help and guides
   - **Examples** - Sample contracts

### Step 4: Analyze a Contract

1. **Paste your Solidity code** in the text area (or use the example)
2. **Enter a contract name** (optional, defaults to "Contract")
3. **Choose options:**
   - ✅ **Use LLM Audit** - Check this if you have an API key (optional)
   - ✅ **Run Slither** - Check if Slither is installed (optional)
   - ✅ **Run Mythril** - Check if Mythril is installed (optional)
4. **Click "Analyze Contract"**
5. **Review results:**
   - Risk score (0-100)
   - Overall severity (SAFE, LOW, MEDIUM, HIGH, CRITICAL)
   - List of vulnerabilities with:
     - Line numbers
     - Severity levels
     - Descriptions
     - Code snippets
     - Remediation suggestions

### Step 5: Export Results (Optional)

Scroll down and click:
- **"Download JSON Report"** - For programmatic use
- **"Download Markdown Report"** - For documentation

---

## 🔧 Method 2: REST API (For Integration)

### Start the API

```bash
python fastapi_api.py
```

### Example 1: Basic Analysis

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "contract_code": "pragma solidity ^0.8.0;\n\ncontract Vault {\n    mapping(address => uint256) balances;\n    \n    function withdraw(uint256 amount) public {\n        require(balances[msg.sender] >= amount);\n        (bool success, ) = msg.sender.call{value: amount}(\"\");\n        require(success);\n        balances[msg.sender] -= amount;\n    }\n}",
    "contract_name": "Vault",
    "use_llm_audit": false
  }'
```

**Response:**
```json
{
  "contract_name": "Vault",
  "risk_score": 25,
  "overall_severity": "CRITICAL",
  "vulnerabilities": [
    {
      "type": "reentrancy",
      "severity": "CRITICAL",
      "line": 7,
      "description": "Potential reentrancy vulnerability...",
      "code_snippet": "(bool success, ) = msg.sender.call...",
      "remediation": "Use Checks-Effects-Interactions pattern..."
    }
  ],
  "lines_of_code": 11
}
```

### Example 2: Analysis with SARIF Output (for CI/CD)

```bash
curl -X POST "http://localhost:8000/analyze-sarif" \
  -H "Content-Type: application/json" \
  -d '{
    "contract_code": "pragma solidity ^0.8.0; contract X { function f() public {} }",
    "contract_name": "X",
    "use_llm_audit": false
  }' > results.sarif
```

### Example 3: Upload a File

```bash
curl -X POST "http://localhost:8000/upload-and-analyze" \
  -F "file=@my_contract.sol"
```

### Example 4: Batch Analysis (Multiple Contracts)

```bash
curl -X POST "http://localhost:8000/analyze-batch" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "contract_code": "pragma solidity ^0.8.0; contract A { ... }",
      "contract_name": "ContractA",
      "use_llm_audit": false
    },
    {
      "contract_code": "pragma solidity ^0.8.0; contract B { ... }",
      "contract_name": "ContractB",
      "use_llm_audit": false
    }
  ]'
```

### Example 5: Cross-Validation with External Tools

```bash
curl -X POST "http://localhost:8000/cross-validate" \
  -H "Content-Type: application/json" \
  -d '{
    "contract_code": "pragma solidity ^0.8.0; contract X { ... }",
    "contract_name": "X",
    "use_llm_audit": false,
    "run_slither": true,
    "run_mythril": true
  }'
```

### Interactive API Documentation

Visit **http://localhost:8000/docs** for:
- Interactive API explorer
- Try-it-out functionality
- Request/response schemas

---

## 🐍 Method 3: Python Script (Programmatic Use)

### Example: Basic Static Analysis

```python
from static_analyzer import StaticAnalyzer

# Your contract code
contract_code = """
pragma solidity ^0.8.0;

contract Bank {
    mapping(address => uint256) balance;
    
    function withdraw(uint256 amount) public {
        require(balance[msg.sender] >= amount);
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
        balance[msg.sender] -= amount;
    }
}
"""

# Analyze
analyzer = StaticAnalyzer()
result = analyzer.analyze(contract_code, "Bank")

# Print results
print(f"Risk Score: {result.risk_score}/100")
print(f"Severity: {result._get_overall_severity()}")
print(f"Vulnerabilities: {len(result.vulnerabilities)}")

for vuln in result.vulnerabilities:
    print(f"\n{vuln.vuln_type.upper()}")
    print(f"  Severity: {vuln.severity}")
    print(f"  Line: {vuln.line_number}")
    print(f"  Description: {vuln.description}")
    print(f"  Fix: {vuln.remediation}")
```

### Example: With LLM Audit

```python
from static_analyzer import StaticAnalyzer
from llm_auditor import LLMAuditor

contract_code = "..."  # Your contract

# Static analysis
analyzer = StaticAnalyzer()
static_result = analyzer.analyze(contract_code, "MyContract")

# LLM audit (requires API key in .env)
try:
    auditor = LLMAuditor()
    llm_result = auditor.audit(contract_code, "MyContract")
    print(f"AI Risk Assessment: {llm_result.risk_assessment}")
    print(f"Summary: {llm_result.summary}")
except Exception as e:
    print(f"LLM audit not available: {e}")
```

### Run the Example Script

```bash
python example_usage.py
```

This runs 5 complete examples showing different usage patterns.

---

## 🐳 Method 4: Docker (All-in-One)

### Start Everything with Docker

```bash
# Build and start all services
docker-compose up --build

# Access:
# - UI: http://localhost:8501
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

This includes:
- API server
- Streamlit UI
- Slither container
- Mythril container

No local installation needed!

---

## 📋 Common Use Cases

### Use Case 1: Quick Check Before Deployment

```bash
# 1. Start API
python fastapi_api.py

# 2. In another terminal, analyze
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d @contract.json
```

### Use Case 2: CI/CD Integration

```yaml
# .github/workflows/security.yml
- name: Security Scan
  run: |
    curl -X POST "http://localhost:8000/analyze-sarif" \
      -H "Content-Type: application/json" \
      -d @contract.json > results.sarif
    
- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: results.sarif
```

### Use Case 3: Batch Analysis of Multiple Contracts

```python
import json
from static_analyzer import StaticAnalyzer

contracts = [
    {"name": "Token", "file": "Token.sol"},
    {"name": "Vault", "file": "Vault.sol"},
    {"name": "Router", "file": "Router.sol"}
]

analyzer = StaticAnalyzer()
results = []

for contract in contracts:
    with open(contract["file"], "r") as f:
        code = f.read()
    result = analyzer.analyze(code, contract["name"])
    results.append(result.to_dict())

# Save all results
with open("batch_audit.json", "w") as f:
    json.dump(results, f, indent=2)
```

### Use Case 4: Compare with Other Tools

```bash
# Run this scanner
curl -X POST "http://localhost:8000/analyze" ... > scanner_results.json

# Run Slither
slither contract.sol > slither_results.json

# Run Mythril
mythril analyze contract.sol > mythril_results.json

# Compare results
```

---

## ⚙️ Configuration

### Enable LLM Audit (Optional)

1. **Get an API key:**
   - OpenAI: https://platform.openai.com/api-keys
   - Anthropic: https://console.anthropic.com/

2. **Create `.env` file:**
```env
USE_LLM=true
LLM_PROVIDER=openai  # or "anthropic"
LLM_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4o-mini
```

3. **Restart the API:**
```bash
python fastapi_api.py
```

### Configure Rate Limits

Edit `.env`:
```env
RATE_LIMIT_PER_MINUTE=60  # Default: 60 requests/minute
```

### Adjust Timeouts

Edit `.env`:
```env
TIMEOUT_SECONDS=30  # Default: 30 seconds
```

---

## 🎯 Quick Reference

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze` | POST | Analyze single contract |
| `/analyze-sarif` | POST | Analyze with SARIF output |
| `/analyze-batch` | POST | Analyze multiple contracts |
| `/upload-and-analyze` | POST | Upload file and analyze |
| `/cross-validate` | POST | Analyze with external tools |
| `/health` | GET | Health check |
| `/vulnerabilities` | GET | List all vulnerability types |
| `/docs` | GET | Interactive API documentation |

### Makefile Commands

```bash
make api          # Start API server
make ui           # Start Streamlit UI
make test         # Run tests
make install      # Install dependencies
```

### Common Issues

**Problem:** "Module not found"  
**Solution:** `pip install -r requirements.txt`

**Problem:** "Port already in use"  
**Solution:** Change port in `.env` or kill existing process

**Problem:** "LLM audit not working"  
**Solution:** Check `.env` has `USE_LLM=true` and valid `LLM_API_KEY`

**Problem:** "Slither/Mythril not found"  
**Solution:** Install tools or use Docker: `docker-compose up`

---

## 📚 Next Steps

- **Detailed Usage:** See [docs/USAGE.md](docs/USAGE.md)
- **Installation:** See [docs/INSTALL.md](docs/INSTALL.md)
- **Docker Setup:** See [docs/DOCKER.md](docs/DOCKER.md)
- **Architecture:** See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Security Guidelines:** See [SECURITY.md](SECURITY.md)

---

## 💡 Tips

1. **Start simple:** Use the Web UI first to understand the tool
2. **Free mode works:** You don't need an API key for static analysis
3. **Check examples:** The UI has example contracts you can test
4. **Export reports:** Save JSON reports for later analysis
5. **Use Docker:** If tools are hard to install, Docker makes it easy
6. **Read remediations:** Each vulnerability includes fix suggestions

---

**Need help?** Check the documentation or open an issue on GitHub.
