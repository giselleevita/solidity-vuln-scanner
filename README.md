# Solidity Vuln Scanner

**AI-powered vulnerability detection for Ethereum smart contracts using static analysis and LLM-based auditing.**

---

## 🚀 Quick Start

### Fastest Run (No LLM, No Tools)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start API (Terminal 1)
python fastapi_api.py

# 3. Start UI (Terminal 2)
streamlit run streamlit_ui.py

# 4. Open http://localhost:8501 and paste a contract!
```

**Test with this vulnerable contract:**
```solidity
pragma solidity ^0.8.0;

contract VulnerableVault {
    mapping(address => uint256) balances;
    
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] -= amount;
    }
}
```

### Full Run (With Slither/Mythril)

```bash
# Using Docker (recommended)
docker-compose up --build

# Or install tools locally
pip install slither-analyzer mythril
# Then run as above
```

See [docs/INSTALL.md](docs/INSTALL.md) for detailed setup.

---

## ✨ Features

- **Static Analysis**: Pattern-based detection of 15+ vulnerability types (reentrancy, unchecked calls, overflow/underflow, access control, etc.)
- **LLM Audit**: Optional AI-powered analysis using OpenAI GPT-4o or Claude
- **Risk Scoring**: Vulnerability severity rating (Critical, High, Medium, Low, Info)
- **Cross-Validation**: Integration with Slither and Mythril
- **REST API**: FastAPI backend for integration
- **Web UI**: Streamlit interface for easy contract analysis
- **Report Generation**: JSON, HTML, and Markdown reports

---

## 📖 Documentation

- **[How to Use](HOW_TO_USE.md)** - Complete step-by-step usage guide ⭐ **START HERE**
- **[Installation Guide](docs/INSTALL.md)** - Setup and prerequisites
- **[Usage Guide](docs/USAGE.md)** - API examples and workflows
- **[Docker Guide](docs/DOCKER.md)** - Containerized deployment
- **[Architecture](docs/ARCHITECTURE.md)** - System design and performance characteristics
- **[Security & Limitations](SECURITY.md)** - Responsible usage guidelines

---

## 🛠️ Installation

### Prerequisites

- Python 3.10+ (3.11 recommended)
- Git
- (Optional) OpenAI API key or Claude API key for AI features
- (Optional) Docker Desktop for containerized deployment

### Quick Install

```bash
# Clone repository
git clone https://github.com/yourusername/solidity-vuln-scanner.git
cd solidity-vuln-scanner

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure (optional)
cp .env.example .env
# Edit .env to set USE_LLM=false for free mode, or add LLM_API_KEY for AI features
```

See [docs/INSTALL.md](docs/INSTALL.md) for detailed instructions.

---

## 🎯 Usage

### Web UI

1. Start the application (see Quick Start above)
2. Open http://localhost:8501
3. Paste Solidity contract code
4. Click "Analyze"
5. Review vulnerabilities, risk score, and recommendations

### REST API

```bash
# Analyze a contract (static analysis only)
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "contract_code": "pragma solidity ^0.8.0; contract X { function f() public {} }",
    "contract_name": "X",
    "use_llm_audit": false
  }'

# Analyze with SARIF output (for CI/CD)
curl -X POST "http://localhost:8000/analyze-sarif" \
  -H "Content-Type: application/json" \
  -d '{
    "contract_code": "pragma solidity ^0.8.0; contract X { function f() public {} }",
    "contract_name": "X",
    "use_llm_audit": false
  }'

# Cross-validate with external tools
curl -X POST "http://localhost:8000/cross-validate" \
  -H "Content-Type: application/json" \
  -d '{
    "contract_code": "pragma solidity ^0.8.0; contract X { function f() public {} }",
    "contract_name": "X",
    "run_slither": true,
    "run_mythril": true
  }'

# Batch analysis (multiple contracts)
curl -X POST "http://localhost:8000/analyze-batch" \
  -H "Content-Type: application/json" \
  -d '[
    {"contract_code": "...", "contract_name": "Contract1"},
    {"contract_code": "...", "contract_name": "Contract2"}
  ]'
```

**API Documentation:** Interactive docs available at `http://localhost:8000/docs` (Swagger UI)

See [docs/USAGE.md](docs/USAGE.md) for more examples and workflows.

---

## 🧪 Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Run specific test suite
pytest tests/test_static_analyzer.py -v
pytest tests/test_fastapi_cross_validate.py -v
```

## 📊 Performance Benchmarks

Performance benchmarks track static analysis speed across contract sizes and detect regressions. See [benchmarks/README.md](benchmarks/README.md) for full documentation.

**Quick run:**
```bash
pytest benchmarks/test_performance.py -v
```

**CI:** Benchmarks run on main branch merges with results uploaded as artifacts. See [docs/CI_ARTIFACTS.md](docs/CI_ARTIFACTS.md) for accessing results.

---

## 📊 What Gets Detected?

The scanner detects **15 vulnerability types** using pattern-based analysis:

| Vulnerability | Severity | Description |
|--------------|----------|-------------|
| **Reentrancy** | Critical | External call before state update |
| **Unchecked Call** | High | Low-level call without error handling |
| **Overflow/Underflow** | High | Integer arithmetic without SafeMath |
| **Access Control** | High | Missing authorization checks |
| **Bad Randomness** | Medium | Predictable randomness sources |
| **tx.origin Misuse** | High | Authorization via tx.origin |
| **Delegatecall Risk** | High | Unsafe delegatecall patterns |
| **Gas DoS** | Medium | Unbounded loops |
| **Timestamp Dependency** | Low | Unreliable timing |
| **Selfdestruct** | Medium | Contract destruction capability |
| **Missing Events** | Low | State changes without event emission |
| **Front-Running** | Medium | Transaction ordering vulnerabilities |
| **Logic Error** | Medium | Common logic mistakes |
| **Centralization Risk** | Medium | Single point of control |
| **Missing Input Validation** | High | Unvalidated function parameters |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed detection methods and limitations.

---

## 🐳 Docker

```bash
# Start everything (API + UI + Tools)
docker-compose up --build

# Access
# - UI: http://localhost:8501
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

See [docs/DOCKER.md](docs/DOCKER.md) for detailed Docker guide and troubleshooting.

---

## ⚙️ Configuration

Edit `.env`:

```env
# LLM Settings (optional - can run in free mode)
USE_LLM=false                    # Set to true for AI features
LLM_PROVIDER=openai              # or "anthropic"
LLM_API_KEY=sk-...               # Your API key
LLM_MODEL=gpt-4o-mini            # Model name

# API Settings
API_PORT=8000
API_HOST=0.0.0.0
DEBUG=False
```

---

## 🚨 Security & Disclaimer

**This tool is for educational and research purposes.** It is **NOT a substitute** for professional security audits.

See [SECURITY.md](SECURITY.md) for detailed limitations, responsible usage guidelines, and when to use professional audits.

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| Avg. analysis time (100 LoC) | ~1-2 seconds |
| Max contract size | 10,000 LoC |
| False positive rate (static) | ~15% |
| False positive rate (LLM) | ~20% |
| API rate limit | 60 req/min (configurable) |

See [benchmarks/README.md](benchmarks/README.md) for detailed performance metrics and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for scalability characteristics.

---

## 🤝 Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📜 License

MIT License – see [LICENSE](LICENSE) file.

---

## 🔗 Resources

- [DASP TOP 10 Smart Contract Risks](https://dasp.org/)
- [Solidity Security Guidelines](https://docs.soliditylang.org/en/v0.8.0/security-considerations.html)
- [OpenZeppelin Security Best Practices](https://docs.openzeppelin.com/contracts/)
- [Ethereum Smart Contract Security](https://consensys.io/research/smart-contract-best-practices/)

---

**Last updated**: December 2025
