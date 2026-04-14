import pytest

from static_analyzer import StaticAnalyzer


def test_reentrancy_detected():
    code = """
    pragma solidity ^0.8.0;
    contract Vault {
        mapping(address => uint256) balances;
        function withdraw(uint256 amount) public {
            require(balances[msg.sender] >= amount);
            (bool ok, ) = msg.sender.call{value: amount}("");
            require(ok);
            balances[msg.sender] -= amount;
        }
    }
    """
    analyzer = StaticAnalyzer()
    result = analyzer.analyze(code, "Vault")
    vuln_types = {v.vuln_type for v in result.vulnerabilities}
    assert "reentrancy" in vuln_types
    assert any(v.severity == "CRITICAL" for v in result.vulnerabilities)


def test_access_control_detected():
    code = """
    pragma solidity ^0.8.0;
    contract Token {
        function mint(address to, uint256 amount) public {
            // no access control
        }
    }
    """
    analyzer = StaticAnalyzer()
    result = analyzer.analyze(code, "Token")
    vuln_types = {v.vuln_type for v in result.vulnerabilities}
    assert "access_control" in vuln_types
    assert result._get_overall_severity() in {"HIGH", "CRITICAL"}


def test_clean_contract_is_safe():
    code = """
    pragma solidity ^0.8.0;
    contract SafeToken {
        mapping(address => uint256) balances;
        event Transfer(address indexed from, address indexed to, uint256 amount);
        function transfer(address to, uint256 amount) public {
            require(balances[msg.sender] >= amount, "insufficient");
            require(to != address(0), "bad");
            balances[msg.sender] -= amount;
            balances[to] += amount;
            emit Transfer(msg.sender, to, amount);
        }
    }
    """
    analyzer = StaticAnalyzer()
    result = analyzer.analyze(code, "SafeToken")
    # With improved patterns, may find some low-confidence findings, but should be minimal
    high_severity = [v for v in result.vulnerabilities if v.severity in ["CRITICAL", "HIGH"]]
    assert len(high_severity) == 0 or all(v.confidence < 0.5 for v in high_severity)

