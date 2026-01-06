pragma solidity ^0.8.0;

/**
 * Safe Contract - Best Practices
 * This contract follows security best practices
 */
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
    
    function mint(address to, uint256 amount) public onlyOwner {
        require(to != address(0), "Invalid recipient");
        balances[to] += amount;
        emit Transfer(address(0), to, amount);
    }
}
