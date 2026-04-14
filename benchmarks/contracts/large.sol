pragma solidity ^0.8.0;

/**
 * Large Contract - 2k-6k LoC
 * Complex DeFi-like contract with multiple features
 * Includes various patterns and some vulnerabilities
 */
contract LargeVault {
    
    // State variables
    mapping(address => uint256) public balances;
    mapping(address => mapping(address => uint256)) public allowances;
    mapping(address => bool) public whitelist;
    mapping(address => uint256) public depositTimestamps;
    mapping(address => uint256) public rewards;
    
    address public owner;
    address public treasury;
    uint256 public totalDeposits;
    uint256 public totalRewards;
    uint256 public constant MIN_DEPOSIT = 1000;
    uint256 public constant MAX_DEPOSIT = 1000000;
    uint256 public constant REWARD_RATE = 5; // 5% APY
    bool public paused;
    
    struct UserInfo {
        uint256 balance;
        uint256 lastClaim;
        uint256 totalEarned;
    }
    
    mapping(address => UserInfo) public userInfo;
    
    event Deposit(address indexed user, uint256 amount);
    event Withdraw(address indexed user, uint256 amount);
    event ClaimRewards(address indexed user, uint256 amount);
    event WhitelistUpdated(address indexed user, bool status);
    event Paused(address account);
    event Unpaused(address account);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    modifier whenNotPaused() {
        require(!paused, "Contract paused");
        _;
    }
    
    constructor(address _treasury) {
        owner = msg.sender;
        treasury = _treasury;
    }
    
    function deposit() public payable whenNotPaused {
        require(msg.value >= MIN_DEPOSIT, "Below minimum");
        require(msg.value <= MAX_DEPOSIT, "Above maximum");
        
        balances[msg.sender] += msg.value;
        totalDeposits += msg.value;
        depositTimestamps[msg.sender] = block.timestamp;
        
        userInfo[msg.sender].balance += msg.value;
        userInfo[msg.sender].lastClaim = block.timestamp;
        
        emit Deposit(msg.sender, msg.value);
    }
    
    function withdraw(uint256 amount) public whenNotPaused {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        require(block.timestamp >= depositTimestamps[msg.sender] + 7 days, "Lock period");
        
        // VULNERABILITY: Reentrancy - external call before state update
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] -= amount;
        totalDeposits -= amount;
        userInfo[msg.sender].balance -= amount;
        
        emit Withdraw(msg.sender, amount);
    }
    
    function claimRewards() public whenNotPaused {
        uint256 pending = calculateRewards(msg.sender);
        require(pending > 0, "No rewards");
        
        rewards[msg.sender] += pending;
        totalRewards += pending;
        userInfo[msg.sender].totalEarned += pending;
        userInfo[msg.sender].lastClaim = block.timestamp;
        
        (bool success, ) = msg.sender.call{value: pending}("");
        require(success, "Reward transfer failed");
        
        emit ClaimRewards(msg.sender, pending);
    }
    
    function calculateRewards(address user) public view returns (uint256) {
        if (userInfo[user].balance == 0) return 0;
        
        uint256 timeElapsed = block.timestamp - userInfo[user].lastClaim;
        uint256 principal = userInfo[user].balance;
        uint256 annualReward = principal * REWARD_RATE / 100;
        uint256 reward = annualReward * timeElapsed / 365 days;
        
        return reward;
    }
    
    function addToWhitelist(address user) public onlyOwner {
        whitelist[user] = true;
        emit WhitelistUpdated(user, true);
    }
    
    function removeFromWhitelist(address user) public onlyOwner {
        whitelist[user] = false;
        emit WhitelistUpdated(user, false);
    }
    
    function pause() public onlyOwner {
        paused = true;
        emit Paused(msg.sender);
    }
    
    function unpause() public onlyOwner {
        paused = false;
        emit Unpaused(msg.sender);
    }
    
    function updateTreasury(address _treasury) public onlyOwner {
        require(_treasury != address(0), "Invalid address");
        treasury = _treasury;
    }
    
    function emergencyWithdraw() public onlyOwner {
        uint256 balance = address(this).balance;
        (bool success, ) = treasury.call{value: balance}("");
        require(success, "Transfer failed");
    }
    
    function getUserInfo(address user) public view returns (
        uint256 balance,
        uint256 lastClaim,
        uint256 totalEarned,
        uint256 pendingRewards
    ) {
        UserInfo memory info = userInfo[user];
        return (
            info.balance,
            info.lastClaim,
            info.totalEarned,
            calculateRewards(user)
        );
    }
    
    function getTotalDeposits() public view returns (uint256) {
        return totalDeposits;
    }
    
    function getTotalRewards() public view returns (uint256) {
        return totalRewards;
    }
}

// Library for safe math operations
library SafeMath {
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        uint256 c = a + b;
        require(c >= a, "SafeMath: addition overflow");
        return c;
    }
    
    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b <= a, "SafeMath: subtraction underflow");
        return a - b;
    }
    
    function mul(uint256 a, uint256 b) internal pure returns (uint256) {
        if (a == 0) return 0;
        uint256 c = a * b;
        require(c / a == b, "SafeMath: multiplication overflow");
        return c;
    }
    
    function div(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b > 0, "SafeMath: division by zero");
        return a / b;
    }
}
