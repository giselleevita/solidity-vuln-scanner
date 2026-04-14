# Architecture Overview

**TL;DR:** Three-layer analysis approach (static patterns → optional LLM → optional external tools) with FastAPI backend, Streamlit UI, and performance benchmarks. Static analysis is deterministic and O(n) over source size.

## High-Level Design

The scanner uses a **three-layer analysis approach**:

1. **Static Analysis** - Pattern-based vulnerability detection (always enabled)
2. **LLM Audit** - Semantic understanding via AI (optional, requires API key)
3. **External Tools** - Cross-validation with Slither/Mythril (optional)

Each layer operates independently and can be enabled/disabled based on requirements.

## Component Architecture

### Core Analysis Engine

#### Static Analyzer (`static_analyzer.py`)

- **Purpose:** Fast, deterministic pattern matching
- **Method:** Regex-based detection across 15+ vulnerability types
- **Performance:** O(n) complexity over lines of code
- **Dependencies:** None (pure Python)
- **Deterministic:** Yes - same input always produces same output

**Key characteristics:**
- Pattern-based detection (not full AST parsing)
- Fast execution (< 3s for contracts up to 6k LoC)
- No external API calls
- Suitable for CI/CD integration

#### LLM Auditor (`llm_auditor.py`)

- **Purpose:** Semantic understanding and logic-level vulnerability detection
- **Method:** API calls to OpenAI GPT-4o or Claude
- **Performance:** Variable (2-5s depending on API latency)
- **Dependencies:** OpenAI or Anthropic API key
- **Deterministic:** No - LLM responses may vary

**Key characteristics:**
- Understands business logic context
- Identifies vulnerabilities missed by pattern matching
- Provides remediation suggestions
- Maps findings to security frameworks

### API Layer

#### FastAPI Server (`fastapi_api.py`)

- **Framework:** FastAPI (async-capable)
- **Endpoints:**
  - `POST /analyze` - Single contract analysis
  - `POST /analyze-sarif` - Analysis with SARIF output
  - `POST /analyze-batch` - Batch analysis (multiple contracts)
  - `POST /upload-and-analyze` - File upload endpoint
  - `POST /cross-validate` - Analysis with external tools
  - `GET /health` - Health check
  - `GET /vulnerabilities` - List all detectable vulnerability types
- **Middleware:**
  - Rate limiting (60 req/min per IP)
  - CORS (allows cross-origin requests)
  - Caching (1-hour TTL for static analysis results)
- **Response formats:** JSON, HTML (via report generator), SARIF, Markdown

**Request flow:**
```
Request → Rate Limiter → Cache Check → Analysis → Response
         ↓ (if rate limited)
         HTTP 429 Too Many Requests
         
         ↓ (if cached)
         Return cached result
         
         ↓ (if new)
         Execute analysis → Cache result → Return
```

### UI Layer

#### Streamlit Interface (`streamlit_ui.py`)

- **Framework:** Streamlit
- **Features:**
  - Contract code input (text area or file upload)
  - Visual vulnerability display with severity badges
  - Report export (JSON, Markdown)
  - Example contracts for testing
- **Backend:** Calls FastAPI endpoints

### Tool Integration

#### External Tools (`tools_integration.py`)

- **Slither:** Static analysis tool (optional)
- **Mythril:** Symbolic execution tool (optional)
- **Auto-detection:** Checks for local installation or Docker availability
- **Execution:** Runs in containers or locally via subprocess

**Why optional:**
- External tools add significant runtime (30-90s)
- Not required for core functionality
- Useful for cross-validation only

### Middleware

#### Request Handling (`middleware.py`)

- **Rate Limiter:** Prevents abuse (60 req/min per IP)
- **Analysis Cache:** Reduces redundant analysis (1-hour TTL)
- **In-memory storage:** No database required

**Cache strategy:**
- Key: MD5 hash of contract code + name
- TTL: 1 hour
- Max size: 100 entries (LRU eviction)
- Scope: Static analysis only (LLM results not cached)

### Configuration

#### App Config (`app_config.py`)

- **Method:** Environment variables via `.env`
- **Settings:**
  - LLM provider and API key
  - API host/port
  - File size limits
  - Timeout values
- **Default mode:** Free (static-only, no API key required)

## Data Flow

### Standard Analysis Flow

```
User Input (Solidity Code)
    ↓
FastAPI Endpoint (/analyze)
    ↓
[Rate Limiting] → [Cache Check] → [Analysis]
    ├─ If rate limited: HTTP 429
    ├─ If cached: Return cached result
    └─ If new: Continue
    ↓
Static Analyzer (Pattern Matching)
    ├─ Remove comments
    ├─ Pattern matching (15 vulnerability types)
    ├─ Calculate risk score (0-100)
    └─ Returns deterministic results
    ↓
[Optional] LLM Auditor (Semantic Analysis)
    ├─ API call to OpenAI/Claude
    ├─ Business logic understanding
    ├─ Logic-level vulnerability detection
    └─ Remediation suggestions
    ↓
[Optional] Slither/Mythril (Cross-Validation)
    ├─ Docker container execution
    ├─ External tool analysis
    └─ Result comparison
    ↓
Result Aggregation
    ├─ Combine findings from all layers
    ├─ Deduplicate vulnerabilities
    ├─ Calculate overall severity
    └─ Generate reports
    ↓
Response Formatting
    ├─ JSON (default)
    ├─ HTML (via report_generator)
    ├─ Markdown (via report_generator)
    └─ SARIF (for CI/CD integration)
    ↓
Response (with caching)
```

### Batch Analysis Flow

```
Multiple Contracts (JSON array)
    ↓
POST /analyze-batch
    ↓
For each contract:
    ├─ Rate limit check
    ├─ Cache check
    ├─ Static analysis
    ├─ [Optional] LLM audit
    └─ Result aggregation
    ↓
Return array of results
```

### Error Handling

- **Invalid input:** HTTP 400 with error message
- **Rate limit exceeded:** HTTP 429 with retry-after header
- **LLM API failure:** Falls back to static-only results
- **External tool failure:** Continues without tool results
- **Timeout:** HTTP 504 after configured timeout

## Vulnerability Detection

### Static Pattern Detection

The scanner detects **15 vulnerability types** using regex patterns:

| Vulnerability | Detection Method | Severity | Pattern Focus |
|--------------|------------------|----------|---------------|
| Reentrancy | External call before state update | Critical | `call()`/`send()` before balance update |
| Unchecked Call | Low-level call without error handling | High | `call()`/`delegatecall()` without `require` |
| Overflow/Underflow | Arithmetic without SafeMath/checks | High | Math operations without SafeMath/checked |
| Access Control | Public functions without modifiers | High | Sensitive functions (`transfer`, `mint`, etc.) |
| Bad Randomness | Predictable randomness sources | Medium | `blockhash`/`block.timestamp` for randomness |
| tx.origin Misuse | Authorization via tx.origin | High | `tx.origin` in authorization checks |
| Delegatecall Risk | Unsafe delegatecall patterns | High | Dynamic `delegatecall` without validation |
| Gas DoS | Unbounded loops | Medium | Loops over unbounded arrays/mappings |
| Timestamp Dependency | Unreliable timing | Low | `block.timestamp` in critical logic |
| Selfdestruct | Contract destruction capability | Medium | `selfdestruct()` usage |
| Missing Events | State changes without events | Low | Critical functions without `emit` |
| Front-Running | Transaction ordering vulnerabilities | Medium | Detectable via pattern analysis |
| Logic Error | Common logic mistakes | Medium | Pattern-based logic flaw detection |
| Centralization Risk | Single point of control | Medium | Admin-only functions without safeguards |
| Missing Input Validation | Unvalidated function parameters | High | Functions without input checks |

**Detection approach:**
- Regex pattern matching on source code
- Line-by-line analysis with context
- Pattern combinations for complex vulnerabilities
- No AST parsing (faster but less precise)

**Limitations:**
- Pattern-based (not full semantic analysis)
- May produce false positives (~15%)
- May miss logic-level vulnerabilities
- No bytecode analysis
- Cannot analyze multi-file contracts as a unit

### LLM Analysis

The LLM auditor provides:
- **Business logic understanding** - Context-aware analysis
- **Logic-level vulnerabilities** - Issues missed by patterns
- **Remediation strategies** - Actionable recommendations
- **Framework mapping** - OWASP, DASP TOP 10 alignment

**Limitations:**
- Requires API key and credits
- Non-deterministic (responses may vary)
- False positive rate ~20%
- Dependent on API availability

## Risk Scoring Algorithm

Risk score (0-100) calculated from:

1. **Vulnerability weights:**
   - CRITICAL: 25 points
   - HIGH: 15 points
   - MEDIUM: 8 points
   - LOW: 3 points
   - INFO: 1 point

2. **Code size factor:**
   - Larger contracts = higher risk potential
   - Factor: `min(LoC / 100, 5) * 0.1`

3. **Overall severity:**
   - Worst severity present determines overall level
   - SAFE if no vulnerabilities found

**Formula:**
```
score = sum(vulnerability_weights) * (1 + size_factor)
score = min(score, 100)  # Cap at 100
```

## Performance Characteristics

### Static Analysis

- **Complexity:** O(n) over lines of code
- **Typical times:**
  - Small (50-150 LoC): < 0.5s
  - Medium (300-1200 LoC): < 1.5s
  - Large (2k-6k LoC): < 3s
  - XLarge (10k+ LoC): < 10s

**Benchmarks:** See [benchmarks/README.md](../benchmarks/README.md) for detailed performance metrics and regression tracking.

### LLM Analysis

- **Complexity:** O(1) API call (processing done remotely)
- **Typical time:** 2-5 seconds (depends on API latency)
- **Variable factors:** Network latency, API rate limits, model load

### External Tools

- **Slither:** 30-60 seconds
- **Mythril:** 60-90 seconds
- **Not included in benchmarks** (too variable, external dependency)

## Deployment Options

### 1. Local Development

- **Setup:** Direct Python execution
- **Pros:** Fast iteration, easy debugging
- **Cons:** Requires local dependencies
- **Use case:** Development, testing

### 2. Docker

- **Setup:** Containerized services
- **Pros:** Consistent environment, no local tool installation
- **Cons:** Slower startup, Docker overhead
- **Use case:** Production, CI/CD

### 3. CI/CD Integration

- **Setup:** GitHub Actions workflow
- **Features:**
  - Automated scanning on commits
  - SARIF output for code scanning
  - Performance benchmarks
  - Coverage reporting
- **Use case:** Continuous security validation

## Scalability Considerations

### Current Limits

- **Max contract size:** 10,000 LoC (configurable)
- **Rate limit:** 60 requests/minute per IP
- **Cache size:** 100 entries
- **Concurrent requests:** Limited by FastAPI/uvicorn workers

### Scaling Strategies

- **Horizontal scaling:** Multiple API instances behind load balancer
- **Database caching:** Replace in-memory cache with Redis/PostgreSQL
- **Queue system:** Use Celery for long-running analyses
- **CDN:** Serve static UI assets via CDN

## Report Generation

### Report Formats

#### JSON Report (`report_generator.py`)
- **Format:** Structured JSON with all analysis data
- **Use case:** API responses, programmatic processing
- **Contents:** Vulnerabilities, risk score, metadata, code snippets

#### HTML Report
- **Format:** Styled HTML document
- **Use case:** Human-readable reports, sharing
- **Features:** Color-coded severity, code highlighting, printable format

#### Markdown Report
- **Format:** Markdown text
- **Use case:** Documentation, version control, plain text viewing
- **Features:** Structured sections, code blocks

#### SARIF Report
- **Format:** SARIF 2.1.0 standard
- **Use case:** CI/CD integration, GitHub Code Scanning
- **Features:** 
  - Rule definitions for each vulnerability type
  - Result locations with line numbers
  - Severity mapping
  - Tool metadata
- **Integration:** Uploaded to GitHub Actions for code scanning alerts

## Security Considerations

### Input Security
- **Input validation:** Contract code size limits (10k LoC default), sanitization
- **No code execution:** Static analysis only (no `eval()`/`exec()`)
- **File upload limits:** Max file size enforced (1MB default)
- **Timeout protection:** Analysis timeout prevents resource exhaustion

### API Security
- **Rate limiting:** 60 req/min per IP (prevents abuse and DoS)
- **CORS:** Configurable origins (default: allow all for development)
- **API key security:** Stored in environment variables, never committed
- **No authentication:** Public API (add auth layer for production)

### Data Security
- **No persistent storage:** Results cached in-memory only (1 hour TTL)
- **No logging of contract code:** Only metadata logged
- **Cache eviction:** LRU eviction prevents memory leaks

## Next Steps

- **Usage**: See [USAGE.md](USAGE.md)
- **Installation**: See [INSTALL.md](INSTALL.md)
- **Docker**: See [DOCKER.md](DOCKER.md)
- **Performance**: See [benchmarks/README.md](../benchmarks/README.md)
- **Security**: See [SECURITY.md](../SECURITY.md)
