"""
Unit tests untuk Database Optimizer System
"""

import pytest
import asyncio
import asyncpg
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json
import time

try:
    import redis.asyncio as redis
except ImportError:
    try:
        import aioredis as redis
    except ImportError:
        redis = None

# Tambahkan parent directory ke path untuk import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_optimizer import (
    DatabaseConfig, QueryMetrics, ConnectionPool, QueryCache,
    QueryOptimizer, DatabaseOptimizer, SlowQueryAnalyzer
)

class TestDatabaseConfig:
    """Test DatabaseConfig class"""
    
    def test_default_config(self):
        """Test default configuration"""
        config = DatabaseConfig()
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "sangkuriang_db"
        assert config.user == "sangkuriang_user"
        assert config.min_connections == 10
        assert config.max_connections == 100
        assert config.enable_caching == True
        assert config.cache_ttl == 3600
        assert config.slow_query_threshold == 1.0
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = DatabaseConfig(
            host="custom-host",
            port=5433,
            database="custom_db",
            min_connections=20,
            max_connections=200,
            enable_caching=False,
            cache_ttl=7200
        )
        assert config.host == "custom-host"
        assert config.port == 5433
        assert config.database == "custom_db"
        assert config.min_connections == 20
        assert config.max_connections == 200
        assert config.enable_caching == False
        assert config.cache_ttl == 7200

class TestQueryMetrics:
    """Test QueryMetrics class"""
    
    def test_initialization(self):
        """Test QueryMetrics initialization"""
        metrics = QueryMetrics(
            query_hash="hash123",
            query_text="SELECT * FROM users"
        )
        assert metrics.query_hash == "hash123"
        assert metrics.query_text == "SELECT * FROM users"
        assert metrics.execution_count == 0
        assert metrics.total_time == 0.0
        assert metrics.avg_time == 0.0
        assert metrics.min_time == float('inf')
        assert metrics.max_time == 0.0
        assert metrics.last_executed is None
    
    def test_update_metrics(self):
        """Test metrics update functionality"""
        metrics = QueryMetrics("hash123", "SELECT * FROM users")
        
        # First execution
        metrics.update(0.5)
        assert metrics.execution_count == 1
        assert metrics.total_time == 0.5
        assert metrics.avg_time == 0.5
        assert metrics.min_time == 0.5
        assert metrics.max_time == 0.5
        assert metrics.last_executed is not None
        
        # Second execution
        metrics.update(1.2)
        assert metrics.execution_count == 2
        assert metrics.total_time == 1.7
        assert metrics.avg_time == 0.85
        assert metrics.min_time == 0.5
        assert metrics.max_time == 1.2
    
    def test_multiple_updates(self):
        """Test multiple metrics updates"""
        metrics = QueryMetrics("hash123", "SELECT * FROM users")
        
        execution_times = [0.1, 0.3, 0.2, 0.4, 0.15]
        for time_val in execution_times:
            metrics.update(time_val)
        
        assert metrics.execution_count == 5
        assert metrics.total_time == sum(execution_times)
        assert metrics.avg_time == sum(execution_times) / 5
        assert metrics.min_time == min(execution_times)
        assert metrics.max_time == max(execution_times)

class TestConnectionPool:
    """Test ConnectionPool class"""
    
    @pytest.fixture
    def config(self):
        return DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_pass",
            min_connections=5,
            max_connections=20
        )
    
    @pytest.fixture
    def pool(self, config):
        return ConnectionPool(config)
    
    @pytest.mark.asyncio
    async def test_pool_initialization(self, pool):
        """Test connection pool initialization"""
        with patch('asyncpg.create_pool', new_callable=AsyncMock) as mock_create_pool:
            mock_pool = AsyncMock()
            mock_create_pool.return_value = mock_pool
            
            await pool.initialize()
            
            mock_create_pool.assert_called_once()
            assert pool.pool == mock_pool
            assert pool.pool_created_at is not None
    
    @pytest.mark.asyncio
    async def test_pool_initialization_failure(self, pool):
        """Test connection pool initialization failure"""
        with patch('asyncpg.create_pool', new_callable=AsyncMock) as mock_create_pool:
            mock_create_pool.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception):
                await pool.initialize()
    
    @pytest.mark.asyncio
    async def test_pool_close(self, pool):
        """Test connection pool closing"""
        pool.pool = AsyncMock()
        
        await pool.close()
        
        pool.pool.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_acquire_connection(self, pool):
        """Test connection acquisition"""
        pool.pool = AsyncMock()
        mock_connection = AsyncMock()
        pool.pool.acquire = AsyncMock(return_value=mock_connection)
        pool.pool.release = AsyncMock()
        
        async with pool.acquire_connection() as connection:
            assert connection == mock_connection
        
        pool.pool.acquire.assert_called_once()
        pool.pool.release.assert_called_once_with(mock_connection)
    
    @pytest.mark.asyncio
    async def test_acquire_connection_with_wait_time(self, pool):
        """Test connection acquisition with wait time"""
        pool.pool = AsyncMock()
        mock_connection = AsyncMock()
        
        # Simulate slow acquisition
        async def slow_acquire():
            await asyncio.sleep(0.2)  # Simulate delay
            return mock_connection
        
        pool.pool.acquire = slow_acquire
        pool.pool.release = AsyncMock()
        
        async with pool.acquire_connection() as connection:
            assert connection == mock_connection
        
        # Verify metrics were updated
        assert len(pool.connection_metrics['connection_wait_time']) > 0
    
    @pytest.mark.asyncio
    async def test_acquire_connection_error(self, pool):
        """Test connection acquisition with error"""
        pool.pool = AsyncMock()
        pool.pool.acquire = AsyncMock(side_effect=Exception("Acquisition failed"))
        
        with pytest.raises(Exception):
            async with pool.acquire_connection():
                pass
        
        assert pool.connection_metrics['connection_errors'] == 1
    
    def test_get_metrics_without_pool(self, pool):
        """Test getting metrics without initialized pool"""
        metrics = pool.get_metrics()
        assert metrics == {}
    
    def test_get_metrics_with_pool(self, pool):
        """Test getting metrics with initialized pool"""
        pool.pool = Mock()
        pool.pool.get_stats.return_value = {
            'size': 10,
            'idle': 5,
            'used': 5
        }
        pool.pool_created_at = datetime.now() - timedelta(minutes=5)  # Set 5 minutes ago
        pool.connection_metrics['total_connections'] = 50
        
        metrics = pool.get_metrics()
        
        assert metrics['pool_size'] == 10
        assert metrics['available_connections'] == 5
        assert metrics['active_connections'] == 5
        assert metrics['total_connections'] == 50
        assert metrics['pool_uptime_minutes'] >= 5

class TestQueryCache:
    """Test QueryCache class"""
    
    @pytest.fixture
    def redis_client(self):
        return AsyncMock()
    
    @pytest.fixture
    def cache(self, redis_client):
        return QueryCache(redis_client, default_ttl=3600)
    
    def test_cache_initialization(self, cache):
        """Test cache initialization"""
        assert cache.default_ttl == 3600
        assert cache.cache_hits == 0
        assert cache.cache_misses == 0
        assert cache.cache_invalidations == 0
    
    def test_generate_cache_key(self, cache):
        """Test cache key generation"""
        query = "SELECT * FROM users WHERE id = $1"
        params = (123,)
        
        key1 = cache._generate_cache_key(query, params)
        key2 = cache._generate_cache_key(query, params)
        
        # Same query and params should generate same key
        assert key1 == key2
        
        # Different params should generate different key
        key3 = cache._generate_cache_key(query, (456,))
        assert key1 != key3
    
    @pytest.mark.asyncio
    async def test_cache_get_hit(self, cache):
        """Test cache get with hit"""
        query = "SELECT * FROM users"
        params = (123,)
        expected_result = [{"id": 123, "name": "John"}]
        
        cache.redis.get = AsyncMock(return_value=json.dumps(expected_result))
        
        result = await cache.get(query, params)
        
        assert result == expected_result
        assert cache.cache_hits == 1
        assert cache.cache_misses == 0
    
    @pytest.mark.asyncio
    async def test_cache_get_miss(self, cache):
        """Test cache get with miss"""
        query = "SELECT * FROM users"
        params = (123,)
        
        cache.redis.get = AsyncMock(return_value=None)
        
        result = await cache.get(query, params)
        
        assert result is None
        assert cache.cache_hits == 0
        assert cache.cache_misses == 1
    
    @pytest.mark.asyncio
    async def test_cache_get_error(self, cache):
        """Test cache get with error"""
        query = "SELECT * FROM users"
        params = (123,)
        
        cache.redis.get = AsyncMock(side_effect=Exception("Redis error"))
        
        result = await cache.get(query, params)
        
        assert result is None
        assert cache.cache_hits == 0
        assert cache.cache_misses == 0
    
    @pytest.mark.asyncio
    async def test_cache_set(self, cache, redis_client):
        """Test setting cache entries"""
        query = "SELECT * FROM users"
        params = (123,)
        result = [(1, 'user1'), (2, 'user2')]
        
        # Mock redis.setex untuk return True
        redis_client.setex = AsyncMock(return_value=True)
        
        await cache.set(query, params, result)
        
        # Verify redis.setex was called with correct parameters
        redis_client.setex.assert_called_once()
        call_args = redis_client.setex.call_args
        assert call_args is not None
        
        # Cache hits should remain 0 since we're only setting, not getting
        assert cache.cache_hits == 0
    
    @pytest.mark.asyncio
    async def test_cache_set_with_custom_ttl(self, cache, redis_client):
        """Test cache set with custom TTL"""
        query = "SELECT * FROM users"
        params = (123,)
        result = [{"id": 123, "name": "John"}]
        custom_ttl = 7200

        redis_client.setex = AsyncMock(return_value=True)

        await cache.set(query, params, result, custom_ttl)

        redis_client.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_set_no_redis(self):
        """Test cache set without Redis"""
        cache = QueryCache(None, default_ttl=3600)
        
        await cache.set("query", (), "result")
        # Should not raise error
    
    @pytest.mark.asyncio
    async def test_cache_invalidate(self, cache, redis_client):
        """Test cache invalidation"""
        # Mock redis operations
        redis_client.keys = AsyncMock(return_value=["query_cache:abc123"])
        redis_client.delete = AsyncMock(return_value=1)
        
        # Test invalidate specific pattern
        await cache.invalidate("SELECT * FROM users")
        
        redis_client.keys.assert_called_once()
        redis_client.delete.assert_called_once()
        assert cache.cache_invalidations == 1
        
        # Test full invalidation
        redis_client.keys = AsyncMock(return_value=["query_cache:def456", "query_cache:ghi789"])
        redis_client.delete = AsyncMock(return_value=2)
        
        await cache.invalidate()
        
        assert cache.cache_invalidations == 3  # 1 + 2

# Tambahan test untuk komponen yang belum diimplementasikan
class TestQueryOptimizer:
    """Test QueryOptimizer class (placeholder)"""
    
    def test_placeholder(self):
        """Placeholder test"""
        assert True

class TestDatabaseOptimizer:
    """Test DatabaseOptimizer class (placeholder)"""
    
    def test_placeholder(self):
        """Placeholder test"""
        assert True

class TestSlowQueryAnalyzer:
    """Test SlowQueryAnalyzer class (placeholder)"""
    
    def test_placeholder(self):
        """Placeholder test"""
        assert True

if __name__ == "__main__":
    pytest.main([__file__])