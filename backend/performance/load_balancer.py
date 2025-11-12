"""
Load Balancer dan Auto-scaling System untuk SANGKURIANG
Mengimplementasikan load balancing cerdas dengan health monitoring
"""

import asyncio
import logging
import time
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import aiohttp
from redis import asyncio as aioredis
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServerStatus(Enum):
    """Status server untuk load balancing"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    OVERLOADED = "overloaded"
    MAINTENANCE = "maintenance"

class LoadBalancingAlgorithm(Enum):
    """Algoritma load balancing yang tersedia"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    IP_HASH = "ip_hash"
    LEAST_RESPONSE_TIME = "least_response_time"

@dataclass
class ServerInstance:
    """Representasi instance server"""
    server_id: str = None
    host: str = "localhost"
    port: int = 8080
    weight: float = 1.0
    max_connections: int = 1000
    current_connections: int = 0
    status: ServerStatus = ServerStatus.HEALTHY
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    last_health_check: datetime = field(default_factory=datetime.now)
    error_count: int = 0
    total_requests: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    is_healthy: bool = True
    active: bool = True
    id: str = None
    
    def __post_init__(self):
        if self.server_id is None:
            self.server_id = self.id or f"server-{self.host}:{self.port}"
    
    def increment_connections(self):
        """Increment connection count"""
        self.current_connections += 1
    
    def decrement_connections(self):
        """Decrement connection count"""
        if self.current_connections > 0:
            self.current_connections -= 1
    
    def set_healthy(self, healthy: bool):
        """Set server health status"""
        self.is_healthy = healthy
    
    def get_utilization(self) -> float:
        """Get server utilization percentage"""
        if self.max_connections == 0:
            return 0.0
        return self.current_connections / self.max_connections
    
    @property
    def average_response_time(self) -> float:
        """Rata-rata response time"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    @property
    def is_available(self) -> bool:
        """Cek apakah server tersedia"""
        return (self.status == ServerStatus.HEALTHY and 
                self.current_connections < self.max_connections)

@dataclass
class LoadBalancingMetrics:
    """Metrik load balancing"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    server_distribution: Dict[str, int] = field(default_factory=dict)
    peak_load_time: Optional[datetime] = None
    auto_scaling_events: int = 0
    
    def record_request(self, success: bool, response_time: float):
        """Record request with success/failure and response time"""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        # Update average response time
        if self.total_requests == 1:
            self.average_response_time = response_time
        else:
            self.average_response_time = (self.average_response_time * (self.total_requests - 1) + response_time) / self.total_requests
    
    def get_success_rate(self) -> float:
        """Get success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def avg_response_time(self) -> float:
        """Average response time (alias for compatibility)"""
        return self.average_response_time
    
    @avg_response_time.setter
    def avg_response_time(self, value: float):
        """Setter for avg_response_time"""
        self.average_response_time = value
    
    @property
    def avg_utilization(self) -> float:
        """Average utilization (for compatibility with tests)"""
        return getattr(self, '_avg_utilization', 0.0)
    
    @avg_utilization.setter
    def avg_utilization(self, value: float):
        """Set average utilization"""
        self._avg_utilization = value

class HealthChecker:
    """Health checker untuk monitoring server"""
    
    def __init__(self, check_interval: int = 30, timeout: int = 5):
        self.check_interval = check_interval
        self.timeout = timeout
        self.running = False
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def start(self):
        """Mulai health checking"""
        self.running = True
        self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        logger.info("Health checker started")
    
    async def stop(self):
        """Hentikan health checking"""
        self.running = False
        if self._session:
            await self._session.close()
        logger.info("Health checker stopped")
    
    async def check_server_health(self, server: ServerInstance) -> bool:
        """Cek health dari single server"""
        try:
            start_time = time.time()
            url = f"http://{server.host}:{server.port}/health"
            
            async with self._session.get(url) as response:
                response_time = time.time() - start_time
                server.response_times.append(response_time)
                
                if response.status == 200:
                    health_data = await response.json()
                    
                    # Update server metrics
                    server.cpu_usage = health_data.get('cpu_usage', 0.0)
                    server.memory_usage = health_data.get('memory_usage', 0.0)
                    server.status = ServerStatus.HEALTHY
                    server.error_count = 0
                    
                    # Cek apakah server overloaded
                    if server.cpu_usage > 80.0 or server.memory_usage > 85.0:
                        server.status = ServerStatus.OVERLOADED
                        logger.warning(f"Server {server.server_id} is overloaded")
                    
                    return True
                else:
                    server.error_count += 1
                    if server.error_count >= 3:
                        server.status = ServerStatus.UNHEALTHY
                    return False
                    
        except Exception as e:
            logger.error(f"Health check failed for server {server.server_id}: {e}")
            server.error_count += 1
            if server.error_count >= 3:
                server.status = ServerStatus.UNHEALTHY
            return False

class AutoScaler:
    """Auto-scaling system untuk menambah/mengurangi server instances"""
    
    def __init__(self, 
                 min_instances: int = 2,
                 max_instances: int = 10,
                 scale_up_threshold: float = 75.0,
                 scale_down_threshold: float = 25.0,
                 scale_cooldown: int = 300):
        self.min_instances = min_instances
        self.max_instances = max_instances
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold
        self.scale_cooldown = scale_cooldown
        self.last_scale_event = datetime.min
        self.scaling_in_progress = False
        
        logger.info(f"AutoScaler initialized: min={min_instances}, max={max_instances}")
    
    def should_scale_up(self, metrics: LoadBalancingMetrics, current_instances: int) -> bool:
        """Determine if we should scale up"""
        if current_instances >= self.max_instances:
            return False
        
        # Check utilization threshold
        if hasattr(metrics, 'avg_utilization') and metrics.avg_utilization > self.scale_up_threshold:
            return True
        
        # Check response time threshold (only if utilization is also high)
        if (hasattr(metrics, 'avg_utilization') and metrics.avg_utilization > self.scale_up_threshold and
            hasattr(metrics, 'average_response_time') and metrics.average_response_time > 1.0):
            return True
            
        return False
    
    def should_scale_down(self, metrics: LoadBalancingMetrics, current_instances: int) -> bool:
        """Determine if we should scale down"""
        if current_instances <= self.min_instances:
            return False
        
        if hasattr(metrics, 'avg_utilization') and metrics.avg_utilization < self.scale_down_threshold:
            return True
            
        return False
    
    def get_scale_recommendation(self, metrics: LoadBalancingMetrics, current_instances: int) -> int:
        """Get recommended number of instances"""
        if self.should_scale_up(metrics, current_instances):
            return min(current_instances + 1, self.max_instances)
        elif self.should_scale_down(metrics, current_instances):
            return max(current_instances - 1, self.min_instances)
        else:
            return current_instances
    
    async def evaluate_scaling_need(self, 
                                    servers: List[ServerInstance],
                                    metrics: LoadBalancingMetrics) -> Optional[str]:
        """Evaluasi kebutuhan scaling"""
        
        if self.scaling_in_progress:
            return None
        
        now = datetime.now()
        if (now - self.last_scale_event).total_seconds() < self.cooldown_period:
            return None
        
        # Hitung average load
        total_load = sum(server.cpu_usage for server in servers if server.status == ServerStatus.HEALTHY)
        healthy_servers = [s for s in servers if s.status == ServerInstance.HEALTHY]
        
        if not healthy_servers:
            return "scale_up"
        
        avg_load = total_load / len(healthy_servers)
        current_instances = len(servers)
        
        # Scale up decision
        if avg_load > self.scale_up_threshold and current_instances < self.max_instances:
            self.scaling_in_progress = True
            self.last_scale_event = now
            metrics.auto_scaling_events += 1
            logger.info(f"Auto-scaling UP triggered. Avg load: {avg_load:.1f}%")
            return "scale_up"
        
        # Scale down decision
        elif avg_load < self.scale_down_threshold and current_instances > self.min_instances:
            self.scaling_in_progress = True
            self.last_scale_event = now
            metrics.auto_scaling_events += 1
            logger.info(f"Auto-scaling DOWN triggered. Avg load: {avg_load:.1f}%")
            return "scale_down"
        
        return None
    
    async def scale_up(self, load_balancer: 'LoadBalancer') -> bool:
        """Scale up - tambah server instance"""
        try:
            # Implementasi actual scaling logic di sini
            # Bisa integrate dengan cloud provider APIs (AWS, GCP, Azure)
            
            new_server_id = f"server-{int(time.time())}"
            new_server = ServerInstance(
                server_id=new_server_id,
                host=f"10.0.1.{len(load_balancer.servers) + 10}",  # Contoh IP
                port=8080,
                weight=1
            )
            
            load_balancer.add_server(new_server)
            logger.info(f"Scaled up: Added server {new_server_id}")
            self.scaling_in_progress = False
            return True
            
        except Exception as e:
            logger.error(f"Scale up failed: {e}")
            self.scaling_in_progress = False
            return False
    
    async def scale_down(self, load_balancer: 'LoadBalancer') -> bool:
        """Scale down - kurangi server instance"""
        try:
            # Pilih server dengan beban paling rendah
            available_servers = [s for s in load_balancer.servers.values() 
                               if s.current_connections == 0 and s.status == ServerStatus.HEALTHY]
            
            if not available_servers:
                logger.warning("No servers available for scale down")
                self.scaling_in_progress = False
                return False
            
            # Pilih server dengan response time tertinggi
            target_server = max(available_servers, key=lambda s: s.average_response_time)
            
            load_balancer.remove_server(target_server.server_id)
            logger.info(f"Scaled down: Removed server {target_server.server_id}")
            self.scaling_in_progress = False
            return True
            
        except Exception as e:
            logger.error(f"Scale down failed: {e}")
            self.scaling_in_progress = False
            return False

class LoadBalancer:
    """
    Advanced Load Balancer dengan auto-scaling dan health monitoring
    untuk SANGKURIANG Platform
    """
    
    def __init__(self, 
                 servers: List[ServerInstance] = None,
                 algorithm: LoadBalancingAlgorithm = LoadBalancingAlgorithm.LEAST_CONNECTIONS,
                 redis_url: str = "redis://localhost:6379",
                 enable_auto_scaling: bool = True,
                 health_check_interval: int = 30,
                 **kwargs):
        
        self.algorithm = algorithm
        self.servers: Dict[str, ServerInstance] = {}
        self.metrics = LoadBalancingMetrics()
        self.health_checker = HealthChecker(check_interval=health_check_interval)
        self.auto_scaler = AutoScaler() if enable_auto_scaling else None
        self.redis_client: Optional[redis.Redis] = None
        self.redis_url = redis_url
        self.health_check_interval = health_check_interval
        
        # Round-robin state
        self.round_robin_index = 0
        
        # Connection tracking
        self.client_connections: Dict[str, str] = {}  # client_ip -> server_id
        
        # Add initial servers if provided
        if servers:
            for server in servers:
                self.add_server(server)
        
        logger.info(f"LoadBalancer initialized with algorithm: {algorithm.value}")
    
    async def start(self):
        """Mulai load balancer dan komponen terkait"""
        try:
            # Connect to Redis untuk session persistence
            self.redis_client = aioredis.from_url(self.redis_url)
            await self.health_checker.start()
            logger.info("LoadBalancer started successfully")
        except Exception as e:
            logger.error(f"Failed to start LoadBalancer: {e}")
            raise
    
    async def stop(self):
        """Hentikan load balancer"""
        try:
            await self.health_checker.stop()
            if self.redis_client:
                await self.redis_client.close()
            logger.info("LoadBalancer stopped")
        except Exception as e:
            logger.error(f"Error stopping LoadBalancer: {e}")
    
    def add_server(self, server: ServerInstance):
        """Tambah server ke pool"""
        self.servers[server.server_id] = server
        logger.info(f"Added server {server.server_id} to pool")
    
    def remove_server(self, server_id: str):
        """Hapus server dari pool"""
        if server_id in self.servers:
            del self.servers[server_id]
            logger.info(f"Removed server {server_id} from pool")
    
    def get_next_server(self, client_ip: str = None) -> Optional[ServerInstance]:
        """Pilih server berdasarkan algoritma load balancing"""
        
        available_servers = [s for s in self.servers.values() if s.is_available]
        
        if not available_servers:
            logger.warning("No available servers")
            return None
        
        # Update metrics
        self.metrics.total_requests += 1
        
        selected_server = None
        
        if self.algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
            selected_server = self._round_robin_selection(available_servers)
        
        elif self.algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
            selected_server = self._least_connections_selection(available_servers)
        
        elif self.algorithm == LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN:
            selected_server = self._weighted_round_robin_selection(available_servers)
        
        elif self.algorithm == LoadBalancingAlgorithm.IP_HASH:
            selected_server = self._ip_hash_selection(available_servers, client_ip)
        
        elif self.algorithm == LoadBalancingAlgorithm.LEAST_RESPONSE_TIME:
            selected_server = self._least_response_time_selection(available_servers)
        
        if selected_server:
            selected_server.current_connections += 1
            selected_server.total_requests += 1
            
            # Track client connection untuk session persistence
            if client_ip:
                self.client_connections[client_ip] = selected_server.server_id
            
            # Update server distribution metrics
            if selected_server.server_id not in self.metrics.server_distribution:
                self.metrics.server_distribution[selected_server.server_id] = 0
            self.metrics.server_distribution[selected_server.server_id] += 1
        
        return selected_server
    
    def _round_robin_selection(self, servers: List[ServerInstance]) -> ServerInstance:
        """Round-robin selection"""
        server = servers[self.round_robin_index % len(servers)]
        self.round_robin_index += 1
        return server
    
    def _least_connections_selection(self, servers: List[ServerInstance]) -> ServerInstance:
        """Pilih server dengan koneksi paling sedikit"""
        return min(servers, key=lambda s: s.current_connections)
    
    def _weighted_round_robin_selection(self, servers: List[ServerInstance]) -> ServerInstance:
        """Weighted round-robin selection"""
        # Implementasi weighted round-robin
        total_weight = sum(server.weight for server in servers)
        random_weight = random.randint(1, total_weight)
        
        current_weight = 0
        for server in servers:
            current_weight += server.weight
            if current_weight >= random_weight:
                return server
        
        return servers[-1]
    
    def _ip_hash_selection(self, servers: List[ServerInstance], client_ip: str) -> ServerInstance:
        """IP hash selection untuk session persistence"""
        if not client_ip:
            return self._round_robin_selection(servers)
        
        # Hash IP address
        ip_hash = hash(client_ip) % len(servers)
        return servers[ip_hash]
    
    def _least_response_time_selection(self, servers: List[ServerInstance]) -> ServerInstance:
        """Pilih server dengan response time tercepat"""
        return min(servers, key=lambda s: s.average_response_time)
    
    def release_connection(self, server_id: str):
        """Lepas koneksi dari server"""
        if server_id in self.servers:
            server = self.servers[server_id]
            if server.current_connections > 0:
                server.current_connections -= 1
    
    async def perform_health_checks(self):
        """Lakukan health check untuk semua server"""
        tasks = []
        for server in self.servers.values():
            if server.status != ServerStatus.MAINTENANCE:
                tasks.append(self.health_checker.check_server_health(server))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def update_metrics(self):
        """Update metrics dan lakukan auto-scaling jika diperlukan"""
        try:
            # Update average response time
            all_response_times = []
            for server in self.servers.values():
                if server.response_times:
                    all_response_times.extend(server.response_times)
            
            if all_response_times:
                self.metrics.average_response_time = sum(all_response_times) / len(all_response_times)
            
            # Evaluasi auto-scaling
            if self.auto_scaler:
                scaling_action = await self.auto_scaler.evaluate_scaling_need(
                    list(self.servers.values()), 
                    self.metrics
                )
                
                if scaling_action == "scale_up":
                    await self.auto_scaler.scale_up(self)
                elif scaling_action == "scale_down":
                    await self.auto_scaler.scale_down(self)
            
            # Track peak load time
            if self.metrics.server_distribution:
                total_requests = sum(self.metrics.server_distribution.values())
                if total_requests > 1000:  # Threshold untuk peak load
                    self.metrics.peak_load_time = datetime.now()
        
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Dapatkan current metrics"""
        return {
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "avg_response_time": self.metrics.average_response_time,
            "success_rate": self.metrics.get_success_rate(),
            "server_distribution": self.metrics.server_distribution,
            "peak_load_time": self.metrics.peak_load_time.isoformat() if self.metrics.peak_load_time else None,
            "auto_scaling_events": self.metrics.auto_scaling_events,
            "active_servers": len([s for s in self.servers.values() if s.is_available]),
            "total_servers": len(self.servers)
        }
    
    def get_healthy_servers(self) -> List[ServerInstance]:
        """Get list of healthy servers"""
        return [s for s in self.servers.values() if s.is_healthy and s.is_available]
    
    def _select_server_round_robin(self, servers: List[ServerInstance] = None) -> Optional[ServerInstance]:
        """Round-robin selection for testing"""
        if servers is None:
            servers = list(self.servers.values())
        available_servers = [s for s in servers if s.is_available]
        if not available_servers:
            return None
        server = available_servers[self.round_robin_index % len(available_servers)]
        self.round_robin_index += 1
        return server
    
    def _select_server_least_connections(self, servers: List[ServerInstance] = None) -> Optional[ServerInstance]:
        """Least connections selection for testing"""
        if servers is None:
            servers = list(self.servers.values())
        available_servers = [s for s in servers if s.is_available]
        if not available_servers:
            return None
        return min(available_servers, key=lambda s: s.current_connections)
    
    def _select_server_weighted_round_robin(self, servers: List[ServerInstance] = None) -> Optional[ServerInstance]:
        """Weighted round-robin selection for testing"""
        if servers is None:
            servers = list(self.servers.values())
        available_servers = [s for s in servers if s.is_available]
        if not available_servers:
            return None
        total_weight = sum(server.weight for server in available_servers)
        random_weight = random.randint(1, int(total_weight))
        current_weight = 0
        for server in available_servers:
            current_weight += server.weight
            if current_weight >= random_weight:
                return server
        return available_servers[-1]
    
    async def route_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate server"""
        server = self.get_next_server()
        if not server:
            return {"status": "error", "error": "No available servers"}
        
        try:
            # Simulate request processing
            server.increment_connections()
            
            # Simulate actual HTTP request processing
            async with aiohttp.ClientSession() as session:
                url = f"http://{server.host}:{server.port}{endpoint}"
                async with session.post(url, json=data) as response:
                    response_data = await response.json()
                    
                    # Record success
                    self.metrics.record_request(success=True, response_time=0.1)
                    server.decrement_connections()
                    
                    return {
                        "status": "success",
                        "response": response_data,
                        "server_id": server.server_id
                    }
        except Exception as e:
            server.decrement_connections()
            self.metrics.record_request(success=False, response_time=0.0)
            return {"status": "error", "error": str(e)}
    
    def _select_server_round_robin(self) -> Optional[ServerInstance]:
        """Select server using round robin"""
        healthy_servers = self.get_healthy_servers()
        if not healthy_servers:
            return None
        
        server = healthy_servers[self.round_robin_index % len(healthy_servers)]
        self.round_robin_index += 1
        return server
    
    def _select_server_least_connections(self) -> Optional[ServerInstance]:
        """Select server with least connections"""
        healthy_servers = self.get_healthy_servers()
        if not healthy_servers:
            return None
        return min(healthy_servers, key=lambda s: s.current_connections)
    
    def _select_server_weighted_round_robin(self) -> Optional[ServerInstance]:
        """Select server using weighted round robin"""
        healthy_servers = self.get_healthy_servers()
        if not healthy_servers:
            return None
        
        total_weight = sum(server.weight for server in healthy_servers)
        random_weight = random.randint(1, total_weight)
        
        current_weight = 0
        for server in healthy_servers:
            current_weight += server.weight
            if current_weight >= random_weight:
                return server
        
        return healthy_servers[-1]
    
    def get_server_status(self) -> Dict[str, Any]:
        """Dapatkan status semua server"""
        return {
            server_id: {
                "host": server.host,
                "port": server.port,
                "status": server.status.value,
                "current_connections": server.current_connections,
                "weight": server.weight,
                "cpu_usage": server.cpu_usage,
                "memory_usage": server.memory_usage,
                "average_response_time": server.average_response_time,
                "total_requests": server.total_requests,
                "error_count": server.error_count
            }
            for server_id, server in self.servers.items()
        }

# Utility functions untuk integration
async def create_load_balancer_pool(
    servers_config: List[Dict[str, Any]],
    algorithm: str = "least_connections",
    enable_auto_scaling: bool = True
) -> LoadBalancer:
    """
    Utility function untuk membuat load balancer pool
    
    Args:
        servers_config: List konfigurasi server
        algorithm: Algoritma load balancing
        enable_auto_scaling: Enable auto-scaling feature
    
    Returns:
        LoadBalancer instance yang sudah dikonfigurasi
    """
    
    # Parse algorithm
    algo_map = {
        "round_robin": LoadBalancingAlgorithm.ROUND_ROBIN,
        "least_connections": LoadBalancingAlgorithm.LEAST_CONNECTIONS,
        "weighted_round_robin": LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN,
        "ip_hash": LoadBalancingAlgorithm.IP_HASH,
        "least_response_time": LoadBalancingAlgorithm.LEAST_RESPONSE_TIME
    }
    
    algorithm_enum = algo_map.get(algorithm, LoadBalancingAlgorithm.LEAST_CONNECTIONS)
    
    # Create load balancer
    load_balancer = LoadBalancer(
        servers=[],
        algorithm=algorithm_enum,
        enable_auto_scaling=enable_auto_scaling
    )
    
    # Add servers
    for server_config in servers_config:
        server = ServerInstance(
            server_id=server_config["server_id"],
            host=server_config["host"],
            port=server_config["port"],
            weight=server_config.get("weight", 1),
            max_connections=server_config.get("max_connections", 1000)
        )
        load_balancer.add_server(server)
    
    # Start load balancer
    await load_balancer.start()
    
    return load_balancer

# Example usage dan testing
if __name__ == "__main__":
    async def test_load_balancer():
        """Test load balancer functionality"""
        
        # Contoh konfigurasi server
        servers_config = [
            {"server_id": "web-01", "host": "127.0.0.1", "port": 8001, "weight": 2},
            {"server_id": "web-02", "host": "127.0.0.1", "port": 8002, "weight": 1},
            {"server_id": "web-03", "host": "127.0.0.1", "port": 8003, "weight": 1}
        ]
        
        # Create load balancer
        lb = await create_load_balancer_pool(
            servers_config=servers_config,
            algorithm="least_connections",
            enable_auto_scaling=True
        )
        
        # Simulate requests
        for i in range(10):
            server = lb.get_next_server(f"client-{i}")
            if server:
                print(f"Request {i}: Routed to {server.server_id}")
                # Simulate request processing
                await asyncio.sleep(0.1)
                lb.release_connection(server.server_id)
        
        # Print metrics
        metrics = lb.get_metrics()
        print(f"Metrics: {json.dumps(metrics, indent=2)}")
        
        # Stop load balancer
        await lb.stop()
    
    # Run test
    asyncio.run(test_load_balancer())