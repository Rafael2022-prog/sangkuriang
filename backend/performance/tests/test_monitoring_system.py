"""
Unit tests untuk Monitoring dan Analytics System
"""

import pytest
import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Tambahkan parent directory ke path untuk import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import redis.asyncio as redis
except ImportError:
    try:
        import aioredis as redis
    except ImportError:
        redis = None

from monitoring_system import (
    MonitoringSystem, MetricsCollector, AlertManager, SystemMonitor,
    ApplicationMonitor, MonitoringDashboard, MetricData, AlertRule, Alert,
    MetricType, AlertLevel, create_monitoring_system
)

class TestMetricData:
    """Test MetricData class"""
    
    def test_metric_data_creation(self):
        """Test creating metric data"""
        metric = MetricData(
            name="test_metric",
            value=42.5,
            metric_type=MetricType.GAUGE,
            labels={"env": "test", "service": "api"}
        )
        
        assert metric.name == "test_metric"
        assert metric.value == 42.5
        assert metric.metric_type == MetricType.GAUGE
        assert metric.labels == {"env": "test", "service": "api"}
        assert isinstance(metric.timestamp, datetime)
    
    def test_metric_data_to_dict(self):
        """Test converting metric data to dictionary"""
        metric = MetricData(
            name="test_metric",
            value=42.5,
            metric_type=MetricType.GAUGE,
            labels={"env": "test"}
        )
        
        result = metric.to_dict()
        
        assert result['name'] == "test_metric"
        assert result['value'] == 42.5
        assert result['type'] == "gauge"
        assert result['labels'] == {"env": "test"}
        assert 'timestamp' in result

class TestAlertRule:
    """Test AlertRule class"""
    
    def test_alert_rule_creation(self):
        """Test creating alert rule"""
        rule = AlertRule(
            name="high_cpu",
            metric_name="cpu_usage",
            condition="greater_than",
            threshold=80.0,
            duration=300,
            level=AlertLevel.WARNING,
            message="CPU usage is high: {value:.1f}%"
        )
        
        assert rule.name == "high_cpu"
        assert rule.metric_name == "cpu_usage"
        assert rule.condition == "greater_than"
        assert rule.threshold == 80.0
        assert rule.duration == 300
        assert rule.level == AlertLevel.WARNING
        assert rule.enabled is True
    
    def test_alert_rule_evaluation_greater_than(self):
        """Test greater than condition evaluation"""
        rule = AlertRule(
            name="high_cpu",
            metric_name="cpu_usage",
            condition="greater_than",
            threshold=80.0,
            duration=60,
            level=AlertLevel.WARNING
        )
        
        # Value above threshold with duration met
        result = rule.evaluate(85.0, True)
        assert result == AlertLevel.WARNING
        
        # Value below threshold
        result = rule.evaluate(75.0, True)
        assert result is None
        
        # Duration not met
        result = rule.evaluate(85.0, False)
        assert result is None
    
    def test_alert_rule_evaluation_less_than(self):
        """Test less than condition evaluation"""
        rule = AlertRule(
            name="low_memory",
            metric_name="memory_available",
            condition="less_than",
            threshold=10.0,
            duration=60,
            level=AlertLevel.ERROR
        )
        
        # Value below threshold
        result = rule.evaluate(5.0, True)
        assert result == AlertLevel.ERROR
        
        # Value above threshold
        result = rule.evaluate(15.0, True)
        assert result is None
    
    def test_alert_rule_evaluation_equals(self):
        """Test equals condition evaluation"""
        rule = AlertRule(
            name="service_down",
            metric_name="service_status",
            condition="equals",
            threshold=0.0,
            duration=30,
            level=AlertLevel.CRITICAL
        )
        
        # Value equals threshold
        result = rule.evaluate(0.0, True)
        assert result == AlertLevel.CRITICAL
        
        # Value not equal
        result = rule.evaluate(1.0, True)
        assert result is None

class TestAlert:
    """Test Alert class"""
    
    def test_alert_creation(self):
        """Test creating alert"""
        alert = Alert(
            rule_name="high_cpu",
            level=AlertLevel.WARNING,
            message="CPU usage is high: 85.0%",
            value=85.0,
            threshold=80.0
        )
        
        assert alert.rule_name == "high_cpu"
        assert alert.level == AlertLevel.WARNING
        assert alert.message == "CPU usage is high: 85.0%"
        assert alert.value == 85.0
        assert alert.threshold == 80.0
        assert alert.acknowledged is False
        assert isinstance(alert.timestamp, datetime)
    
    def test_alert_to_dict(self):
        """Test converting alert to dictionary"""
        alert = Alert(
            rule_name="high_cpu",
            level=AlertLevel.WARNING,
            message="CPU usage is high: 85.0%",
            value=85.0,
            threshold=80.0
        )
        
        result = alert.to_dict()
        
        assert result['rule_name'] == "high_cpu"
        assert result['level'] == "warning"
        assert result['message'] == "CPU usage is high: 85.0%"
        assert result['value'] == 85.0
        assert result['threshold'] == 80.0
        assert result['acknowledged'] is False
        assert 'timestamp' in result

class TestMetricsCollector:
    """Test MetricsCollector class"""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        mock = Mock()
        mock.pipeline = Mock(return_value=Mock())
        return mock
    
    def test_metrics_collector_creation(self, mock_redis):
        """Test creating metrics collector"""
        collector = MetricsCollector(mock_redis)
        
        assert collector.redis_client == mock_redis
        assert collector.buffer_size == 1000
        assert collector.flush_interval == 60
        assert len(collector.metrics_buffer) == 0
    
    @pytest.mark.asyncio
    async def test_collect_metric(self, mock_redis):
        """Test collecting metric"""
        collector = MetricsCollector(mock_redis)
        
        metric = MetricData(
            name="test_metric",
            value=42.5,
            metric_type=MetricType.GAUGE
        )
        
        await collector.collect_metric(metric)
        
        assert len(collector.metrics_buffer) == 1
        assert collector.metrics_buffer[0] == metric
    
    @pytest.mark.asyncio
    async def test_flush_metrics(self, mock_redis):
        """Test flushing metrics"""
        collector = MetricsCollector(mock_redis)
        
        # Add some metrics
        for i in range(5):
            metric = MetricData(
                name=f"metric_{i}",
                value=float(i),
                metric_type=MetricType.COUNTER
            )
            await collector.collect_metric(metric)
        
        # Mock pipeline execution
        mock_pipeline = Mock()
        mock_pipeline.execute = AsyncMock(return_value=[True, True])
        mock_redis.pipeline.return_value = mock_pipeline
        
        await collector.flush_metrics()
        
        # Buffer should be cleared
        assert len(collector.metrics_buffer) == 0
    
    def test_get_metric_history(self, mock_redis):
        """Test getting metric history"""
        collector = MetricsCollector(mock_redis)
        
        # Add some historical metrics
        now = datetime.now()
        for i in range(5):
            metric = MetricData(
                name="test_metric",
                value=float(i),
                metric_type=MetricType.GAUGE
            )
            metric.timestamp = now - timedelta(minutes=i)
            collector.metrics_buffer.append(metric)
        
        # Get recent history
        history = collector.get_metric_history("test_metric", {}, 3600)
        
        assert len(history) == 5
        assert all(m.name == "test_metric" for m in history)
    
    def test_get_current_value(self, mock_redis):
        """Test getting current metric value"""
        collector = MetricsCollector(mock_redis)
        
        # Add current metric
        metric = MetricData(
            name="current_metric",
            value=99.9,
            metric_type=MetricType.GAUGE
        )
        collector.metrics_buffer.append(metric)
        
        value = collector.get_current_value("current_metric")
        
        assert value == 99.9

class TestAlertManager:
    """Test AlertManager class"""
    
    def test_alert_manager_creation(self):
        """Test creating alert manager"""
        manager = AlertManager()
        
        assert len(manager.alert_rules) == 0
        assert len(manager.active_alerts) == 0
        assert len(manager.alert_history) == 0
    
    def test_add_remove_alert_rule(self):
        """Test adding and removing alert rules"""
        manager = AlertManager()
        
        rule = AlertRule(
            name="test_rule",
            metric_name="test_metric",
            condition="greater_than",
            threshold=10.0,
            duration=60,
            level=AlertLevel.WARNING
        )
        
        manager.add_alert_rule(rule)
        assert len(manager.alert_rules) == 1
        assert "test_rule" in manager.alert_rules
        
        manager.remove_alert_rule("test_rule")
        assert len(manager.alert_rules) == 0
    
    @pytest.mark.asyncio
    async def test_evaluate_metrics_trigger_alert(self):
        """Test evaluating metrics that trigger alert"""
        manager = AlertManager()
        
        # Add alert rule
        rule = AlertRule(
            name="high_metric",
            metric_name="test_metric",
            condition="greater_than",
            threshold=50.0,
            duration=0,  # No duration requirement for testing
            level=AlertLevel.ERROR
        )
        manager.add_alert_rule(rule)
        
        # Create metrics collector with current value
        collector = MetricsCollector()
        metric = MetricData("test_metric", 75.0, MetricType.GAUGE)
        await collector.collect_metric(metric)
        
        # Evaluate metrics
        await manager.evaluate_metrics(collector)
        
        # Should have triggered alert
        active_alerts = manager.get_active_alerts()
        assert len(active_alerts) == 1
        assert active_alerts[0].rule_name == "high_metric"
        assert active_alerts[0].level == AlertLevel.ERROR
    
    @pytest.mark.asyncio
    async def test_alert_callback(self):
        """Test alert callback functionality"""
        manager = AlertManager()
        
        # Create callback
        callback_called = False
        async def test_callback(alert):
            nonlocal callback_called
            callback_called = True
            assert alert.rule_name == "test_rule"
        
        manager.add_alert_callback(AlertLevel.WARNING, test_callback)
        
        # Add rule that will trigger
        rule = AlertRule(
            name="test_rule",
            metric_name="test_metric",
            condition="greater_than",
            threshold=10.0,
            duration=0,
            level=AlertLevel.WARNING
        )
        manager.add_alert_rule(rule)
        
        # Create collector and trigger evaluation
        collector = MetricsCollector()
        metric = MetricData("test_metric", 15.0, MetricType.GAUGE)
        await collector.collect_metric(metric)
        
        await manager.evaluate_metrics(collector)
        
        # Callback should have been called
        assert callback_called is True
    
    def test_acknowledge_and_clear_alerts(self):
        """Test acknowledging and clearing alerts"""
        manager = AlertManager()
        
        # Create alert
        alert = Alert(
            rule_name="test_rule",
            level=AlertLevel.WARNING,
            message="Test alert",
            value=15.0,
            threshold=10.0
        )
        manager.active_alerts.append(alert)
        
        # Acknowledge alert
        manager.acknowledge_alert(0)
        assert manager.active_alerts[0].acknowledged is True
        
        # Clear alert
        manager.clear_alert(0)
        assert len(manager.active_alerts) == 0

class TestSystemMonitor:
    """Test SystemMonitor class"""
    
    @pytest.fixture
    def mock_metrics_collector(self):
        """Mock metrics collector"""
        return Mock(spec=MetricsCollector)
    
    def test_system_monitor_creation(self, mock_metrics_collector):
        """Test creating system monitor"""
        monitor = SystemMonitor(mock_metrics_collector)
        
        assert monitor.metrics_collector == mock_metrics_collector
        assert monitor.monitoring is False
        assert monitor.monitor_interval == 30
    
    @pytest.mark.asyncio
    async def test_collect_system_metrics(self, mock_metrics_collector):
        """Test collecting system metrics"""
        monitor = SystemMonitor(mock_metrics_collector)
        
        # Mock psutil functions
        with patch('psutil.cpu_percent', return_value=45.5), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk, \
             patch('psutil.net_io_counters') as mock_network, \
             patch('psutil.pids', return_value=[1, 2, 3]), \
             patch('os.getloadavg', return_value=[1.5, 1.2, 1.0]), \
             patch('time.time', return_value=1000000), \
             patch.object(monitor, 'boot_time', 900000):
            
            # Mock memory data
            mock_memory.return_value.percent = 60.0
            mock_memory.return_value.available = 1024 * 1024 * 1024  # 1GB
            
            # Mock disk data
            mock_disk.return_value.used = 50 * 1024 * 1024 * 1024  # 50GB
            mock_disk.return_value.total = 100 * 1024 * 1024 * 1024  # 100GB
            
            # Mock network data
            mock_network.return_value.bytes_recv = 1000 * 1024 * 1024  # 1GB
            mock_network.return_value.bytes_sent = 500 * 1024 * 1024   # 500MB
            
            await monitor._collect_system_metrics()
            
            # Should have collected multiple metrics
            assert mock_metrics_collector.collect_metric.call_count >= 7

class TestApplicationMonitor:
    """Test ApplicationMonitor class"""
    
    @pytest.fixture
    def mock_metrics_collector(self):
        """Mock metrics collector"""
        return Mock(spec=MetricsCollector)
    
    def test_application_monitor_creation(self, mock_metrics_collector):
        """Test creating application monitor"""
        monitor = ApplicationMonitor(mock_metrics_collector)
        
        assert monitor.metrics_collector == mock_metrics_collector
        assert len(monitor.request_times) == 0
        assert monitor.error_count == 0
        assert monitor.request_count == 0
    
    @pytest.mark.asyncio
    async def test_record_request_success(self, mock_metrics_collector):
        """Test recording successful request"""
        monitor = ApplicationMonitor(mock_metrics_collector)
        
        await monitor.record_request(0.5, 200, "/api/test")
        
        assert monitor.request_count == 1
        assert monitor.error_count == 0
        assert len(monitor.request_times) == 1
        assert monitor.request_times[0] == 0.5
        
        # Should have collected metrics
        assert mock_metrics_collector.collect_metric.call_count >= 3
    
    @pytest.mark.asyncio
    async def test_record_request_error(self, mock_metrics_collector):
        """Test recording error request"""
        monitor = ApplicationMonitor(mock_metrics_collector)
        
        await monitor.record_request(1.0, 500, "/api/error")
        
        assert monitor.request_count == 1
        assert monitor.error_count == 1
        assert len(monitor.request_times) == 1
    
    @pytest.mark.asyncio
    async def test_record_database_metrics(self, mock_metrics_collector):
        """Test recording database metrics"""
        monitor = ApplicationMonitor(mock_metrics_collector)
        
        await monitor.record_database_metrics(10, 0.05)
        
        # Should have collected database metrics
        assert mock_metrics_collector.collect_metric.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_record_cache_metrics(self, mock_metrics_collector):
        """Test recording cache metrics"""
        monitor = ApplicationMonitor(mock_metrics_collector)
        
        await monitor.record_cache_metrics(0.85)
        
        # Should have collected cache metric
        assert mock_metrics_collector.collect_metric.call_count >= 1

class TestMonitoringDashboard:
    """Test MonitoringDashboard class"""
    
    @pytest.fixture
    def mock_components(self):
        """Mock dashboard components"""
        metrics_collector = Mock(spec=MetricsCollector)
        alert_manager = Mock(spec=AlertManager)
        
        # Mock current values
        metrics_collector.get_current_value.side_effect = lambda name, labels=None: {
            "system_cpu_usage": 45.5,
            "system_memory_usage": 60.0,
            "system_disk_usage": 50.0,
            "system_load_average": 1.5
        }.get(name, 0)
        
        # Mock alert manager
        alert_manager.get_active_alerts.return_value = [
            Alert("rule1", AlertLevel.WARNING, "Test alert", 85.0, 80.0),
            Alert("rule2", AlertLevel.ERROR, "Another alert", 95.0, 90.0)
        ]
        
        return metrics_collector, alert_manager
    
    def test_dashboard_creation(self, mock_components):
        """Test creating monitoring dashboard"""
        metrics_collector, alert_manager = mock_components
        dashboard = MonitoringDashboard(metrics_collector, alert_manager)
        
        assert dashboard.metrics_collector == metrics_collector
        assert dashboard.alert_manager == alert_manager
    
    def test_get_system_overview(self, mock_components):
        """Test getting system overview"""
        metrics_collector, alert_manager = mock_components
        dashboard = MonitoringDashboard(metrics_collector, alert_manager)
        
        overview = dashboard.get_system_overview()
        
        assert overview['cpu_usage_percent'] == 45.5
        assert overview['memory_usage_percent'] == 60.0
        assert overview['disk_usage_percent'] == 50.0
        assert overview['load_average'] == 1.5
        assert overview['active_alerts'] == 2  # Two unacknowledged alerts
        assert overview['system_status'] == "healthy"
    
    def test_get_performance_metrics(self, mock_components):
        """Test getting performance metrics"""
        metrics_collector, alert_manager = mock_components
        dashboard = MonitoringDashboard(metrics_collector, alert_manager)
        
        # Mock metric history
        metrics_collector.get_metric_history.return_value = [
            MetricData("app_request_count", 1, MetricType.COUNTER),
            MetricData("app_request_count", 1, MetricType.COUNTER),
            MetricData("app_request_count", 1, MetricType.COUNTER)
        ]
        
        performance = dashboard.get_performance_metrics()
        
        assert performance['total_requests'] == 3
        assert performance['error_rate_percent'] == 0.0
        assert 'request_trend' in performance
        assert 'response_time_trend' in performance
    
    def test_get_alert_summary(self, mock_components):
        """Test getting alert summary"""
        metrics_collector, alert_manager = mock_components
        dashboard = MonitoringDashboard(metrics_collector, alert_manager)
        
        summary = dashboard.get_alert_summary()
        
        assert summary['total_active'] == 2
        assert summary['acknowledged'] == 0
        assert 'by_level' in summary
        assert 'recent_alerts' in summary

class TestMonitoringSystem:
    """Test MonitoringSystem class"""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        mock = Mock()
        mock.from_url = Mock(return_value=mock)
        mock.close = AsyncMock()
        return mock
    
    @pytest.mark.asyncio
    async def test_monitoring_system_creation(self, mock_redis):
        """Test creating monitoring system"""
        with patch('monitoring_system.aioredis', mock_redis):
            system = MonitoringSystem("redis://localhost:6379")
            
            assert system.monitoring_enabled is False
            assert len(system.monitoring_tasks) == 0
            assert system.metrics_collector is not None
            assert system.alert_manager is not None
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, mock_redis):
        """Test starting and stopping monitoring"""
        with patch('monitoring_system.aioredis', mock_redis):
            system = MonitoringSystem("redis://localhost:6379")
            
            # Start monitoring
            await system.start_monitoring()
            assert system.monitoring_enabled is True
            assert len(system.monitoring_tasks) == 3  # system monitor, alerts, flush
            
            # Stop monitoring
            await system.stop_monitoring()
            assert system.monitoring_enabled is False
            assert len(system.monitoring_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_convenience_methods(self, mock_redis):
        """Test convenience monitoring methods"""
        with patch('monitoring_system.aioredis', mock_redis):
            system = MonitoringSystem("redis://localhost:6379")
            
            # Test convenience methods
            await system.record_request(0.5, 200, "/api/test")
            await system.record_database_metrics(5, 0.05)
            await system.record_cache_metrics(0.85)
            await system.record_memory_usage(256.0)
            
            # Should not raise any errors
            assert True
    
    def test_get_dashboard_data(self, mock_redis):
        """Test getting dashboard data"""
        with patch('monitoring_system.aioredis', mock_redis):
            system = MonitoringSystem("redis://localhost:6379")
            
            # Mock dashboard methods
            system.dashboard.get_system_overview = Mock(return_value={"status": "healthy"})
            system.dashboard.get_performance_metrics = Mock(return_value={"requests": 100})
            system.dashboard.get_alert_summary = Mock(return_value={"alerts": 2})
            
            data = system.get_dashboard_data()
            
            assert 'system_overview' in data
            assert 'performance_metrics' in data
            assert 'alert_summary' in data
            assert 'generated_at' in data
    
    def test_get_metrics_summary(self, mock_redis):
        """Test getting metrics summary"""
        with patch('monitoring_system.aioredis', mock_redis):
            system = MonitoringSystem("redis://localhost:6379")
            
            # Mock metrics collector
            system.metrics_collector.get_metric_history = Mock(return_value=[
                MetricData("system_cpu_usage", 45.5, MetricType.GAUGE),
                MetricData("system_cpu_usage", 50.0, MetricType.GAUGE)
            ])
            
            system.alert_manager.get_alert_history = Mock(return_value=[
                Alert("rule1", AlertLevel.WARNING, "Test", 85.0, 80.0)
            ])
            
            summary = system.get_metrics_summary(3600)
            
            assert 'time_range_seconds' in summary
            assert 'system_metrics' in summary
            assert 'application_metrics' in summary
            assert 'alerts' in summary

class TestCreateMonitoringSystem:
    """Test create_monitoring_system utility function"""
    
    @pytest.mark.asyncio
    async def test_create_monitoring_system(self):
        """Test creating monitoring system via utility function"""
        with patch('monitoring_system.aioredis') as mock_redis:
            mock_redis.from_url = Mock()
            
            system = await create_monitoring_system("redis://localhost:6379")
            
            assert isinstance(system, MonitoringSystem)
            mock_redis.from_url.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__])