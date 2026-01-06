pragma solidity ^0.8.0;

/**
 * Small Contract - 50-150 LoC
 * Simple token contract with basic functionality
 */
contract SmallToken {
    mapping(address => uint256) public balances;
    address public owner;
    
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
    
    function burn(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        emit Transfer(msg.sender, address(0), amount);
    }
    
    function getBalance(address account) public view returns (uint256) {
        return balances[account];
    }
}
