"""
Database Optimization System untuk SANGKURIANG
Mengimplementasikan connection pooling, query optimization, dan caching strategies
"""

import asyncio
import logging
import time
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import asyncpg

try:
    import redis.asyncio as redis
except ImportError:
    try:
        import aioredis as redis
    except ImportError:
        redis = None

from collections import defaultdict, deque
import psutil
import aiofiles

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str = "sangkuriang_db"
    user: str = "sangkuriang_user"
    password: str = ""
    min_connections: int = 10
    max_connections: int = 100
    connection_timeout: int = 30
    command_timeout: int = 60
    
    # Optimization settings
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1 hour
    enable_query_logging: bool = True
    slow_query_threshold: float = 1.0  # seconds

@dataclass
class QueryMetrics:
    """Query performance metrics"""
    query_hash: str
    query_text: str
    execution_count: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    last_executed: Optional[datetime] = None
    
    def update(self, execution_time: float):
        """Update metrics dengan execution time baru"""
        self.execution_count += 1
        self.total_time += execution_time
        self.avg_time = self.total_time / self.execution_count
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)
        self.last_executed = datetime.now()

class ConnectionPool:
    """Advanced connection pool dengan monitoring dan optimization"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self.connection_metrics = {
            'total_connections': 0,
            'active_connections': 0,
            'idle_connections': 0,
            'waiting_connections': 0,
            'connection_wait_time': deque(maxlen=1000),
            'connection_errors': 0
        }
        self.pool_created_at: Optional[datetime] = None
    
    async def initialize(self):
        """Initialize connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=self.config.command_timeout,
                server_settings={
                    'application_name': 'sangkuriang_db_pool',
                    'jit': 'off',  # Disable JIT untuk performance
                    'work_mem': '256MB',  # Increase work memory
                    'maintenance_work_mem': '512MB'
                }
            )
            self.pool_created_at = datetime.now()
            logger.info(f"Connection pool initialized with {self.config.min_connections}-{self.config.max_connections} connections")
            
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Connection pool closed")
    
    @asynccontextmanager
    async def acquire_connection(self):
        """Acquire connection dari pool dengan timing"""
        start_time = time.time()
        connection = None
        
        try:
            connection = await self.pool.acquire()
            wait_time = time.time() - start_time
            
            if wait_time > 0.1:  # Log slow acquisitions
                logger.warning(f"Slow connection acquisition: {wait_time:.3f}s")
            
            self.connection_metrics['connection_wait_time'].append(wait_time)
            self.connection_metrics['active_connections'] += 1
            
            yield connection
            
        except Exception as e:
            self.connection_metrics['connection_errors'] += 1
            logger.error(f"Connection acquisition error: {e}")
            raise
            
        finally:
            if connection:
                await self.pool.release(connection)
                self.connection_metrics['active_connections'] -= 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get connection pool metrics"""
        if not self.pool:
            return {}
        
        pool_stats = self.pool.get_stats()
        return {
            'pool_size': pool_stats.get('size', 0),
            'available_connections': pool_stats.get('idle', 0),
            'active_connections': pool_stats.get('used', 0),
            'total_connections': self.connection_metrics['total_connections'],
            'connection_errors': self.connection_metrics['connection_errors'],
            'avg_wait_time': (sum(self.connection_metrics['connection_wait_time']) / 
                            len(self.connection_metrics['connection_wait_time']))
                           if self.connection_metrics['connection_wait_time'] else 0,
            'pool_uptime_minutes': ((datetime.now() - self.pool_created_at).total_seconds() / 60)
                                   if self.pool_created_at else 0
        }

class QueryCache:
    """Intelligent query cache dengan TTL dan invalidation"""
    
    def __init__(self, redis_client: redis.Redis, default_ttl: int = 3600):
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_invalidations = 0
        
    def _generate_cache_key(self, query: str, params: Tuple) -> str:
        """Generate cache key dari query dan parameters"""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        params_hash = hashlib.md5(str(params).encode()).hexdigest()
        return f"query_cache:{query_hash}:{params_hash}"
    
    async def get(self, query: str, params: Tuple = ()) -> Optional[Any]:
        """Get cached query result"""
        if not self.redis:
            return None
        
        cache_key = self._generate_cache_key(query, params)
        
        try:
            cached_result = await self.redis.get(cache_key)
            if cached_result:
                self.cache_hits += 1
                return json.loads(cached_result)
            else:
                self.cache_misses += 1
                return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(self, query: str, params: Tuple = (), result: Any = None, ttl: int = None):
        """Set cache untuk query result"""
        if not self.redis or result is None:
            return
        
        cache_key = self._generate_cache_key(query, params)
        ttl = ttl or self.default_ttl
        
        try:
            await self.redis.setex(
                cache_key, 
                ttl, 
                json.dumps(result, default=str)
            )
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def invalidate(self, query_pattern: str = None):
        """Invalidate cache entries"""
        if not self.redis:
            return
        
        try:
            if query_pattern:
                # Invalidate specific pattern
                pattern = f"query_cache:*{hashlib.md5(query_pattern.encode()).hexdigest()}*"
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
                    self.cache_invalidations += len(keys)
            else:
                # Flush all query cache
                keys = await self.redis.keys("query_cache:*")
                if keys:
                    await self.redis.delete(*keys)
                    self.cache_invalidations += len(keys)
                    
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate_percent': round(hit_rate, 2),
            'total_requests': total_requests,
            'invalidations': self.cache_invalidations
        }

class QueryOptimizer:
    """Query optimization dengan analysis dan recommendations"""
    
    def __init__(self, slow_query_threshold: float = 1.0):
        self.slow_query_threshold = slow_query_threshold
        self.query_metrics: Dict[str, QueryMetrics] = {}
        self.optimization_recommendations = []
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query untuk consistent hashing"""
        # Remove extra whitespace and normalize
        normalized = ' '.join(query.strip().split())
        # Convert to lowercase
        normalized = normalized.lower()
        # Remove specific values (keep placeholders)
        import re
        normalized = re.sub(r'\$\d+|%s|\?', '?', normalized)
        return normalized
    
    def _generate_query_hash(self, query: str) -> str:
        """Generate hash untuk query"""
        normalized_query = self._normalize_query(query)
        return hashlib.md5(normalized_query.encode()).hexdigest()
    
    def record_query_execution(self, query: str, execution_time: float, params: Tuple = ()):
        """Record query execution metrics"""
        query_hash = self._generate_query_hash(query)
        
        if query_hash not in self.query_metrics:
            self.query_metrics[query_hash] = QueryMetrics(
                query_hash=query_hash,
                query_text=self._normalize_query(query)[:200]  # Truncate for storage
            )
        
        self.query_metrics[query_hash].update(execution_time)
        
        # Check if slow query
        if execution_time > self.slow_query_threshold:
            logger.warning(f"Slow query detected: {execution_time:.3f}s - {query[:100]}...")
            self._generate_optimization_recommendation(query, execution_time)
    
    def _generate_optimization_recommendation(self, query: str, execution_time: float):
        """Generate optimization recommendations"""
        recommendations = []
        
        # Basic query analysis
        query_lower = query.lower()
        
        # Check for missing indexes
        if 'where' in query_lower and 'select' in query_lower:
            if not any(keyword in query_lower for keyword in ['indexed', 'primary key']):
                recommendations.append("Consider adding indexes on WHERE clause columns")
        
        # Check for N+1 query patterns
        if 'in (' in query_lower or 'exists' in query_lower:
            recommendations.append("Consider using JOIN instead of subqueries")
        
        # Check for SELECT *
        if 'select *' in query_lower:
            recommendations.append("Avoid SELECT *, specify only needed columns")
        
        # Check for missing LIMIT
        if 'select' in query_lower and 'limit' not in query_lower:
            recommendations.append("Consider adding LIMIT clause for large result sets")
        
        if recommendations:
            self.optimization_recommendations.append({
                'query': query[:100] + "...",
                'execution_time': execution_time,
                'recommendations': recommendations,
                'timestamp': datetime.now()
            })
    
    def get_slow_queries(self, threshold: float = None) -> List[Dict[str, Any]]:
        """Get list of slow queries"""
        threshold = threshold or self.slow_query_threshold
        slow_queries = []
        
        for metrics in self.query_metrics.values():
            if metrics.avg_time > threshold:
                slow_queries.append({
                    'query': metrics.query_text,
                    'avg_time': metrics.avg_time,
                    'max_time': metrics.max_time,
                    'execution_count': metrics.execution_count,
                    'last_executed': metrics.last_executed
                })
        
        # Sort by average time
        slow_queries.sort(key=lambda x: x['avg_time'], reverse=True)
        return slow_queries[:20]  # Return top 20
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get optimization recommendations"""
        return self.optimization_recommendations[-50:]  # Last 50 recommendations

class DatabaseOptimizer:
    """
    Main database optimization system untuk SANGKURIANG
    Menggabungkan connection pooling, caching, dan query optimization
    """
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection_pool = ConnectionPool(config)
        self.query_optimizer = QueryOptimizer(config.slow_query_threshold)
        self.cache: Optional[QueryCache] = None
        self.redis_client: Optional[redis.Redis] = None
        self.performance_metrics = {
            'total_queries': 0,
            'cached_queries': 0,
            'optimized_queries': 0,
            'total_time_saved': 0.0
        }
    
    async def initialize(self):
        """Initialize database optimizer"""
        try:
            # Initialize connection pool
            await self.connection_pool.initialize()
            
            # Initialize Redis untuk caching jika di-enable
            if self.config.enable_caching:
                self.redis_client = aioredis.from_url(
                    "redis://localhost:6379/1",  # Use different DB for cache
                    encoding="utf-8",
                    decode_responses=True
                )
                self.cache = QueryCache(self.redis_client, self.config.cache_ttl)
            
            logger.info("Database optimizer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database optimizer: {e}")
            raise
    
    async def close(self):
        """Close database optimizer"""
        try:
            await self.connection_pool.close()
            if self.redis_client:
                await self.redis_client.close()
            logger.info("Database optimizer closed")
        except Exception as e:
            logger.error(f"Error closing database optimizer: {e}")
    
    async def execute_query(self, query: str, params: Tuple = (), use_cache: bool = True) -> Any:
        """
        Execute query dengan optimization
        
        Args:
            query: SQL query string
            params: Query parameters
            use_cache: Whether to use cache
        
        Returns:
            Query result
        """
        start_time = time.time()
        query_hash = self.query_optimizer._generate_query_hash(query)
        
        try:
            # Check cache first
            if use_cache and self.cache:
                cached_result = await self.cache.get(query, params)
                if cached_result is not None:
                    self.performance_metrics['cached_queries'] += 1
                    return cached_result
            
            # Execute query
            async with self.connection_pool.acquire_connection() as connection:
                result = await connection.fetch(query, *params)
                
                # Convert to list of dicts for serialization
                result_list = [dict(row) for row in result]
                
                # Cache the result
                if use_cache and self.cache and result_list:
                    await self.cache.set(query, params, result_list)
                
                # Record metrics
                execution_time = time.time() - start_time
                self.query_optimizer.record_query_execution(query, execution_time, params)
                
                self.performance_metrics['total_queries'] += 1
                
                return result_list
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query execution error: {e}")
            raise
    
    async def execute_optimized_query(self, query: str, params: Tuple = ()) -> Any:
        """Execute query dengan additional optimizations"""
        
        # Apply query optimizations
        optimized_query = self._apply_query_optimizations(query)
        
        # Execute optimized query
        result = await self.execute_query(optimized_query, params)
        
        self.performance_metrics['optimized_queries'] += 1
        
        return result
    
    def _apply_query_optimizations(self, query: str) -> str:
        """Apply automatic query optimizations"""
        optimized_query = query
        
        # Add query hints based on analysis
        # This is a simplified version - real implementation would be more sophisticated
        
        if 'select' in query.lower() and 'limit' not in query.lower():
            # Add reasonable limit for safety
            optimized_query += " LIMIT 10000"
        
        return optimized_query
    
    async def perform_maintenance(self):
        """Perform database maintenance tasks"""
        try:
            # Update table statistics
            maintenance_queries = [
                "ANALYZE",
                "VACUUM ANALYZE",
                "SELECT pg_stat_reset()"
            ]
            
            for query in maintenance_queries:
                await self.execute_query(query, use_cache=False)
            
            # Clear old cache entries
            if self.cache:
                await self.cache.invalidate()
            
            logger.info("Database maintenance completed")
            
        except Exception as e:
            logger.error(f"Database maintenance error: {e}")
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        
        # Get connection pool metrics
        pool_metrics = self.connection_pool.get_metrics()
        
        # Get cache statistics
        cache_stats = self.cache.get_cache_stats() if self.cache else {}
        
        # Get slow queries
        slow_queries = self.query_optimizer.get_slow_queries()
        
        # Get optimization recommendations
        recommendations = self.query_optimizer.get_optimization_recommendations()
        
        # Calculate time saved by caching
        avg_query_time = sum(q['avg_time'] for q in slow_queries) / len(slow_queries) if slow_queries else 0.1
        time_saved = self.performance_metrics['cached_queries'] * avg_query_time
        
        return {
            'connection_pool': pool_metrics,
            'cache_statistics': cache_stats,
            'performance_metrics': self.performance_metrics,
            'slow_queries': slow_queries[:10],  # Top 10 slow queries
            'optimization_recommendations': recommendations[-10:],  # Last 10
            'time_saved_by_caching_seconds': round(time_saved, 2),
            'generated_at': datetime.now().isoformat()
        }
    
    async def export_slow_query_log(self, filepath: str):
        """Export slow query log ke file"""
        try:
            slow_queries = self.query_optimizer.get_slow_queries()
            
            async with aiofiles.open(filepath, 'w') as f:
                await f.write(json.dumps({
                    'exported_at': datetime.now().isoformat(),
                    'slow_query_threshold': self.config.slow_query_threshold,
                    'slow_queries': slow_queries
                }, indent=2, default=str))
            
            logger.info(f"Slow query log exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Export slow query log error: {e}")

# Utility functions
async def create_database_optimizer(config: DatabaseConfig = None) -> DatabaseOptimizer:
    """
    Utility function untuk membuat database optimizer
    
    Args:
        config: Database configuration (optional)
    
    Returns:
        DatabaseOptimizer instance yang sudah di-initialize
    """
    
    if config is None:
        config = DatabaseConfig()
    
    optimizer = DatabaseOptimizer(config)
    await optimizer.initialize()
    
    return optimizer

# Example usage dan testing
if __name__ == "__main__":
    async def test_database_optimizer():
        """Test database optimizer functionality"""
        
        # Create config
        config = DatabaseConfig(
            host="localhost",
            database="test_db",
            min_connections=5,
            max_connections=20,
            enable_caching=True,
            slow_query_threshold=0.5
        )
        
        # Create optimizer
        optimizer = await create_database_optimizer(config)
        
        try:
            # Test queries
            test_queries = [
                ("SELECT COUNT(*) FROM projects", ()),
                ("SELECT * FROM projects WHERE status = $1", ("active",)),
                ("SELECT p.*, u.username FROM projects p JOIN users u ON p.user_id = u.id", ())
            ]
            
            for query, params in test_queries:
                print(f"Executing: {query}")
                result = await optimizer.execute_query(query, params)
                print(f"Result: {len(result)} rows")
                await asyncio.sleep(0.1)
            
            # Get performance report
            report = await optimizer.get_performance_report()
            print(f"Performance Report: {json.dumps(report, indent=2, default=str)}")
            
            # Export slow query log
            await optimizer.export_slow_query_log("slow_queries.json")
            
        finally:
            await optimizer.close()

class SlowQueryAnalyzer:
    """Analyzer untuk slow query identification dan optimization"""
    
    def __init__(self, threshold: float = 1.0):
        self.threshold = threshold
        self.slow_queries = []
        self.query_patterns = defaultdict(list)
    
    def add_slow_query(self, query: str, execution_time: float, params: Tuple = ()):
        """Add slow query untuk analysis"""
        if execution_time > self.threshold:
            query_info = {
                'query': query,
                'execution_time': execution_time,
                'params': params,
                'timestamp': datetime.now(),
                'query_pattern': self._extract_query_pattern(query)
            }
            self.slow_queries.append(query_info)
            self.query_patterns[query_info['query_pattern']].append(query_info)
    
    def _extract_query_pattern(self, query: str) -> str:
        """Extract query pattern untuk grouping"""
        # Remove specific values, keep structure
        import re
        pattern = re.sub(r'\$\d+', '?', query)
        pattern = re.sub(r"'[^']*'", '?', pattern)
        pattern = re.sub(r'\d+', '?', pattern)
        return pattern.strip()
    
    def get_slow_query_report(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slow query report"""
        # Sort by execution time
        sorted_queries = sorted(self.slow_queries, key=lambda x: x['execution_time'], reverse=True)
        
        report = []
        for query in sorted_queries[:limit]:
            report.append({
                'query': query['query'],
                'execution_time': round(query['execution_time'], 3),
                'params': query['params'],
                'timestamp': query['timestamp'].isoformat(),
                'pattern_frequency': len(self.query_patterns[query['query_pattern']])
            })
        
        return report
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get optimization recommendations berdasarkan slow query patterns"""
        recommendations = []
        
        # Analyze patterns
        for pattern, queries in self.query_patterns.items():
            if len(queries) > 5:  # Frequent pattern
                avg_time = sum(q['execution_time'] for q in queries) / len(queries)
                recommendations.append(
                    f"Query pattern '{pattern[:50]}...' executed {len(queries)} times "
                    f"with avg time {avg_time:.2f}s - consider adding index"
                )
        
        # Check for missing indexes
        for query in self.slow_queries[-10:]:  # Check recent slow queries
            query_text = query['query'].lower()
            if 'where' in query_text and 'join' in query_text:
                recommendations.append(
                    f"Query with WHERE and JOIN clauses may benefit from composite indexes: "
                    f"{query['query'][:60]}..."
                )
        
        return recommendations[:10]  # Limit recommendations
    
    def clear_old_queries(self, days: int = 7):
        """Clear queries older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        self.slow_queries = [q for q in self.slow_queries if q['timestamp'] > cutoff_date]
        
        # Clean up patterns
        for pattern in list(self.query_patterns.keys()):
            self.query_patterns[pattern] = [
                q for q in self.query_patterns[pattern] if q['timestamp'] > cutoff_date
            ]
            if not self.query_patterns[pattern]:
                del self.query_patterns[pattern]
    
    
# Example usage dan testing
if __name__ == "__main__":
    async def test_database_optimizer():
        """Test database optimizer functionality"""
        
        # Create config
        config = DatabaseConfig(
            host="localhost",
            database="test_db",
            min_connections=5,
            max_connections=20,
            enable_caching=True,
            slow_query_threshold=0.5
        )
        
        # Create optimizer
        optimizer = await create_database_optimizer(config)
        
        try:
            # Test queries
            test_queries = [
                ("SELECT COUNT(*) FROM projects", ()),
                ("SELECT * FROM projects WHERE status = $1", ("active",)),
                ("SELECT p.*, u.username FROM projects p JOIN users u ON p.user_id = u.id", ())
            ]
            
            for query, params in test_queries:
                print(f"Executing: {query}")
                result = await optimizer.execute_query(query, params)
                print(f"Result: {len(result)} rows")
                await asyncio.sleep(0.1)
            
            # Get performance report
            report = await optimizer.get_performance_report()
            print(f"Performance Report: {json.dumps(report, indent=2, default=str)}")
            
            # Export slow query log
            await optimizer.export_slow_query_log("slow_queries.json")
            
        finally:
            await optimizer.close()
    
    # Run test
    asyncio.run(test_database_optimizer())