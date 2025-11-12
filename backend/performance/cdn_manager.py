"""
CDN Integration System untuk SANGKURIANG
Mengimplementasikan content delivery network dengan intelligent caching dan optimization
"""

import asyncio
import logging
import time
import hashlib
import json
import aiofiles
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp
from collections import deque

# Handle redis import conflict
try:
    import redis.asyncio as redis
except ImportError:
    try:
        import aioredis as redis
    except ImportError:
        redis = None

from collections import defaultdict
import mimetypes
import gzip
import brotli
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CDNConfig:
    """CDN Configuration"""
    # Cache settings
    cache_ttl: int = 86400  # 24 hours default
    browser_cache_ttl: int = 3600  # 1 hour
    cdn_cache_ttl: int = 86400  # 24 hours
    
    # Compression settings
    enable_gzip: bool = True
    enable_brotli: bool = True
    compression_threshold: int = 1024  # 1KB
    
    # Performance settings
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    chunk_size: int = 64 * 1024  # 64KB chunks
    
    # Storage settings
    storage_path: str = "./cdn_cache"
    enable_persistent_cache: bool = True
    
    # Network settings
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Security settings
    enable_cors: bool = True
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    enable_hotlink_protection: bool = False
    allowed_referrers: List[str] = field(default_factory=list)

@dataclass
class CacheEntry:
    """Cache entry metadata"""
    key: str
    file_path: str
    content_type: str
    file_size: int
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    etag: str = ""
    compression_type: Optional[str] = None
    compressed_size: Optional[int] = None

@dataclass
class CDNMetrics:
    """CDN performance metrics"""
    cache_hits: int = 0
    cache_misses: int = 0
    cache_evictions: int = 0
    total_requests: int = 0
    bytes_served: int = 0
    bytes_saved_by_compression: int = 0
    compression_ratio: float = 0.0
    average_response_time: float = 0.0
    edge_server_hits: Dict[str, int] = field(default_factory=dict)
    popular_files: Dict[str, int] = field(default_factory=dict)

class FileCompressor:
    """File compression dengan gzip dan brotli"""
    
    def __init__(self, config: CDNConfig):
        self.config = config
        self.compression_stats = {
            'gzip_compressed': 0,
            'brotli_compressed': 0,
            'compression_saved_bytes': 0
        }
    
    async def compress_content(self, content: bytes, content_type: str) -> Tuple[bytes, str]:
        """
        Compress content based on type and size
        
        Returns:
            Tuple of (compressed_content, compression_type)
        """
        if len(content) < self.config.compression_threshold:
            return content, "none"
        
        # Don't compress already compressed formats
        if self._is_already_compressed(content_type):
            return content, "none"
        
        try:
            # Try brotli first (better compression)
            if self.config.enable_brotli and self._should_compress_brotli(content_type):
                compressed = brotli.compress(content, quality=6)
                if len(compressed) < len(content) * 0.9:  # At least 10% reduction
                    self.compression_stats['brotli_compressed'] += 1
                    self.compression_stats['compression_saved_bytes'] += (len(content) - len(compressed))
                    return compressed, "br"
            
            # Fallback to gzip
            if self.config.enable_gzip:
                compressed = gzip.compress(content, compresslevel=6)
                if len(compressed) < len(content) * 0.9:  # At least 10% reduction
                    self.compression_stats['gzip_compressed'] += 1
                    self.compression_stats['compression_saved_bytes'] += (len(content) - len(compressed))
                    return compressed, "gzip"
            
            return content, "none"
            
        except Exception as e:
            logger.error(f"Compression error: {e}")
            return content, "none"
    
    def _is_already_compressed(self, content_type: str) -> bool:
        """Check if content type is already compressed"""
        compressed_types = [
            'image/',
            'video/',
            'audio/',
            'application/zip',
            'application/gzip',
            'application/x-brotli',
            'application/pdf'
        ]
        return any(content_type.startswith(ct) for ct in compressed_types)
    
    def _should_compress_brotli(self, content_type: str) -> bool:
        """Check if content type should use brotli compression"""
        brotli_friendly_types = [
            'text/',
            'application/javascript',
            'application/json',
            'application/xml',
            'application/css'
        ]
        return any(content_type.startswith(ct) for ct in brotli_friendly_types)
    
    async def decompress_content(self, content: bytes, compression_type: str) -> bytes:
        """Decompress content"""
        try:
            if compression_type == "br":
                return brotli.decompress(content)
            elif compression_type == "gzip":
                return gzip.decompress(content)
            else:
                return content
        except Exception as e:
            logger.error(f"Decompression error: {e}")
            return content

class CacheManager:
    """Intelligent cache management dengan LRU dan TTL"""
    
    def __init__(self, config: CDNConfig, redis_client: Optional[redis.Redis] = None):
        self.config = config
        self.redis_client = redis_client
        self.cache_entries: Dict[str, CacheEntry] = {}
        self.access_log: deque = deque(maxlen=10000)
        self.cache_size = 0
        self.max_cache_size = 2 * 1024 * 1024 * 1024  # 2GB limit
        
        # Ensure cache directory exists
        Path(self.config.storage_path).mkdir(parents=True, exist_ok=True)
    
    def _generate_cache_key(self, file_path: str, params: Dict = None) -> str:
        """Generate cache key dari file path dan parameters"""
        key_string = file_path
        if params:
            key_string += json.dumps(params, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    async def get_cached_file(self, cache_key: str) -> Optional[CacheEntry]:
        """Get cached file jika tersedia"""
        
        # Check memory cache
        if cache_key in self.cache_entries:
            entry = self.cache_entries[cache_key]
            entry.last_accessed = datetime.now()
            entry.access_count += 1
            
            # Check if file still exists
            if os.path.exists(entry.file_path):
                return entry
            else:
                # Remove from cache if file doesn't exist
                del self.cache_entries[cache_key]
                self.cache_size -= entry.file_size
        
        # Check Redis cache jika tersedia
        if self.redis_client:
            try:
                cached_data = await self.redis_client.get(f"cdn:{cache_key}")
                if cached_data:
                    entry_data = json.loads(cached_data)
                    entry = CacheEntry(**entry_data)
                    
                    # Restore to memory cache
                    if os.path.exists(entry.file_path):
                        self.cache_entries[cache_key] = entry
                        self.cache_size += entry.file_size
                        return entry
            except Exception as e:
                logger.error(f"Redis cache get error: {e}")
        
        return None
    
    async def cache_file(self, cache_key: str, file_path: str, content_type: str, 
                        compressed_content: bytes, compression_type: str) -> CacheEntry:
        """Cache file dengan metadata"""
        
        # Create cache file path
        cache_file_path = os.path.join(self.config.storage_path, f"{cache_key}.cache")
        
        # Write compressed content to cache
        async with aiofiles.open(cache_file_path, 'wb') as f:
            await f.write(compressed_content)
        
        # Create cache entry
        entry = CacheEntry(
            key=cache_key,
            file_path=cache_file_path,
            content_type=content_type,
            file_size=len(compressed_content),
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=1,
            etag=f'"{cache_key}"',
            compression_type=compression_type if compression_type != "none" else None,
            compressed_size=len(compressed_content) if compression_type != "none" else None
        )
        
        # Add to memory cache
        self.cache_entries[cache_key] = entry
        self.cache_size += entry.file_size
        
        # Cache in Redis jika tersedia
        if self.redis_client:
            try:
                entry_data = {
                    'key': entry.key,
                    'file_path': entry.file_path,
                    'content_type': entry.content_type,
                    'file_size': entry.file_size,
                    'created_at': entry.created_at.isoformat(),
                    'etag': entry.etag,
                    'compression_type': entry.compression_type,
                    'compressed_size': entry.compressed_size
                }
                await self.redis_client.setex(
                    f"cdn:{cache_key}",
                    self.config.cache_ttl,
                    json.dumps(entry_data)
                )
            except Exception as e:
                logger.error(f"Redis cache set error: {e}")
        
        # Check cache size and evict jika perlu
        await self._evict_if_necessary()
        
        return entry
    
    async def _evict_if_necessary(self):
        """Evict cache entries jika cache terlalu besar"""
        if self.cache_size <= self.max_cache_size:
            return
        
        # Sort by last accessed time (LRU)
        sorted_entries = sorted(
            self.cache_entries.items(),
            key=lambda x: x[1].last_accessed
        )
        
        # Evict oldest entries
        evicted_count = 0
        for cache_key, entry in sorted_entries:
            if self.cache_size <= self.max_cache_size * 0.8:  # Target 80% capacity
                break
            
            # Remove from cache
            del self.cache_entries[cache_key]
            self.cache_size -= entry.file_size
            
            # Remove cache file
            try:
                if os.path.exists(entry.file_path):
                    os.remove(entry.file_path)
            except Exception as e:
                logger.error(f"Error removing cache file: {e}")
            
            # Remove from Redis
            if self.redis_client:
                try:
                    await self.redis_client.delete(f"cdn:{cache_key}")
                except Exception as e:
                    logger.error(f"Error removing Redis cache: {e}")
            
            evicted_count += 1
        
        logger.info(f"Evicted {evicted_count} cache entries")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cache_entries': len(self.cache_entries),
            'cache_size_mb': self.cache_size / (1024 * 1024),
            'max_cache_size_mb': self.max_cache_size / (1024 * 1024),
            'cache_utilization_percent': (self.cache_size / self.max_cache_size) * 100
        }

class EdgeServer:
    """Edge server untuk CDN dengan geographic distribution"""
    
    def __init__(self, server_id: str, region: str, host: str, priority: int = 1):
        self.server_id = server_id
        self.region = region
        self.host = host
        self.priority = priority
        self.is_healthy = True
        self.response_times = deque(maxlen=100)
        self.request_count = 0
        self.last_health_check = datetime.now()
    
    @property
    def average_response_time(self) -> float:
        """Get average response time"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

class CDNManager:
    """
    Main CDN management system untuk SANGKURIANG
    Menggabungkan caching, compression, dan edge server management
    """
    
    def __init__(self, config: CDNConfig = None):
        self.config = config or CDNConfig()
        self.cache_manager = CacheManager(self.config)
        self.compressor = FileCompressor(self.config)
        self.metrics = CDNMetrics()
        self.edge_servers: Dict[str, EdgeServer] = {}
        self.redis_client: Optional[redis.Redis] = None
        
        # Initialize Redis connection untuk distributed caching
        if self.config.enable_persistent_cache:
            self.redis_client = aioredis.from_url(
                "redis://localhost:6379/2",  # Use different DB for CDN
                encoding="utf-8",
                decode_responses=True
            )
            self.cache_manager.redis_client = self.redis_client
    
    async def start(self):
        """Start CDN manager"""
        try:
            # Add default edge servers
            default_servers = [
                EdgeServer("edge-jkt", "Jakarta", "edge-jkt.sangkuriang.id", 1),
                EdgeServer("edge-sby", "Surabaya", "edge-sby.sangkuriang.id", 2),
                EdgeServer("edge-bdg", "Bandung", "edge-bdg.sangkuriang.id", 2)
            ]
            
            for server in default_servers:
                self.add_edge_server(server)
            
            logger.info("CDN Manager started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start CDN Manager: {e}")
            raise
    
    async def stop(self):
        """Stop CDN manager"""
        try:
            if self.redis_client:
                await self.redis_client.close()
            logger.info("CDN Manager stopped")
        except Exception as e:
            logger.error(f"Error stopping CDN Manager: {e}")
    
    def add_edge_server(self, server: EdgeServer):
        """Add edge server ke pool"""
        self.edge_servers[server.server_id] = server
        logger.info(f"Added edge server: {server.server_id} ({server.region})")
    
    def get_optimal_edge_server(self, client_region: str = None) -> Optional[EdgeServer]:
        """Get optimal edge server untuk client region"""
        
        healthy_servers = [s for s in self.edge_servers.values() if s.is_healthy]
        
        if not healthy_servers:
            return None
        
        # Sort by priority and response time
        healthy_servers.sort(key=lambda s: (s.priority, s.average_response_time))
        
        # Try to match client region
        if client_region:
            regional_servers = [s for s in healthy_servers if s.region.lower() in client_region.lower()]
            if regional_servers:
                return regional_servers[0]
        
        # Return best server
        return healthy_servers[0]
    
    async def serve_content(self, file_path: str, client_region: str = None, 
                          params: Dict = None, headers: Dict = None) -> Optional[Dict[str, Any]]:
        """
        Serve content dengan full CDN optimization
        
        Returns:
            Dictionary dengan content dan metadata
        """
        
        start_time = time.time()
        self.metrics.total_requests += 1
        
        try:
            # Generate cache key
            cache_key = self.cache_manager._generate_cache_key(file_path, params)
            
            # Check cache
            cached_entry = await self.cache_manager.get_cached_file(cache_key)
            
            if cached_entry:
                self.metrics.cache_hits += 1
                
                # Read cached content
                async with aiofiles.open(cached_entry.file_path, 'rb') as f:
                    content = await f.read()
                
                # Decompress jika perlu
                if cached_entry.compression_type:
                    content = await self.compressor.decompress_content(
                        content, cached_entry.compression_type
                    )
                
                response_time = time.time() - start_time
                self.metrics.average_response_time = (
                    (self.metrics.average_response_time * (self.metrics.total_requests - 1) + response_time) 
                    / self.metrics.total_requests
                )
                
                return {
                    'content': content,
                    'content_type': cached_entry.content_type,
                    'etag': cached_entry.etag,
                    'cache_hit': True,
                    'compression': cached_entry.compression_type,
                    'response_time': response_time
                }
            
            # Cache miss - load original content
            self.metrics.cache_misses += 1
            
            # Get optimal edge server
            edge_server = self.get_optimal_edge_server(client_region)
            if edge_server:
                self.metrics.edge_server_hits[edge_server.server_id] = \
                    self.metrics.edge_server_hits.get(edge_server.server_id, 0) + 1
            
            # Load content dari origin atau file system
            content, content_type = await self._load_content(file_path)
            
            if content is None:
                return None
            
            # Compress content
            compressed_content, compression_type = await self.compressor.compress_content(
                content, content_type
            )
            
            # Cache the content
            cache_entry = await self.cache_manager.cache_file(
                cache_key, file_path, content_type, compressed_content, compression_type
            )
            
            # Update metrics
            self.metrics.bytes_served += len(content)
            if compression_type != "none":
                self.metrics.bytes_saved_by_compression += (len(content) - len(compressed_content))
            
            # Track popular files
            self.metrics.popular_files[file_path] = \
                self.metrics.popular_files.get(file_path, 0) + 1
            
            response_time = time.time() - start_time
            self.metrics.average_response_time = (
                (self.metrics.average_response_time * (self.metrics.total_requests - 1) + response_time) 
                / self.metrics.total_requests
            )
            
            return {
                'content': compressed_content if compression_type != "none" else content,
                'content_type': content_type,
                'etag': cache_entry.etag,
                'cache_hit': False,
                'compression': compression_type,
                'response_time': response_time
            }
            
        except Exception as e:
            logger.error(f"Error serving content: {e}")
            return None
    
    async def _load_content(self, file_path: str) -> Tuple[Optional[bytes], str]:
        """Load content dari file system atau origin"""
        
        try:
            # Try to load from local file system
            if os.path.exists(file_path):
                async with aiofiles.open(file_path, 'rb') as f:
                    content = await f.read()
                
                # Detect content type
                content_type, _ = mimetypes.guess_type(file_path)
                content_type = content_type or 'application/octet-stream'
                
                return content, content_type
            
            # If not found locally, could fetch from origin server
            # This would be implemented based on your origin server setup
            logger.warning(f"File not found: {file_path}")
            return None, ""
            
        except Exception as e:
            logger.error(f"Error loading content: {e}")
            return entry
    
    def get_file_stats(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file statistics"""
        cache_key = self._generate_cache_key(file_path)
        entry = self.cache_entries.get(cache_key)
        
        if entry:
            return {
                'cache_key': entry.key,
                'file_size': entry.file_size,
                'compressed_size': entry.compressed_size,
                'compression_ratio': (entry.file_size - (entry.compressed_size or entry.file_size)) / entry.file_size if entry.compressed_size else 0,
                'access_count': entry.access_count,
                'last_accessed': entry.last_accessed,
                'created_at': entry.created_at,
                'compression_type': entry.compression_type
            }
        return None
    
    async def invalidate_cache(self, file_path: str = None, pattern: str = None):
        """Invalidate cache entries"""
        
        if file_path:
            cache_key = self.cache_manager._generate_cache_key(file_path)
            if cache_key in self.cache_manager.cache_entries:
                entry = self.cache_manager.cache_entries[cache_key]
                
                # Remove cache file
                if os.path.exists(entry.file_path):
                    os.remove(entry.file_path)
                
                # Remove from cache
                del self.cache_manager.cache_entries[cache_key]
                self.cache_manager.cache_size -= entry.file_size
                
                # Remove from Redis
                if self.redis_client:
                    await self.redis_client.delete(f"cdn:{cache_key}")
                
                self.metrics.cache_evictions += 1
                logger.info(f"Invalidated cache for: {file_path}")
        
        elif pattern:
            # Invalidate by pattern (more complex implementation)
            keys_to_remove = []
            for cache_key, entry in self.cache_manager.cache_entries.items():
                if pattern in entry.file_path:
                    keys_to_remove.append(cache_key)
            
            for cache_key in keys_to_remove:
                await self.invalidate_cache(entry.file_path)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive CDN metrics"""
        
        total_requests = self.metrics.cache_hits + self.metrics.cache_misses
        cache_hit_rate = (self.metrics.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        compression_ratio = 0.0
        if self.metrics.bytes_served > 0:
            compression_ratio = (self.metrics.bytes_saved_by_compression / self.metrics.bytes_served) * 100
        
        return {
            'cache_metrics': {
                'hits': self.metrics.cache_hits,
                'misses': self.metrics.cache_misses,
                'hit_rate_percent': round(cache_hit_rate, 2),
                'evictions': self.metrics.cache_evictions
            },
            'performance_metrics': {
                'total_requests': self.metrics.total_requests,
                'bytes_served_mb': round(self.metrics.bytes_served / (1024 * 1024), 2),
                'bytes_saved_by_compression_mb': round(self.metrics.bytes_saved_by_compression / (1024 * 1024), 2),
                'compression_ratio_percent': round(compression_ratio, 2),
                'average_response_time_ms': round(self.metrics.average_response_time * 1000, 2)
            },
            'edge_servers': {
                server_id: {
                    'region': server.region,
                    'is_healthy': server.is_healthy,
                    'average_response_time_ms': round(server.average_response_time * 1000, 2),
                    'request_count': server.request_count
                }
                for server_id, server in self.edge_servers.items()
            },
            'cache_stats': self.cache_manager.get_cache_stats(),
            'popular_files': dict(sorted(self.metrics.popular_files.items(), 
                                       key=lambda x: x[1], reverse=True)[:10]),
            'generated_at': datetime.now().isoformat()
        }

# Utility functions
async def create_cdn_manager(config: CDNConfig = None) -> CDNManager:
    """
    Utility function untuk membuat CDN manager
    
    Args:
        config: CDN configuration (optional)
    
    Returns:
        CDNManager instance yang sudah di-initialize
    """
    
    manager = CDNManager(config)
    await manager.start()
    
    return manager

# Example usage dan testing
if __name__ == "__main__":
    async def test_cdn_manager():
        """Test CDN manager functionality"""
        
        # Create config
        config = CDNConfig(
            cache_ttl=3600,
            enable_gzip=True,
            enable_brotli=True,
            storage_path="./test_cdn_cache"
        )
        
        # Create CDN manager
        cdn = await create_cdn_manager(config)
        
        try:
            # Create test files
            test_files = [
                ("test.html", "<html><body>Hello World</body></html>", "text/html"),
                ("test.css", "body { margin: 0; padding: 0; }", "text/css"),
                ("test.js", "console.log('Hello World');", "application/javascript")
            ]
            
            for filename, content, content_type in test_files:
                async with aiofiles.open(filename, 'w') as f:
                    await f.write(content)
                
                # Serve content
                result = await cdn.serve_content(filename)
                if result:
                    print(f"Served {filename}: {len(result['content'])} bytes, "
                          f"cache_hit: {result['cache_hit']}, "
                          f"compression: {result['compression']}")
                
                # Serve again (should hit cache)
                result = await cdn.serve_content(filename)
                if result:
                    print(f"Second serve {filename}: cache_hit: {result['cache_hit']}")
            
            # Get metrics
            metrics = cdn.get_metrics()
            print(f"CDN Metrics: {json.dumps(metrics, indent=2, default=str)}")
            
            # Cleanup test files
            for filename, _, _ in test_files:
                if os.path.exists(filename):
                    os.remove(filename)
            
        finally:
            await cdn.stop()
    
    # Run test
    asyncio.run(test_cdn_manager())