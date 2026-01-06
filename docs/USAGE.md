# Usage Guide

## Quick Start

### Fastest Run (No LLM, No Tools)

```bash
# Start API
python fastapi_api.py

# In another terminal, start UI
streamlit run streamlit_ui.py
```

Open http://localhost:8501 and paste a contract!

### Full Run (With Slither/Mythril)

See [DOCKER.md](DOCKER.md) for Docker setup, or install tools locally.

## Using the Web UI

1. **Start the application** (see [INSTALL.md](INSTALL.md))
2. **Open browser** to http://localhost:8501
3. **Paste Solidity contract** in the text area
4. **Click "Analyze"**
5. **Review results**:
   - Risk score (0-100)
   - Severity level
   - Detailed vulnerabilities with line numbers
   - Code snippets and remediation suggestions
   - (Optional) AI audit summary

## Using the REST API

### Analyze a Contract

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "contract_code": "pragma solidity ^0.8.0;\n\ncontract Vault {\n    mapping(address => uint256) balances;\n    \n    function withdraw(uint256 amount) public {\n        require(balances[msg.sender] >= amount);\n        (bool success, ) = msg.sender.call{value: amount}(\"\");\n        require(success);\n        balances[msg.sender] -= amount;\n    }\n}",
    "contract_name": "Vault",
    "use_llm_audit": false
  }'
```

### Cross-Validate with External Tools

```bash
curl -X POST "http://localhost:8000/cross-validate" \
  -H "Content-Type: application/json" \
  -d '{
    "contract_code": "pragma solidity ^0.8.0; contract X { function f() public {} }",
    "contract_name": "X",
    "use_llm_audit": false,
    "run_slither": true,
    "run_mythril": true
  }'
```

### Upload a File

```bash
curl -X POST "http://localhost:8000/upload-and-analyze" \
  -F "file=@contract.sol"
```

## Example Contracts

### Vulnerable Contract (Reentrancy)

```solidity
pragma solidity ^0.8.0;

contract VulnerableVault {
    mapping(address => uint256) balances;
    
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        // REENTRANCY: External call before state update!
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] -= amount;  // State updated too late
    }
}
```

### Safe Contract

```solidity
pragma solidity ^0.8.0;

contract SafeToken {
    mapping(address => uint256) balances;
    address owner;
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }
    
    function transfer(address to, uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        require(to != address(0), "Invalid recipient");
        
        balances[msg.sender] -= amount;
        balances[to] += amount;
    }
}
```

## API Endpoints

- `GET /health` - Health check
- `POST /analyze` - Analyze contract
- `POST /cross-validate` - Analyze with external tools
- `POST /analyze-batch` - Analyze multiple contracts
- `POST /upload-and-analyze` - Upload and analyze file
- `GET /tools/status` - Check tool availability
- `GET /vulnerabilities` - Get vulnerability definitions
- `GET /docs` - Interactive API documentation

## Using Makefile

```bash
# Start API
make api

# Start UI
make ui

# Run tests
make test

# Install dependencies
make install
```

## Exporting Reports

### From Web UI

1. After analysis, scroll to "Export Results"
2. Click "Download JSON Report" or "Download Markdown Report"

### From API

Reports are included in the JSON response. Use `report_generator.py` to convert to HTML:

```python
from report_generator import generate_html_report

# After getting analysis result
html = generate_html_report(result_dict)
with open('report.html', 'w') as f:
    f.write(html)
```

## Next Steps

- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Docker**: See [DOCKER.md](DOCKER.md)
- **Contributing**: See [CONTRIBUTING.md](../CONTRIBUTING.md)
