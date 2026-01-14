"""
Tests for middleware (rate limiting, caching)
"""

import pytest
import time
from middleware import RateLimiter, AnalysisCache


class TestRateLimiter:
    """Test rate limiting functionality"""
    
    def test_rate_limiter_allows_requests(self):
        """Test that rate limiter allows requests within limit"""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        key = "test_ip"
        
        # Should allow first 10 requests
        for i in range(10):
            assert limiter.is_allowed(key)
        
        # 11th request should be blocked
        assert not limiter.is_allowed(key)
    
    def test_rate_limiter_resets_after_window(self):
        """Test that rate limiter resets after time window"""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        key = "test_ip"
        
        assert limiter.is_allowed(key)
        assert limiter.is_allowed(key)
        assert not limiter.is_allowed(key)
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should allow requests again
        assert limiter.is_allowed(key)
    
    def test_remaining_requests_calculation(self):
        """Test remaining requests calculation"""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        key = "test_ip"
        
        assert limiter.get_remaining(key) == 5
        limiter.is_allowed(key)
        assert limiter.get_remaining(key) == 4
        limiter.is_allowed(key)
        assert limiter.get_remaining(key) == 3


class TestAnalysisCache:
    """Test analysis cache functionality"""
    
    def test_cache_stores_and_retrieves(self):
        """Test that cache stores and retrieves values"""
        cache = AnalysisCache(max_size=10, ttl_seconds=60)
        
        code = "pragma solidity ^0.8.0; contract X {}"
        name = "X"
        result = {"test": "data"}
        
        # Should not be in cache initially
        assert cache.get(code, name) is None
        
        # Store in cache
        cache.set(code, name, result)
        
        # Should retrieve from cache
        cached = cache.get(code, name)
        assert cached == result
    
    def test_cache_expires_after_ttl(self):
        """Test that cache entries expire after TTL"""
        cache = AnalysisCache(max_size=10, ttl_seconds=1)
        
        code = "pragma solidity ^0.8.0; contract X {}"
        name = "X"
        result = {"test": "data"}
        
        cache.set(code, name, result)
        assert cache.get(code, name) == result
        
        # Wait for TTL to expire
        time.sleep(1.1)
        
        # Should be expired
        assert cache.get(code, name) is None
    
    def test_cache_evicts_oldest_when_full(self):
        """Test that cache evicts oldest entry when full"""
        cache = AnalysisCache(max_size=2, ttl_seconds=60)
        
        # Fill cache
        cache.set("code1", "name1", {"data": 1})
        cache.set("code2", "name2", {"data": 2})
        
        # Add third entry (should evict oldest)
        cache.set("code3", "name3", {"data": 3})
        
        # First entry should be evicted
        assert cache.get("code1", "name1") is None
        # Other entries should still be there
        assert cache.get("code2", "name2") is not None
        assert cache.get("code3", "name3") is not None
    
    def test_cache_key_generation(self):
        """Test that cache keys are generated correctly"""
        cache = AnalysisCache()
        
        code1 = "pragma solidity ^0.8.0; contract X {}"
        code2 = "pragma solidity ^0.8.0; contract Y {}"
        
        # Different code should generate different keys
        key1 = cache._generate_key(code1, "X")
        key2 = cache._generate_key(code2, "Y")
        assert key1 != key2
        
        # Same code should generate same key
        key1_again = cache._generate_key(code1, "X")
        assert key1 == key1_again
    
    def test_cache_uses_sha256(self):
        """Test that cache uses SHA-256 (not MD5)"""
        cache = AnalysisCache()
        key = cache._generate_key("test", "name")
        
        # SHA-256 produces 64 hex characters
        assert len(key) == 64
        # Should be valid hex
        assert all(c in '0123456789abcdef' for c in key)
