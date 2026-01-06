"""
Example usage of Solidity Vuln Scanner
Shows how to use the scanner programmatically (not just web UI)
"""

import json
from static_analyzer import StaticAnalyzer
from llm_auditor import LLMAuditor


# Example 1: Static Analysis Only
def example_static_analysis():
    """Basic vulnerability detection using static analysis"""
    
    vulnerable_contract = '''
    pragma solidity ^0.8.0;
    
    contract Bank {
        mapping(address => uint256) balance;
        
        function withdraw(uint256 amount) public {
            require(balance[msg.sender] >= amount);
            // Reentrancy vulnerability!
            (bool success, ) = msg.sender.call{value: amount}("");
            require(success);
            balance[msg.sender] -= amount;
        }
        
        function deposit() public payable {
            balance[msg.sender] += msg.value;
        }
    }
    '''
    
    print("=" * 60)
    print("EXAMPLE 1: Static Analysis")
    print("=" * 60)
    
    analyzer = StaticAnalyzer()
    result = analyzer.analyze(vulnerable_contract, "Bank")
    
    print(f"\nContract: {result.contract_name}")
    print(f"Risk Score: {result.risk_score}/100")
    print(f"Overall Severity: {result._get_overall_severity()}")
    print(f"Lines of Code: {result.lines_of_code}")
    print(f"\nVulnerabilities Found: {len(result.vulnerabilities)}")
    
    for i, vuln in enumerate(result.vulnerabilities, 1):
        print(f"\n  {i}. {vuln.vuln_type.upper()}")
        print(f"     Severity: {vuln.severity}")
        print(f"     Line: {vuln.line_number}")
        print(f"     Description: {vuln.description}")
        print(f"     Remediation: {vuln.remediation}")


# Example 2: Using LLM Auditor (requires API key)
def example_llm_audit():
    """Intelligent analysis using OpenAI/Claude"""
    
    contract = '''
    pragma solidity ^0.8.0;
    
    contract Token {
        mapping(address => uint256) balances;
        address owner;
        
        constructor() {
            owner = msg.sender;
            balances[owner] = 1000000 * 10 ** 18;
        }
        
        function transfer(address to, uint256 amount) public returns (bool) {
            require(balances[msg.sender] >= amount);
            require(to != address(0));
            
            balances[msg.sender] -= amount;
            balances[to] += amount;
            
            return true;
        }
        
        function burn(uint256 amount) public {
            // Only owner can burn
            require(msg.sender == owner);
            balances[msg.sender] -= amount;
        }
    }
    '''
    
    print("\n" + "=" * 60)
    print("EXAMPLE 2: LLM-Powered Audit")
    print("=" * 60)
    print("(Requires LLM_API_KEY environment variable)")
    
    try:
        auditor = LLMAuditor()
        result = auditor.audit(contract, "Token")
        
        print(f"\nAI Security Assessment:")
        print(f"Risk Level: {result.risk_assessment}")
        print(f"\nSummary:\n{result.summary}")
        
        if result.recommendations:
            print("\nRecommendations:")
            for rec in result.recommendations:
                print(f"  • {rec}")
        
        if result.best_practices:
            print("\nBest Practices:")
            for practice in result.best_practices:
                print(f"  • {practice}")
                
    except Exception as e:
        print(f"LLM audit not available: {e}")
        print("(Make sure LLM_API_KEY environment variable is set)")


# Example 3: Full analysis pipeline
def example_full_pipeline():
    """Complete analysis with both static and LLM audit"""
    
    contract = '''
    pragma solidity ^0.8.0;
    
    contract VulnerableDEX {
        mapping(address => uint256) userBalances;
        
        function swap(address token, uint256 amount) external {
            require(userBalances[msg.sender] >= amount);
            
            // REENTRANCY: Dangerous external call before state update
            (bool success, ) = token.call(
                abi.encodeWithSignature("transfer(address,uint256)", msg.sender, amount)
            );
            require(success);
            
            // State updated too late!
            userBalances[msg.sender] -= amount;
        }
    }
    '''
    
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Full Analysis Pipeline")
    print("=" * 60)
    
    # Static analysis
    analyzer = StaticAnalyzer()
    static_result = analyzer.analyze(contract, "VulnerableDEX")
    
    print(f"Static Analysis:")
    print(f"  Risk Score: {static_result.risk_score}")
    print(f"  Vulnerabilities: {len(static_result.vulnerabilities)}")
    
    for vuln in static_result.vulnerabilities:
        print(f"    - {vuln.vuln_type}: {vuln.severity}")
    
    # LLM audit
    try:
        auditor = LLMAuditor()
        llm_result = auditor.audit(contract, "VulnerableDEX")
        
        print(f"\nLLM Audit:")
        print(f"  Risk Level: {llm_result.risk_assessment}")
        print(f"  Summary: {llm_result.summary[:200]}...")
        
    except Exception as e:
        print(f"\nLLM Audit: Not available ({e})")
    
    # Combined report
    print(f"\nCombined Assessment:")
    print(f"  This contract has CRITICAL vulnerabilities")
    print(f"  Status: ❌ NOT PRODUCTION READY")


# Example 4: Batch analysis
def example_batch_analysis():
    """Analyze multiple contracts"""
    
    contracts = [
        {
            "name": "SimpleContract",
            "code": '''
            pragma solidity ^0.8.0;
            contract Simple {
                uint256 count = 0;
                function increment() public { count++; }
            }
            '''
        },
        {
            "name": "ProblematicContract",
            "code": '''
            pragma solidity ^0.8.0;
            contract Problem {
                function bad() public {
                    tx.origin.call("");  // tx.origin usage!
                }
            }
            '''
        }
    ]
    
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Batch Analysis")
    print("=" * 60)
    
    analyzer = StaticAnalyzer()
    results = []
    
    for contract in contracts:
        result = analyzer.analyze(contract["code"], contract["name"])
        results.append(result)
        
        print(f"\n{contract['name']}:")
        print(f"  Risk Score: {result.risk_score}")
        print(f"  Vulnerabilities: {len(result.vulnerabilities)}")
    
    # Summary
    total_vulns = sum(len(r.vulnerabilities) for r in results)
    avg_risk = sum(r.risk_score for r in results) / len(results)
    
    print(f"\n--- Batch Summary ---")
    print(f"Contracts analyzed: {len(results)}")
    print(f"Total vulnerabilities: {total_vulns}")
    print(f"Average risk score: {avg_risk:.2f}")


# Example 5: Export to JSON
def example_export_to_json():
    """Export analysis results to JSON for integration"""
    
    contract = '''
    pragma solidity ^0.8.0;
    contract Example {
        mapping(address => uint256) balances;
        
        function withdraw() public {
            (bool success, ) = msg.sender.call{value: balances[msg.sender]}("");
            balances[msg.sender] = 0;
        }
    }
    '''
    
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Export to JSON")
    print("=" * 60)
    
    analyzer = StaticAnalyzer()
    result = analyzer.analyze(contract, "Example")
    
    # Convert to dict
    report = result.to_dict()
    
    # Pretty print as JSON
    json_str = json.dumps(report, indent=2)
    print("\nJSON Report:")
    print(json_str)
    
    # Could save to file
    with open("audit_report.json", "w") as f:
        f.write(json_str)
    
    print("\n✅ Report saved to audit_report.json")


if __name__ == "__main__":
    print("\n🔐 Solidity Vuln Scanner - Examples\n")
    
    # Run examples
    example_static_analysis()
    example_llm_audit()
    example_full_pipeline()
    example_batch_analysis()
    example_export_to_json()
    
    print("\n" + "=" * 60)
    print("Examples complete! Check the code for more details.")
    print("=" * 60)
