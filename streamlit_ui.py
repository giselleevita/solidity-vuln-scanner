"""
Streamlit Web UI for Solidity Vuln Scanner
Professional, user-friendly interface for contract analysis
"""

import os
import streamlit as st
import requests
import json
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="Solidity Vuln Scanner",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional styling
st.markdown("""
<style>
    /* Main container */
    .main {
        padding: 2rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9);
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }
    
    /* Vulnerability cards */
    .vulnerability-card {
        border-left: 4px solid;
        padding: 1.2rem;
        margin: 1rem 0;
        border-radius: 8px;
        background: #f8f9fa;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    
    .vulnerability-card:hover {
        transform: translateX(4px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .critical { 
        border-left-color: #d32f2f; 
        background: #ffebee;
    }
    .high { 
        border-left-color: #f57c00; 
        background: #fff3e0;
    }
    .medium { 
        border-left-color: #fbc02d; 
        background: #fffde7;
    }
    .low { 
        border-left-color: #388e3c; 
        background: #e8f5e9;
    }
    .info { 
        border-left-color: #1976d2; 
        background: #e3f2fd;
    }
    
    /* Metrics styling */
    .metric-container {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .status-safe { background: #4caf50; color: white; }
    .status-low { background: #8bc34a; color: white; }
    .status-medium { background: #ffc107; color: #000; }
    .status-high { background: #ff9800; color: white; }
    .status-critical { background: #f44336; color: white; }
    
    /* Code blocks */
    .code-block {
        background: #263238;
        color: #aed581;
        padding: 1rem;
        border-radius: 6px;
        font-family: 'Courier New', monospace;
        overflow-x: auto;
    }
    
    /* Tool status */
    .tool-status {
        padding: 0.75rem;
        border-radius: 6px;
        margin: 0.5rem 0;
    }
    
    .tool-installed {
        background: #e8f5e9;
        border-left: 3px solid #4caf50;
    }
    
    .tool-not-installed {
        background: #fff3e0;
        border-left: 3px solid #ff9800;
    }
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# API configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
USE_LLM_FEATURE = os.getenv("USE_LLM", "false").lower() == "true"

def check_api_health():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except:
        return False, None

def get_tools_status():
    """Get status of external tools"""
    try:
        response = requests.get(f"{API_URL}/tools/status", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def analyze_contract(code: str, name: str, use_llm: bool = False):
    """Call API to analyze contract"""
    try:
        response = requests.post(
            f"{API_URL}/analyze",
            json={
                "contract_code": code,
                "contract_name": name,
                "use_llm_audit": use_llm
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {str(e)}\n\nMake sure the API server is running on {API_URL}")
        return None

def format_severity_badge(severity: str) -> str:
    """Format severity as styled badge"""
    colors = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🟢",
        "INFO": "🔵",
        "SAFE": "✅"
    }
    return f"{colors.get(severity, '❓')} **{severity}**"

def get_severity_class(severity: str) -> str:
    """Get CSS class for severity"""
    severity_lower = severity.lower()
    if severity_lower == "critical":
        return "status-critical"
    elif severity_lower == "high":
        return "status-high"
    elif severity_lower == "medium":
        return "status-medium"
    elif severity_lower == "low":
        return "status-low"
    else:
        return "status-safe"

def render_vulnerability(vuln: dict):
    """Render single vulnerability with professional styling"""
    severity = vuln.get("severity", "UNKNOWN")
    color_class = severity.lower()
    
    with st.container():
        st.markdown(f"""
        <div class="vulnerability-card {color_class}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <strong style="font-size: 1.1rem;">{vuln.get('type', 'Unknown').upper().replace('_', ' ')}</strong>
                <span class="status-badge {get_severity_class(severity)}">{severity}</span>
            </div>
            <small style="color: #666;">Line {vuln.get('line', '?')}</small>
        </div>
        """, unsafe_allow_html=True)
        
        st.write(f"**Description:** {vuln.get('description', 'N/A')}")
        
        with st.expander("📝 Code Context", expanded=False):
            st.code(vuln.get('code_snippet', 'N/A'), language="solidity")
        
        with st.expander("🔧 Remediation", expanded=False):
            st.info(vuln.get('remediation', 'N/A'))

# Header
st.markdown("""
<div class="main-header">
    <h1>🔐 Solidity Vuln Scanner</h1>
    <p>AI-powered vulnerability detection for Ethereum smart contracts</p>
</div>
""", unsafe_allow_html=True)

# API health check
api_healthy, health_data = check_api_health()
if not api_healthy:
    st.error(f"""
    ⚠️ **API Server Not Running**
    
    Please start the API server first:
    ```bash
    python fastapi_api.py
    ```
    
    The API should run on {API_URL}
    """)
    st.stop()

# Show API status
col1, col2, col3 = st.columns(3)
with col1:
    st.success("✅ API Connected")
with col2:
    if health_data:
        llm_status = "Enabled" if health_data.get("llm_enabled") else "Disabled (Free Mode)"
        st.info(f"🤖 LLM: {llm_status}")
with col3:
    tools_status = get_tools_status()
    if tools_status:
        slither_ok = tools_status.get("slither", {}).get("installed", False)
        mythril_ok = tools_status.get("mythril", {}).get("installed", False)
        tools_count = sum([slither_ok, mythril_ok])
        st.info(f"🔧 External Tools: {tools_count}/2")

st.divider()

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Analyze",
    "🔀 Cross-Validate",
    "📚 Documentation",
    "🎯 Examples",
    "ℹ️ About"
])

# Tab 1: Analysis
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📝 Enter Smart Contract Code")
        
        # Pre-fill with example code if loaded
        default_code = ""
        if "example_code" in st.session_state:
            default_code = st.session_state.example_code
            del st.session_state.example_code
        
        contract_code = st.text_area(
            "Solidity Code",
            height=350,
            value=default_code,
            placeholder="""pragma solidity ^0.8.0;

contract Example {
    // Paste your contract code here
}""",
            key="contract_input",
            help="Paste your Solidity smart contract code above"
        )
        
        contract_name = st.text_input(
            "Contract Name",
            value="MyContract",
            placeholder="e.g., Vault, Token, etc.",
            help="Optional: Name your contract for easier identification"
        )
    
    with col2:
        st.subheader("⚙️ Analysis Options")
        
        st.markdown("""
        <div class="tool-status tool-installed">
            <strong>✅ Static Analysis</strong><br>
            <small>Always enabled - detects 15+ vulnerability patterns</small>
        </div>
        """, unsafe_allow_html=True)
        
        use_llm = st.checkbox(
            "🤖 Enable AI Audit",
            value=False,
            disabled=not USE_LLM_FEATURE,
            help="Use AI for deeper analysis (requires API key)" if USE_LLM_FEATURE else "AI features disabled - running in free mode"
        )
        
        if not USE_LLM_FEATURE:
            st.caption("💡 Free mode: Static analysis only (no API costs)")
        
        st.divider()
        
        if st.button("🔍 Analyze Contract", type="primary", use_container_width=True):
            if not contract_code.strip():
                st.error("⚠️ Please enter contract code")
            else:
                with st.spinner("🔍 Analyzing contract... This may take a few seconds."):
                    result = analyze_contract(contract_code, contract_name, use_llm)
                    
                    if result:
                        st.session_state.last_result = result
                        st.rerun()
    
    # Display results
    if "last_result" in st.session_state:
        result = st.session_state.last_result
        
        st.divider()
        st.subheader("📊 Analysis Results")
        
        # Summary metrics with professional styling
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Risk Score", f"{result['risk_score']:.1f}", "out of 100")
        
        with col2:
            severity = result['severity']
            st.markdown(f"""
            <div class="metric-container">
                <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">Severity</div>
                <div style="font-size: 1.5rem; font-weight: bold;">
                    <span class="status-badge {get_severity_class(severity)}">{severity}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            vuln_count = len(result['vulnerabilities'])
            st.metric("Vulnerabilities", vuln_count, "found" if vuln_count > 0 else "none")
        
        with col4:
            st.metric("Lines of Code", result['lines_of_code'])
        
        # Vulnerabilities section
        if result['vulnerabilities']:
            st.divider()
            st.subheader("🚨 Vulnerabilities Detected")
            
            # Group by severity
            severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
            grouped = {}
            for vuln in result['vulnerabilities']:
                sev = vuln.get('severity', 'INFO')
                if sev not in grouped:
                    grouped[sev] = []
                grouped[sev].append(vuln)
            
            for severity in severity_order:
                if severity in grouped:
                    st.markdown(f"### {format_severity_badge(severity)} ({len(grouped[severity])} found)")
                    for vuln in grouped[severity]:
                        render_vulnerability(vuln)
        else:
            st.success("""
            ✅ **No vulnerabilities detected!**
            
            This contract appears to be secure based on static analysis patterns.
            However, always conduct professional audits before deploying to mainnet.
            """)
        
        # LLM Audit Results
        if USE_LLM_FEATURE and "llm_audit" in result and result["llm_audit"]:
            st.divider()
            st.subheader("🤖 AI Security Audit")
            
            llm = result["llm_audit"]
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Risk Assessment:** {llm.get('risk_assessment', 'N/A')}")
            with col2:
                st.write(f"**Tokens Used:** {llm.get('tokens_used', 'N/A')}")
            
            st.write(f"**Summary:** {llm.get('summary', 'N/A')}")
            
            if llm.get("recommendations"):
                st.write("**💡 Recommendations:**")
                for i, rec in enumerate(llm["recommendations"], 1):
                    st.write(f"{i}. {rec}")
            
            if llm.get("best_practices"):
                st.write("**✨ Best Practices:**")
                for i, practice in enumerate(llm["best_practices"], 1):
                    st.write(f"{i}. {practice}")
        
        # Export results
        st.divider()
        st.subheader("📥 Export Results")
        
        col1, col2 = st.columns(2)
        with col1:
            json_str = json.dumps(result, indent=2)
            st.download_button(
                "📄 Download JSON Report",
                json_str,
                file_name=f"{result['contract_name']}_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        with col2:
            # Generate markdown report
            md_report = f"""# Security Audit Report: {result['contract_name']}

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Risk Score:** {result['risk_score']}/100
**Severity:** {result['severity']}
**Vulnerabilities Found:** {len(result['vulnerabilities'])}

## Vulnerabilities

"""
            for vuln in result['vulnerabilities']:
                md_report += f"""### {vuln.get('type', 'Unknown').upper()} - {vuln.get('severity', 'UNKNOWN')}
- **Line:** {vuln.get('line', '?')}
- **Description:** {vuln.get('description', 'N/A')}
- **Remediation:** {vuln.get('remediation', 'N/A')}

"""
            
            st.download_button(
                "📝 Download Markdown Report",
                md_report,
                file_name=f"{result['contract_name']}_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            )

# Tab 2: Cross-Validate
with tab4:
    st.subheader("🔀 Cross-Validate with External Tools")
    st.write("Run Slither and Mythril alongside our static analyzer for comprehensive security analysis.")
    
    # Show tool status
    tools_status = get_tools_status()
    if tools_status:
        col1, col2 = st.columns(2)
        with col1:
            slither_info = tools_status.get("slither", {})
            if slither_info.get("installed"):
                st.success(f"✅ {slither_info.get('message', 'Slither installed')}")
            else:
                st.warning(f"⚠️ {slither_info.get('message', 'Slither not installed')}")
        
        with col2:
            mythril_info = tools_status.get("mythril", {})
            if mythril_info.get("installed"):
                st.success(f"✅ {mythril_info.get('message', 'Mythril installed')}")
            else:
                st.warning(f"⚠️ {mythril_info.get('message', 'Mythril not installed')}")
    
    st.divider()
    
    with st.form("cross_validate_form"):
        code = st.text_area(
            "Solidity Code",
            height=300,
            placeholder="pragma solidity ^0.8.0; contract X { function f() public {} }",
            key="cv_code",
        )
        name = st.text_input("Contract Name", value="Contract", key="cv_name")
        
        col1, col2 = st.columns(2)
        with col1:
            run_slither = st.checkbox("Run Slither", value=False, help="Requires Slither to be installed")
        with col2:
            run_mythril = st.checkbox("Run Mythril", value=False, help="Requires Mythril to be installed")
        
        use_llm_cv = st.checkbox(
            "Include LLM Audit",
            value=False,
            disabled=not USE_LLM_FEATURE,
            help="Requires LLM API key"
        )
        
        submitted = st.form_submit_button("🚀 Run Cross-Validation", type="primary", use_container_width=True)

    if submitted:
        if not code.strip():
            st.error("⚠️ Please paste Solidity code.")
        else:
            with st.spinner("🔄 Running cross-validation... This may take 1-2 minutes."):
                try:
                    resp = requests.post(
                        f"{API_URL}/cross-validate",
                        json={
                            "contract_code": code,
                            "contract_name": name,
                            "run_slither": run_slither,
                            "run_mythril": run_mythril,
                            "use_llm_audit": use_llm_cv,
                        },
                        timeout=120,
                    )
                    if resp.status_code != 200:
                        st.error(f"❌ API error: {resp.status_code} - {resp.text}")
                    else:
                        data = resp.json()
                        st.success("✅ Cross-validation complete!")
                        
                        # Static/LLM Analysis
                        st.subheader("📊 Static/LLM Analysis")
                        st.json(data.get("analysis", {}))
                        
                        # Slither Results
                        if data.get("slither") is not None:
                            st.subheader("🔍 Slither Results")
                            slither_data = data["slither"]
                            if slither_data.get("success"):
                                st.success("✅ Slither analysis completed")
                                st.code(slither_data.get("output", ""), language="text")
                            else:
                                st.warning(f"⚠️ Slither: {slither_data.get('output', 'Failed')}")
                        else:
                            st.caption("ℹ️ Slither not run")
                        
                        # Mythril Results
                        if data.get("mythril") is not None:
                            st.subheader("🔍 Mythril Results")
                            mythril_data = data["mythril"]
                            if mythril_data.get("success"):
                                st.success("✅ Mythril analysis completed")
                                st.code(mythril_data.get("output", ""), language="text")
                            else:
                                st.warning(f"⚠️ Mythril: {mythril_data.get('output', 'Failed')}")
                        else:
                            st.caption("ℹ️ Mythril not run")
                        
                except requests.exceptions.Timeout:
                    st.error("⏱️ Request timed out. Try with a smaller contract or increase timeout.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# Tab 3: Documentation
with tab2:
    st.subheader("📚 Documentation & Guide")
    
    st.markdown("""
    ### 🚀 Getting Started
    
    1. **Paste your Solidity contract** in the "Analyze" tab
    2. **Enter a contract name** (optional)
    3. **Click "Analyze"** to scan for vulnerabilities
    4. **Review results** including risk score, severity, and detailed findings
    
    ### 🔍 What Gets Detected?
    
    Our scanner detects **15+ vulnerability types**:
    
    - **🔴 Reentrancy** - External calls before state updates
    - **🟠 Access Control** - Missing authorization checks  
    - **🟠 Unchecked Calls** - External calls without error handling
    - **🟠 Integer Overflow/Underflow** - Unchecked arithmetic
    - **🟡 Bad Randomness** - Predictable randomness sources
    - **🟠 tx.origin Misuse** - Authorization via tx.origin
    - **🟠 Delegatecall Issues** - Unsafe delegatecall patterns
    - **🟡 Gas DoS** - Unbounded loops
    - **🟢 Timestamp Dependency** - Unreliable timing
    - And more...
    
    ### 💡 Features
    
    ✅ **Static Analysis** - Pattern-based vulnerability detection (FREE)  
    ✅ **AI Audit** - LLM-powered security analysis (optional)  
    ✅ **Risk Scoring** - Quantified risk assessment (0-100)  
    ✅ **JSON Export** - Integration with other tools  
    ✅ **Cross-Validation** - Compare with Slither/Mythril  
    
    ### ⚠️ Important Notes
    
    - This tool is for **research and education**
    - Always have contracts audited by **professional auditors**
    - May produce **false positives/negatives**
    - Not a substitute for **formal verification**
    - Use multiple analysis tools for best results
    
    ### 🔧 Installing External Tools
    
    **Slither:**
    ```bash
    pip install slither-analyzer
    ```
    
    **Mythril:**
    ```bash
    pip install mythril
    # OR on macOS:
    brew install mythril
    ```
    """)

# Tab 4: Examples
with tab3:
    st.subheader("🎯 Example Contracts")
    st.write("Try these example contracts to see the scanner in action:")
    
    examples = {
        "Vulnerable Vault (Reentrancy)": '''pragma solidity ^0.8.0;

contract VulnerableVault {
    mapping(address => uint256) balances;
    
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        // REENTRANCY: External call before state update!
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] -= amount;  // State updated too late
    }
    
    function transfer(address to, uint256 amount) public {
        // ACCESS CONTROL: No checks at all!
        balances[to] += amount;
    }
}''',
        
        "Safe Token (Secure)": '''pragma solidity ^0.8.0;

contract SafeToken {
    mapping(address => uint256) balances;
    address owner;
    
    event Transfer(address indexed from, address indexed to, uint256 amount);
    
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
        
        emit Transfer(msg.sender, to, amount);
    }
}'''
    }
    
    selected = st.selectbox("Select Example:", list(examples.keys()))
    
    st.code(examples[selected], language="solidity")
    
    if st.button(f"✨ Load '{selected}' Example", type="primary", use_container_width=True):
        st.session_state.example_code = examples[selected]
        st.session_state.example_name = selected
        st.success(f"✅ Loaded '{selected}'. Switch to 'Analyze' tab and click Analyze!")
        st.rerun()

# Tab 5: About
with tab5:
    st.subheader("ℹ️ About This Tool")
    
    st.markdown("""
    ### Solidity Vuln Scanner
    
    An AI-powered tool for detecting vulnerabilities in Ethereum smart contracts.
    
    **Technology Stack:**
    - Static Analysis (Regex patterns, code analysis)
    - OpenAI GPT-4o or Claude 3 for AI auditing (optional)
    - FastAPI for backend
    - Streamlit for frontend
    
    **Project Details:**
    - **Version:** 1.0.0
    - **License:** MIT
    - **Status:** Production Ready
    
    ### ⚠️ Disclaimer
    
    **Educational and Research Purpose Only**
    
    This tool is not a substitute for professional security audits. Always:
    1. Use multiple analysis tools
    2. Conduct professional security audits before production
    3. Run comprehensive test suites
    4. Have code reviewed by experts
    
    The scanner may produce false positives and false negatives.
    
    ### 📚 Resources
    
    - [DASP TOP 10](https://dasp.org/) - Smart Contract Security Best Practices
    - [Solidity Docs](https://docs.soliditylang.org/)
    - [OpenZeppelin Contracts](https://docs.openzeppelin.com/)
    - [Ethereum Security](https://consensys.io/research/smart-contract-best-practices/)
    """)
    
    st.info("""
    📧 **Questions or Issues?**
    
    Open an issue on GitHub or contact the maintainer.
    """)
