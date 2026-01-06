# Security & Responsible Usage

**TL;DR:** This tool is for preliminary security assessment and education. Always conduct professional audits before deploying contracts to mainnet.

## Intended Use Cases

✅ **Suitable for:**
- Learning smart contract security
- Preliminary vulnerability screening
- CI/CD integration for early detection
- Research and development
- Educational demonstrations

❌ **NOT suitable for:**
- Final security validation before mainnet deployment
- Replacing professional security audits
- Legal compliance requirements
- High-value contract validation (without additional audits)

## Limitations

### Detection Limitations

**What the scanner CAN detect:**
- Common vulnerability patterns (reentrancy, access control, etc.)
- Syntax-level issues
- Well-known security anti-patterns

**What the scanner CANNOT detect:**
- Logic-level vulnerabilities without clear patterns
- Business logic flaws requiring domain knowledge
- Vulnerabilities in external contract dependencies
- Bytecode-level issues (source code only)
- Protocol-level attacks (flash loans, MEV, etc.)
- Gas optimization issues (beyond basic DoS patterns)
- Formal verification requirements

### Accuracy Limitations

**False Positive Rate:**
- Static analysis: ~15%
- LLM analysis: ~20%

**False Negative Rate:**
- Static analysis: ~10-15%
- LLM analysis: ~15-20%

**Why false positives occur:**
- Pattern matching may flag safe code that looks similar to vulnerable patterns
- Context-dependent vulnerabilities require human judgment
- Safe patterns may match vulnerability signatures

**Why false negatives occur:**
- Novel attack vectors not yet in pattern database
- Logic-level issues requiring deep understanding
- Complex multi-contract interactions
- Protocol-specific vulnerabilities

## When to Use Professional Audits

**Always use professional audits for:**
- Contracts handling >$100k in value
- Production mainnet deployments
- Regulatory compliance requirements
- High-profile projects
- Complex DeFi protocols
- Upgradeable contracts with admin functions

**Professional audit checklist:**
- [ ] Multiple analysis tools (Slither, Mythril, this scanner)
- [ ] Manual code review by security experts
- [ ] Formal verification (if applicable)
- [ ] Fuzzing and property-based testing
- [ ] Economic attack modeling
- [ ] Gas optimization review
- [ ] Upgrade mechanism review (if applicable)

## Best Practices

### 1. Use Multiple Tools

Never rely on a single scanner. Combine:
- This scanner (pattern + LLM)
- Slither (static analysis)
- Mythril (symbolic execution)
- Manual review
- Professional audit

**Example workflow:**
```bash
# 1. Run this scanner
curl -X POST "http://localhost:8000/analyze" ...

# 2. Run Slither
slither contract.sol

# 3. Run Mythril
mythril analyze contract.sol

# 4. Compare results and investigate discrepancies
```

### 2. Understand the Results

- **Review all findings manually** - Don't blindly trust automated results
- **Investigate false positives** - Learn why they occurred
- **Don't ignore warnings** - Even "low" severity issues can compound
- **Check context** - Some patterns are safe in specific contexts

**Example false positive:**
```solidity
// This might flag as "unchecked call" but is actually safe:
(bool success, bytes memory data) = target.call{value: amount}("");
require(success, "Call failed");  // Check is on next line
```

**Example false negative:**
```solidity
// This might not be detected if the pattern is novel:
function complexReentrancy() {
    // Multi-step reentrancy that doesn't match simple patterns
}
```

### 3. Validate Critical Functions

Pay special attention to:
- Functions handling funds (withdraw, transfer, etc.)
- Access control mechanisms
- Upgrade mechanisms
- External call patterns
- Randomness sources
- Time-dependent logic

**Critical function checklist:**
- [ ] Access control (onlyOwner, role-based, etc.)
- [ ] Reentrancy protection (Checks-Effects-Interactions)
- [ ] Input validation (bounds checking, zero checks)
- [ ] Event emission (for off-chain monitoring)
- [ ] Error handling (require/assert with messages)

### 4. Test Thoroughly

- Write comprehensive unit tests
- Use fuzzing tools (Echidna, Medusa)
- Test edge cases and boundary conditions
- Simulate attack scenarios
- Test with different Solidity compiler versions

**Recommended testing stack:**
- **Unit tests:** Hardhat/Foundry
- **Fuzzing:** Echidna, Medusa
- **Formal verification:** Certora, K framework
- **Integration tests:** Testnet deployments

### 5. Follow Security Standards

- [DASP TOP 10](https://dasp.org/)
- [Consensys Best Practices](https://consensys.io/research/smart-contract-best-practices/)
- [OpenZeppelin Security](https://docs.openzeppelin.com/contracts/)
- [Solidity Security Guidelines](https://docs.soliditylang.org/en/v0.8.0/security-considerations.html)

### 6. CI/CD Integration Best Practices

**Recommended CI workflow:**
```yaml
# Example GitHub Actions workflow
- name: Security Scan
  run: |
    # Run static analysis
    curl -X POST "${{ secrets.API_URL }}/analyze-sarif" \
      -H "Content-Type: application/json" \
      -d @contract.json > results.sarif
    
    # Upload SARIF for code scanning
    - uses: github/codeql-action/upload-sarif@v3
      with:
        sarif_file: results.sarif
```

**Best practices:**
- Run scans on every PR (fail on critical findings)
- Use SARIF output for GitHub Code Scanning
- Set appropriate thresholds (don't fail on low-severity)
- Cache results to avoid redundant scans
- Use rate limiting to prevent API abuse

**Rate limiting considerations:**
- Default: 60 requests/minute per IP
- For CI: Use API keys or dedicated IPs
- Batch analysis: Use `/analyze-batch` for multiple contracts
- Cache results: Same contract code returns cached result

## Tool Limitations by Component

### Static Analyzer

**Strengths:**
- Fast and deterministic
- No external dependencies
- Good for common patterns

**Weaknesses:**
- Pattern-based (not semantic)
- May miss logic-level issues
- False positive rate ~15%

### LLM Auditor

**Strengths:**
- Understands business logic
- Identifies logic-level vulnerabilities
- Provides remediation suggestions

**Weaknesses:**
- Requires API key and credits
- Non-deterministic (responses vary)
- False positive rate ~20%
- Dependent on API availability

### External Tools (Slither/Mythril)

**Strengths:**
- Industry-standard tools
- Comprehensive analysis
- Symbolic execution (Mythril)

**Weaknesses:**
- Slow execution (30-90s)
- May require local installation
- Can be complex to interpret

## Risk Assessment

**Risk Score Interpretation:**

| Score Range | Interpretation | Action |
|------------|----------------|--------|
| 0-20 | Low risk | Review findings, proceed with caution |
| 21-50 | Medium risk | Address high-severity issues, consider audit |
| 51-75 | High risk | Professional audit recommended |
| 76-100 | Critical risk | **Do not deploy** without comprehensive audit |

**Note:** Risk scores are approximate. Always review individual vulnerabilities, not just the score.

**How risk scores are calculated:**
- **Vulnerability weights:** CRITICAL=25, HIGH=15, MEDIUM=8, LOW=3, INFO=1
- **Code size factor:** Larger contracts increase risk potential
- **Formula:** `score = sum(vulnerability_weights) * (1 + size_factor)`, capped at 100

**Interpreting results:**
- **Score alone is insufficient** - Review individual vulnerabilities
- **One CRITICAL finding** can make a contract unsafe even with low total score
- **Multiple LOW findings** can compound into significant risk
- **Context matters** - Some vulnerabilities are acceptable in specific designs

**Example scenarios:**
- **Score: 15, 1 CRITICAL reentrancy** → **DO NOT DEPLOY** (critical issue present)
- **Score: 45, 3 HIGH access control** → **FIX BEFORE DEPLOY** (multiple high-severity issues)
- **Score: 30, 10 LOW missing events** → **Review and fix** (many low-severity issues)

## Interpreting Results

### Understanding Severity Levels

**CRITICAL:**
- Immediate security risk
- Can lead to fund loss or contract compromise
- Examples: Reentrancy, unchecked external calls
- **Action:** Fix immediately, do not deploy

**HIGH:**
- Significant security concern
- May lead to exploitation under certain conditions
- Examples: Access control issues, tx.origin misuse
- **Action:** Fix before deployment, consider audit

**MEDIUM:**
- Moderate risk, context-dependent
- May be acceptable in specific designs
- Examples: Gas DoS, timestamp dependency
- **Action:** Review and fix if applicable

**LOW:**
- Minor issues, best practices
- Usually don't pose immediate risk
- Examples: Missing events, code quality
- **Action:** Consider fixing for better practices

**INFO:**
- Informational findings
- Suggestions for improvement
- **Action:** Optional improvements

### Common False Positive Patterns

**Safe patterns that may be flagged:**
- **Unchecked calls with next-line checks:** Pattern may not detect multi-line error handling
- **Access control via inheritance:** May not detect modifiers from parent contracts
- **SafeMath in Solidity 0.8+:** May flag arithmetic that's actually safe
- **Intentional selfdestruct:** May flag legitimate contract destruction

**How to verify:**
1. Review the flagged code manually
2. Check if the pattern is actually vulnerable in your context
3. Test the specific scenario
4. Consult security best practices

## Reporting Issues

If you find:
- **False positives:** Open an issue with:
  - Contract code snippet
  - Explanation of why it's safe
  - Expected behavior
- **False negatives:** Open an issue with:
  - Vulnerable contract code
  - Expected vulnerability type
  - Why it should be detected
- **Performance issues:** See [benchmarks/README.md](benchmarks/README.md)
- **Security vulnerabilities in the scanner itself:** Email maintainer (do not open public issue)

## Legal Disclaimer

**This tool is provided "as is" without warranty of any kind.**

- No guarantee of vulnerability detection
- No guarantee of accuracy
- No liability for false negatives
- No liability for deployment decisions
- Use at your own risk

**Always:**
- Conduct professional security audits
- Use multiple analysis tools
- Review code manually
- Test thoroughly before deployment

## Resources

- [DASP TOP 10 Smart Contract Risks](https://dasp.org/)
- [Solidity Security Guidelines](https://docs.soliditylang.org/en/v0.8.0/security-considerations.html)
- [OpenZeppelin Security Best Practices](https://docs.openzeppelin.com/contracts/)
- [Ethereum Smart Contract Security](https://consensys.io/research/smart-contract-best-practices/)
- [Smart Contract Security Checklist](https://github.com/crytic/building-secure-contracts)

---

**Remember:** This tool is a starting point, not an endpoint. Security is a process, not a product.
