pragma solidity ^0.8.0;

/**
 * XLarge Contract - 10k+ LoC
 * Very large contract simulating complex DeFi protocol
 * Multiple modules, libraries, and patterns
 */
contract XLargeProtocol {
    // Extensive state variables
    mapping(address => uint256) public balances;
    mapping(address => mapping(address => uint256)) public allowances;
    mapping(address => bool) public whitelist;
    mapping(address => bool) public blacklist;
    mapping(address => uint256) public depositTimestamps;
    mapping(address => uint256) public rewards;
    mapping(address => uint256) public penalties;
    mapping(address => uint256) public stakingAmount;
    mapping(address => uint256) public stakingTimestamp;
    
    address public owner;
    address public treasury;
    address public rewardPool;
    uint256 public totalDeposits;
    uint256 public totalRewards;
    uint256 public totalPenalties;
    uint256 public totalStaked;
    uint256 public constant MIN_DEPOSIT = 1000;
    uint256 public constant MAX_DEPOSIT = 1000000;
    uint256 public constant REWARD_RATE = 5;
    uint256 public constant PENALTY_RATE = 2;
    bool public paused;
    bool public emergencyMode;
    
    struct UserInfo {
        uint256 balance;
        uint256 lastClaim;
        uint256 totalEarned;
        uint256 totalPenalties;
        bool isActive;
    }
    
    struct StakingInfo {
        uint256 amount;
        uint256 timestamp;
        uint256 lockPeriod;
        bool isLocked;
    }
    
    mapping(address => UserInfo) public userInfo;
    mapping(address => StakingInfo) public stakingInfo;
    
    event Deposit(address indexed user, uint256 amount);
    event Withdraw(address indexed user, uint256 amount);
    event ClaimRewards(address indexed user, uint256 amount);
    event Stake(address indexed user, uint256 amount, uint256 lockPeriod);
    event Unstake(address indexed user, uint256 amount);
    event WhitelistUpdated(address indexed user, bool status);
    event BlacklistUpdated(address indexed user, bool status);
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
    
    modifier whenNotEmergency() {
        require(!emergencyMode, "Emergency mode active");
        _;
    }
    
    constructor(address _treasury, address _rewardPool) {
        owner = msg.sender;
        treasury = _treasury;
        rewardPool = _rewardPool;
    }
    
    function deposit() public payable whenNotPaused whenNotEmergency {
        require(!blacklist[msg.sender], "Address blacklisted");
        require(msg.value >= MIN_DEPOSIT, "Below minimum");
        require(msg.value <= MAX_DEPOSIT, "Above maximum");
        
        balances[msg.sender] += msg.value;
        totalDeposits += msg.value;
        depositTimestamps[msg.sender] = block.timestamp;
        
        userInfo[msg.sender].balance += msg.value;
        userInfo[msg.sender].lastClaim = block.timestamp;
        userInfo[msg.sender].isActive = true;
        
        emit Deposit(msg.sender, msg.value);
    }
    
    function withdraw(uint256 amount) public whenNotPaused {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        require(block.timestamp >= depositTimestamps[msg.sender] + 7 days, "Lock period");
        
        // VULNERABILITY: Reentrancy pattern
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] -= amount;
        totalDeposits -= amount;
        userInfo[msg.sender].balance -= amount;
        
        if (userInfo[msg.sender].balance == 0) {
            userInfo[msg.sender].isActive = false;
        }
        
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
    
    function stake(uint256 amount, uint256 lockPeriod) public whenNotPaused {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        require(lockPeriod >= 30 days && lockPeriod <= 365 days, "Invalid lock period");
        
        balances[msg.sender] -= amount;
        stakingAmount[msg.sender] += amount;
        stakingTimestamp[msg.sender] = block.timestamp;
        totalStaked += amount;
        
        stakingInfo[msg.sender] = StakingInfo({
            amount: stakingAmount[msg.sender],
            timestamp: block.timestamp,
            lockPeriod: lockPeriod,
            isLocked: true
        });
        
        emit Stake(msg.sender, amount, lockPeriod);
    }
    
    function unstake() public whenNotPaused {
        StakingInfo memory info = stakingInfo[msg.sender];
        require(info.isLocked, "No active stake");
        require(block.timestamp >= info.timestamp + info.lockPeriod, "Still locked");
        
        uint256 amount = info.amount;
        balances[msg.sender] += amount;
        stakingAmount[msg.sender] = 0;
        totalStaked -= amount;
        
        stakingInfo[msg.sender].isLocked = false;
        
        emit Unstake(msg.sender, amount);
    }
    
    function addToWhitelist(address user) public onlyOwner {
        whitelist[user] = true;
        emit WhitelistUpdated(user, true);
    }
    
    function removeFromWhitelist(address user) public onlyOwner {
        whitelist[user] = false;
        emit WhitelistUpdated(user, false);
    }
    
    function addToBlacklist(address user) public onlyOwner {
        blacklist[user] = true;
        emit BlacklistUpdated(user, true);
    }
    
    function removeFromBlacklist(address user) public onlyOwner {
        blacklist[user] = false;
        emit BlacklistUpdated(user, false);
    }
    
    function pause() public onlyOwner {
        paused = true;
        emit Paused(msg.sender);
    }
    
    function unpause() public onlyOwner {
        paused = false;
        emit Unpaused(msg.sender);
    }
    
    function setEmergencyMode(bool _enabled) public onlyOwner {
        emergencyMode = _enabled;
    }
    
    function updateTreasury(address _treasury) public onlyOwner {
        require(_treasury != address(0), "Invalid address");
        treasury = _treasury;
    }
    
    function updateRewardPool(address _rewardPool) public onlyOwner {
        require(_rewardPool != address(0), "Invalid address");
        rewardPool = _rewardPool;
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
        uint256 pendingRewards,
        bool isActive
    ) {
        UserInfo memory info = userInfo[user];
        return (
            info.balance,
            info.lastClaim,
            info.totalEarned,
            calculateRewards(user),
            info.isActive
        );
    }
    
    function getStakingInfo(address user) public view returns (
        uint256 amount,
        uint256 timestamp,
        uint256 lockPeriod,
        bool isLocked
    ) {
        StakingInfo memory info = stakingInfo[user];
        return (
            info.amount,
            info.timestamp,
            info.lockPeriod,
            info.isLocked
        );
    }
    
    function getTotalDeposits() public view returns (uint256) {
        return totalDeposits;
    }
    
    function getTotalRewards() public view returns (uint256) {
        return totalRewards;
    }
    
    function getTotalStaked() public view returns (uint256) {
        return totalStaked;
    }
}
