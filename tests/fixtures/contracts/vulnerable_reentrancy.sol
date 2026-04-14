pragma solidity ^0.8.0;

/**
 * Vulnerable Contract - Reentrancy Attack
 * This contract has a critical reentrancy vulnerability
 */
contract VulnerableVault {
    mapping(address => uint256) balances;
    
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        // REENTRANCY: External call before state update!
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] -= amount;  // State updated too late
    }
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
}
