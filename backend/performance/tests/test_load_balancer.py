"""
Unit tests untuk Load Balancer dan Auto-scaling System
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from load_balancer import (
    LoadBalancer, ServerInstance, LoadBalancingMetrics, 
    HealthChecker, AutoScaler, LoadBalancingAlgorithm,
    create_load_balancer_pool
)

class TestServerInstance:
    """Test ServerInstance class"""
    
    def test_server_instance_creation(self):
        """Test creating server instance"""
        server = ServerInstance(
            id="server-1",
            host="localhost",
            port=8080,
            weight=1.0,
            max_connections=100
        )
        
        assert server.id == "server-1"
        assert server.host == "localhost"
        assert server.port == 8080
        assert server.weight == 1.0
        assert server.max_connections == 100
        assert server.current_connections == 0
        assert server.is_healthy is True
        assert server.active is True
    
    def test_server_instance_status(self):
        """Test server instance status methods"""
        server = ServerInstance("server-1", "localhost", 8080)
        
        # Test connection management
        server.increment_connections()
        assert server.current_connections == 1
        
        server.decrement_connections()
        assert server.current_connections == 0
        
        # Test health status
        server.set_healthy(False)
        assert server.is_healthy is False
        
        server.set_healthy(True)
        assert server.is_healthy is True
    
    def test_server_instance_utilization(self):
        """Test server utilization calculation"""
        server = ServerInstance("server-1", "localhost", 8080, max_connections=100)
        
        # Test utilization with no connections
        assert server.get_utilization() == 0.0
        
        # Test utilization with connections
        server.current_connections = 50
        assert server.get_utilization() == 0.5
        
        # Test utilization at max
        server.current_connections = 100
        assert server.get_utilization() == 1.0

class TestLoadBalancingMetrics:
    """Test LoadBalancingMetrics class"""
    
    def test_metrics_creation(self):
        """Test creating metrics instance"""
        metrics = LoadBalancingMetrics()
        
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.avg_response_time == 0.0
        assert metrics.server_count == 0
    
    def test_metrics_recording(self):
        """Test recording metrics"""
        metrics = LoadBalancingMetrics()
        
        # Record successful request
        metrics.record_request(success=True, response_time=0.5)
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
        assert metrics.failed_requests == 0
        assert metrics.avg_response_time == 0.5
        
        # Record failed request
        metrics.record_request(success=False, response_time=1.0)
        assert metrics.total_requests == 2
        assert metrics.successful_requests == 1
        assert metrics.failed_requests == 1
        assert metrics.avg_response_time == 0.75  # Average of 0.5 and 1.0
    
    def test_metrics_success_rate(self):
        """Test success rate calculation"""
        metrics = LoadBalancingMetrics()
        
        # No requests yet
        assert metrics.get_success_rate() == 0.0
        
        # Add requests
        metrics.record_request(True, 0.1)
        metrics.record_request(True, 0.2)
        metrics.record_request(False, 0.3)
        
        assert metrics.get_success_rate() == 2/3 * 100  # 66.67%

class TestHealthChecker:
    """Test HealthChecker class"""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check"""
        server = ServerInstance("server-1", "localhost", 8080)
        checker = HealthChecker(timeout=5, retry_count=3)
        
        # Mock successful health check
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="OK")
            
            mock_get.return_value = AsyncMock()
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            
            result = await checker.check_health(server)
            assert result is True
            assert server.is_healthy is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test failed health check"""
        server = ServerInstance("server-1", "localhost", 8080)
        checker = HealthChecker(timeout=5, retry_count=1)
        
        # Mock failed health check
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            
            result = await checker.check_health(server)
            assert result is False
            assert server.is_healthy is False
    
    @pytest.mark.asyncio
    async def test_health_check_with_retry(self):
        """Test health check with retry logic"""
        server = ServerInstance("server-1", "localhost", 8080)
        checker = HealthChecker(timeout=5, retry_count=3)
        
        # Mock failing then succeeding
        with patch('aiohttp.ClientSession.get') as mock_get:
            # First two calls fail, third succeeds
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="OK")
            
            mock_success = AsyncMock()
            mock_success.__aenter__ = AsyncMock(return_value=mock_response)
            
            mock_get.side_effect = [
                Exception("Connection failed"),
                Exception("Timeout"),
                mock_success
            ]
            
            result = await checker.check_health(server)
            # Should succeed on retry
            assert result is True

class TestAutoScaler:
    """Test AutoScaler class"""
    
    def test_auto_scaler_creation(self):
        """Test creating auto scaler"""
        scaler = AutoScaler(
            min_instances=2,
            max_instances=10,
            scale_up_threshold=80.0,
            scale_down_threshold=20.0,
            scale_cooldown=300
        )
        
        assert scaler.min_instances == 2
        assert scaler.max_instances == 10
        assert scaler.scale_up_threshold == 80.0
        assert scaler.scale_down_threshold == 20.0
        assert scaler.scale_cooldown == 300
    
    def test_should_scale_up(self):
        """Test scale up decision"""
        scaler = AutoScaler(scale_up_threshold=70.0)
        
        # Test scale up needed
        metrics = LoadBalancingMetrics()
        metrics.avg_utilization = 80.0
        metrics.avg_response_time = 2.0
        
        result = scaler.should_scale_up(metrics, current_instances=3)
        assert result is True
        
        # Test scale up not needed
        metrics.avg_utilization = 50.0
        result = scaler.should_scale_up(metrics, current_instances=3)
        assert result is False
    
    def test_should_scale_down(self):
        """Test scale down decision"""
        scaler = AutoScaler(scale_down_threshold=30.0)
        
        # Test scale down needed
        metrics = LoadBalancingMetrics()
        metrics.avg_utilization = 20.0
        metrics.avg_response_time = 0.1
        
        result = scaler.should_scale_down(metrics, current_instances=5)
        assert result is True
        
        # Test scale down not needed
        metrics.avg_utilization = 50.0
        result = scaler.should_scale_down(metrics, current_instances=5)
        assert result is False
    
    def test_scale_recommendation(self):
        """Test scale recommendation calculation"""
        scaler = AutoScaler(
            min_instances=2,
            max_instances=10,
            scale_up_threshold=70.0,
            scale_down_threshold=30.0
        )
        
        # Test scale up recommendation
        metrics = LoadBalancingMetrics()
        metrics.avg_utilization = 80.0
        
        recommendation = scaler.get_scale_recommendation(metrics, current_instances=3)
        assert recommendation > 3  # Should recommend more instances
        assert scaler.min_instances <= recommendation <= scaler.max_instances
        
        # Test scale down recommendation
        metrics.avg_utilization = 20.0
        recommendation = scaler.get_scale_recommendation(metrics, current_instances=6)
        assert recommendation < 6  # Should recommend fewer instances

class TestLoadBalancer:
    """Test LoadBalancer class"""
    
    @pytest.fixture
    def sample_servers(self):
        """Create sample servers for testing"""
        return [
            ServerInstance("server-1", "localhost", 8081, weight=1.0),
            ServerInstance("server-2", "localhost", 8082, weight=2.0),
            ServerInstance("server-3", "localhost", 8083, weight=1.0)
        ]
    
    def test_load_balancer_creation(self, sample_servers):
        """Test creating load balancer"""
        lb = LoadBalancer(sample_servers, algorithm=LoadBalancingAlgorithm.LEAST_CONNECTIONS)
        
        assert len(lb.servers) == 3
        assert lb.algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS
        assert lb.health_check_interval == 30
        assert lb.metrics.total_requests == 0
    
    def test_add_remove_server(self, sample_servers):
        """Test adding and removing servers"""
        lb = LoadBalancer(sample_servers)
        
        # Add new server
        new_server = ServerInstance("server-4", "localhost", 8084)
        lb.add_server(new_server)
        assert len(lb.servers) == 4
        
        # Remove server
        lb.remove_server("server-2")
        assert len(lb.servers) == 3
        assert not any(s.server_id == "server-2" for s in lb.servers.values())
    
    def test_get_healthy_servers(self, sample_servers):
        """Test getting healthy servers"""
        lb = LoadBalancer(sample_servers)
        
        # Make one server unhealthy
        sample_servers[1].set_healthy(False)
        
        healthy_servers = lb.get_healthy_servers()
        assert len(healthy_servers) == 2
        assert all(s.is_healthy for s in healthy_servers)
    
    def test_round_robin_selection(self, sample_servers):
        """Test round robin server selection"""
        lb = LoadBalancer(sample_servers, algorithm=LoadBalancingAlgorithm.ROUND_ROBIN)
        
        # Test sequential selection
        server1 = lb._select_server_round_robin()
        server2 = lb._select_server_round_robin()
        server3 = lb._select_server_round_robin()
        server4 = lb._select_server_round_robin()  # Should wrap around
        
        assert server1 == sample_servers[0]
        assert server2 == sample_servers[1]
        assert server3 == sample_servers[2]
        assert server4 == sample_servers[0]  # Back to first
    
    def test_least_connections_selection(self, sample_servers):
        """Test least connections server selection"""
        lb = LoadBalancer(sample_servers, algorithm=LoadBalancingAlgorithm.LEAST_CONNECTIONS)
        
        # Add connections to some servers
        sample_servers[0].current_connections = 10
        sample_servers[1].current_connections = 5
        sample_servers[2].current_connections = 15
        
        # Should select server with least connections
        selected = lb._select_server_least_connections()
        assert selected == sample_servers[1]  # 5 connections
    
    def test_weighted_round_robin_selection(self, sample_servers):
        """Test weighted round robin server selection"""
        lb = LoadBalancer(sample_servers, algorithm=LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN)
        
        # Select multiple servers and check distribution
        selections = []
        for _ in range(100):  # 100 selections for better statistical distribution
            server = lb._select_server_weighted_round_robin()
            if server:
                selections.append(server.server_id)
        
        # Check that server-2 (weight=2.0) is selected more often
        server1_count = selections.count("server-1")
        server2_count = selections.count("server-2")
        server3_count = selections.count("server-3")
        
        # With weighted round robin, server-2 should have approximately 2x more selections
        assert server2_count > server1_count * 1.5  # server-2 should be selected significantly more
        assert server2_count > server3_count * 1.5
    
    @pytest.mark.asyncio
    async def test_route_request_success(self, sample_servers):
        """Test successful request routing"""
        lb = LoadBalancer(sample_servers)
        
        # Mock successful request
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"result": "success"})
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await lb.route_request("/api/test", {"data": "test"})
            
            assert result["status"] == "success"
            assert "response" in result
            assert result["server_id"] in [s.server_id for s in sample_servers]
    
    @pytest.mark.asyncio
    async def test_route_request_failure(self, sample_servers):
        """Test failed request routing"""
        lb = LoadBalancer(sample_servers)
        
        # Mock failed request
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = Exception("Connection failed")
            
            result = await lb.route_request("/api/test", {"data": "test"})
            
            assert result["status"] == "error"
            assert "error" in result
    
    def test_get_metrics(self, sample_servers):
        """Test getting load balancer metrics"""
        lb = LoadBalancer(sample_servers)
        
        # Record some requests
        lb.metrics.record_request(True, 0.5)
        lb.metrics.record_request(False, 1.0)
        lb.metrics.record_request(True, 0.3)
        
        metrics = lb.get_metrics()
        
        assert metrics["total_requests"] == 3
        assert metrics["successful_requests"] == 2
        assert metrics["failed_requests"] == 1
        assert metrics["success_rate"] == pytest.approx(66.67, rel=1e-2)
        assert metrics["avg_response_time"] == pytest.approx(0.6, rel=1e-2)

class TestLoadBalancerIntegration:
    """Integration tests untuk load balancer"""
    
    @pytest.mark.asyncio
    async def test_load_balancer_with_health_checks(self):
        """Test load balancer with health checking"""
        servers = [
            ServerInstance("server-1", "localhost", 8081),
            ServerInstance("server-2", "localhost", 8082),
            ServerInstance("server-3", "localhost", 8083)
        ]
        
        lb = LoadBalancer(servers, health_check_interval=1)  # Fast health checks for testing
        
        # Mock health check responses
        with patch.object(lb.health_checker, 'check_server_health') as mock_health:
            # First server healthy, others not
            mock_health.side_effect = [
                True,   # server-1 healthy
                False,  # server-2 unhealthy
                False   # server-3 unhealthy
            ]
            
            # Perform health checks manually
            for server in servers:
                await lb.health_checker.check_server_health(server)
            
            # Only server-1 should be healthy
            healthy_servers = lb.get_healthy_servers()
            assert len(healthy_servers) == 1
            assert healthy_servers[0].server_id == "server-1"
    
    @pytest.mark.asyncio
    async def test_create_load_balancer_pool(self):
        """Test creating load balancer pool"""
        servers_config = [
            {"server_id": "server-1", "host": "localhost", "port": 8081, "weight": 1.0},
            {"server_id": "server-2", "host": "localhost", "port": 8082, "weight": 2.0},
            {"server_id": "server-3", "host": "localhost", "port": 8083, "weight": 1.0}
        ]
        
        lb = await create_load_balancer_pool(
            servers_config=servers_config,
            algorithm="least_connections",
            enable_auto_scaling=True
        )
        
        assert len(lb.servers) == 3
        assert lb.algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS
        assert lb.auto_scaler is not None

if __name__ == "__main__":
    pytest.main([__file__])