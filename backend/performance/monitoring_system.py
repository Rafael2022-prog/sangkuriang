"""
Monitoring dan Analytics System untuk SANGKURIANG
Mengimplementasikan comprehensive monitoring, alerting, dan performance analytics
"""

import asyncio
import logging
import time
import json
import aiofiles
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque

# Handle redis import conflict
try:
    import redis.asyncio as redis
except ImportError:
    try:
        import aioredis as redis
    except ImportError:
        redis = None

import aiohttp
import statistics
import psutil
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

@dataclass
class MetricData:
    """Individual metric data point"""
    name: str
    value: float
    metric_type: MetricType
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': self.value,
            'type': self.metric_type.value,
            'labels': self.labels,
            'timestamp': self.timestamp.isoformat()
        }

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    metric_name: str
    condition: str  # "greater_than", "less_than", "equals"
    threshold: float
    duration: int  # seconds
    level: AlertLevel
    message: str
    enabled: bool = True
    
    def evaluate(self, value: float, duration_met: bool) -> Optional[AlertLevel]:
        """Evaluate alert rule"""
        if not self.enabled or not duration_met:
            return None
        
        condition_met = False
        if self.condition == "greater_than":
            condition_met = value > self.threshold
        elif self.condition == "less_than":
            condition_met = value < self.threshold
        elif self.condition == "equals":
            condition_met = value == self.threshold
        
        return self.level if condition_met else None

@dataclass
class Alert:
    """Alert notification"""
    rule_name: str
    level: AlertLevel
    message: str
    value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'rule_name': self.rule_name,
            'level': self.level.value,
            'message': self.message,
            'value': self.value,
            'threshold': self.threshold,
            'timestamp': self.timestamp.isoformat(),
            'acknowledged': self.acknowledged
        }

@dataclass
class SystemMetrics:
    """System-level metrics"""
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    network_io_read_mb: float
    network_io_write_mb: float
    load_average_1m: float
    process_count: int
    uptime_seconds: float
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ApplicationMetrics:
    """Application-level metrics"""
    request_count: int
    error_count: int
    response_time_avg_ms: float
    response_time_p95_ms: float
    response_time_p99_ms: float
    active_connections: int
    database_connections: int
    cache_hit_rate: float
    memory_usage_mb: float
    timestamp: datetime = field(default_factory=datetime.now)

class MetricsCollector:
    """Collect dan store metrics dari berbagai sumber"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.metrics_buffer: List[MetricData] = []
        self.buffer_size = 1000
        self.flush_interval = 60  # seconds
        self.last_flush = datetime.now()
        
        # Metric storage
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10080))  # 1 week of minute data
        self.metric_aggregates: Dict[str, Dict[str, float]] = defaultdict(dict)
    
    async def collect_metric(self, metric: MetricData):
        """Collect individual metric"""
        self.metrics_buffer.append(metric)
        
        # Add to real-time history
        metric_key = f"{metric.name}:{json.dumps(metric.labels, sort_keys=True)}"
        self.metric_history[metric_key].append(metric)
        
        # Update aggregates
        self._update_aggregates(metric)
        
        # Flush jika buffer penuh atau interval tercapai
        if (len(self.metrics_buffer) >= self.buffer_size or 
            (datetime.now() - self.last_flush).total_seconds() >= self.flush_interval):
            await self.flush_metrics()
    
    def _update_aggregates(self, metric: MetricData):
        """Update metric aggregates"""
        key = f"{metric.name}:{json.dumps(metric.labels, sort_keys=True)}"
        
        if metric.metric_type == MetricType.COUNTER:
            self.metric_aggregates[key]['total'] = self.metric_aggregates[key].get('total', 0) + metric.value
            self.metric_aggregates[key]['count'] = self.metric_aggregates[key].get('count', 0) + 1
        
        elif metric.metric_type == MetricType.GAUGE:
            values = [m.value for m in self.metric_history[key]]
            if values:
                self.metric_aggregates[key]['current'] = values[-1]
                self.metric_aggregates[key]['avg'] = statistics.mean(values)
                self.metric_aggregates[key]['min'] = min(values)
                self.metric_aggregates[key]['max'] = max(values)
        
        elif metric.metric_type == MetricType.HISTOGRAM:
            values = [m.value for m in self.metric_history[key]]
            if values:
                self.metric_aggregates[key]['avg'] = statistics.mean(values)
                self.metric_aggregates[key]['p50'] = statistics.median(values)
                self.metric_aggregates[key]['p95'] = statistics.quantiles(values, n=20)[18] if len(values) > 1 else values[0]
                self.metric_aggregates[key]['p99'] = statistics.quantiles(values, n=100)[98] if len(values) > 1 else values[0]
    
    async def flush_metrics(self):
        """Flush metrics ke persistent storage"""
        if not self.metrics_buffer:
            return
        
        try:
            # Save ke Redis jika tersedia
            if self.redis_client:
                pipeline = self.redis_client.pipeline()
                
                for metric in self.metrics_buffer:
                    redis_key = f"metrics:{metric.name}:{metric.timestamp.strftime('%Y%m%d%H')}"
                    pipeline.lpush(redis_key, json.dumps(metric.to_dict()))
                    pipeline.expire(redis_key, 86400 * 7)  # 7 days retention
                
                await pipeline.execute()
            
            # Clear buffer
            self.metrics_buffer.clear()
            self.last_flush = datetime.now()
            
            logger.debug(f"Flushed {len(self.metrics_buffer)} metrics")
            
        except Exception as e:
            logger.error(f"Error flushing metrics: {e}")
    
    def get_metric_history(self, metric_name: str, labels: Dict = None, 
                          time_range: int = 3600) -> List[MetricData]:
        """Get metric history untuk time range tertentu"""
        
        label_key = json.dumps(labels or {}, sort_keys=True)
        metric_key = f"{metric_name}:{label_key}"
        
        cutoff_time = datetime.now() - timedelta(seconds=time_range)
        
        if metric_key in self.metric_history:
            return [m for m in self.metric_history[metric_key] if m.timestamp >= cutoff_time]
        
        return []
    
    def get_current_value(self, metric_name: str, labels: Dict = None) -> Optional[float]:
        """Get current value untuk metric"""
        history = self.get_metric_history(metric_name, labels, 300)  # Last 5 minutes
        
        if history:
            return history[-1].value
        
        return None

class AlertManager:
    """Manage dan process alert rules"""
    
    def __init__(self):
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: List[Alert] = []
        self.alert_history: deque = deque(maxlen=1000)
        self.alert_callbacks: Dict[AlertLevel, List[Callable]] = defaultdict(list)
        
        # Track rule violations
        self.rule_violations: Dict[str, List[datetime]] = defaultdict(list)
        self.violation_window = 300  # 5 minutes
    
    def add_alert_rule(self, rule: AlertRule):
        """Add alert rule"""
        self.alert_rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str):
        """Remove alert rule"""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")
    
    async def evaluate_metrics(self, metrics_collector: MetricsCollector):
        """Evaluate semua alert rules terhadap current metrics"""
        
        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            # Get current value untuk metric
            current_value = metrics_collector.get_current_value(rule.metric_name)
            
            if current_value is None:
                continue
            
            # Check if condition is met
            condition_met = False
            if rule.condition == "greater_than":
                condition_met = current_value > rule.threshold
            elif rule.condition == "less_than":
                condition_met = current_value < rule.threshold
            elif rule.condition == "equals":
                condition_met = current_value == rule.threshold
            
            # Track violations
            now = datetime.now()
            if condition_met:
                self.rule_violations[rule_name].append(now)
            else:
                # Clear violations jika condition not met
                self.rule_violations[rule_name].clear()
            
            # Check duration requirement
            violations = self.rule_violations[rule_name]
            violations = [v for v in violations if (now - v).total_seconds() <= rule.duration]
            self.rule_violations[rule_name] = violations
            
            duration_met = len(violations) > 0 and (now - violations[0]).total_seconds() >= rule.duration
            
            # Evaluate rule
            alert_level = rule.evaluate(current_value, duration_met)
            
            if alert_level:
                await self._trigger_alert(rule, current_value, alert_level)
    
    async def _trigger_alert(self, rule: AlertRule, value: float, level: AlertLevel):
        """Trigger alert notification"""
        
        # Check if similar alert sudah ada
        existing_alert = next((a for a in self.active_alerts 
                              if a.rule_name == rule.name and not a.acknowledged), None)
        
        if existing_alert:
            # Update existing alert
            existing_alert.timestamp = datetime.now()
            existing_alert.value = value
        else:
            # Create new alert
            alert = Alert(
                rule_name=rule.name,
                level=level,
                message=rule.message.format(value=value, threshold=rule.threshold),
                value=value,
                threshold=rule.threshold
            )
            
            self.active_alerts.append(alert)
            self.alert_history.append(alert)
            
            # Call alert callbacks
            for callback in self.alert_callbacks[level]:
                try:
                    await callback(alert)
                except Exception as e:
                    logger.error(f"Alert callback error: {e}")
            
            logger.warning(f"Alert triggered: {rule.name} - {level.value} - {value:.2f}")
    
    def acknowledge_alert(self, alert_index: int):
        """Acknowledge alert"""
        if 0 <= alert_index < len(self.active_alerts):
            self.active_alerts[alert_index].acknowledged = True
    
    def clear_alert(self, alert_index: int):
        """Clear alert dari active list"""
        if 0 <= alert_index < len(self.active_alerts):
            del self.active_alerts[alert_index]
    
    def add_alert_callback(self, level: AlertLevel, callback: Callable):
        """Add callback untuk alert level tertentu"""
        self.alert_callbacks[level].append(callback)
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return self.active_alerts.copy()
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return list(self.alert_history)[-limit:]

class SystemMonitor:
    """Monitor system-level metrics"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.monitoring = False
        self.monitor_interval = 30  # seconds
        
        # System metrics tracking
        self.boot_time = psutil.boot_time()
        self.last_network_stats = None
    
    async def start_monitoring(self):
        """Start system monitoring"""
        self.monitoring = True
        logger.info("System monitoring started")
        
        while self.monitoring:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(self.monitor_interval)
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                await asyncio.sleep(self.monitor_interval)
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring = False
        logger.info("System monitoring stopped")
    
    async def _collect_system_metrics(self):
        """Collect system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            await self.metrics_collector.collect_metric(
                MetricData("system_cpu_usage", cpu_percent, MetricType.GAUGE, {"type": "percent"})
            )
            
            # Memory usage
            memory = psutil.virtual_memory()
            await self.metrics_collector.collect_metric(
                MetricData("system_memory_usage", memory.percent, MetricType.GAUGE, {"type": "percent"})
            )
            await self.metrics_collector.collect_metric(
                MetricData("system_memory_available_mb", memory.available / (1024 * 1024), MetricType.GAUGE)
            )
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            await self.metrics_collector.collect_metric(
                MetricData("system_disk_usage", disk_percent, MetricType.GAUGE, {"type": "percent"})
            )
            
            # Network I/O
            network = psutil.net_io_counters()
            if self.last_network_stats:
                read_mb = (network.bytes_recv - self.last_network_stats.bytes_recv) / (1024 * 1024)
                write_mb = (network.bytes_sent - self.last_network_stats.bytes_sent) / (1024 * 1024)
                
                await self.metrics_collector.collect_metric(
                    MetricData("system_network_read_mb", read_mb, MetricType.COUNTER, {"interval": "30s"})
                )
                await self.metrics_collector.collect_metric(
                    MetricData("system_network_write_mb", write_mb, MetricType.COUNTER, {"interval": "30s"})
                )
            
            self.last_network_stats = network
            
            # Load average
            load_avg = os.getloadavg()[0]  # 1-minute load average
            await self.metrics_collector.collect_metric(
                MetricData("system_load_average", load_avg, MetricType.GAUGE, {"duration": "1m"})
            )
            
            # Process count
            process_count = len(psutil.pids())
            await self.metrics_collector.collect_metric(
                MetricData("system_process_count", process_count, MetricType.GAUGE)
            )
            
            # Uptime
            uptime = time.time() - self.boot_time
            await self.metrics_collector.collect_metric(
                MetricData("system_uptime_seconds", uptime, MetricType.GAUGE)
            )
            
            logger.debug(f"System metrics collected: CPU={cpu_percent:.1f}%, Memory={memory.percent:.1f}%")
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

class ApplicationMonitor:
    """Monitor application-level metrics"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.request_times = deque(maxlen=1000)
        self.error_count = 0
        self.request_count = 0
    
    async def record_request(self, response_time: float, status_code: int, endpoint: str):
        """Record HTTP request metrics"""
        self.request_count += 1
        self.request_times.append(response_time)
        
        # Record response time
        await self.metrics_collector.collect_metric(
            MetricData("app_response_time_ms", response_time * 1000, MetricType.HISTOGRAM, 
                      {"endpoint": endpoint, "status": str(status_code)})
        )
        
        # Record request count
        await self.metrics_collector.collect_metric(
            MetricData("app_request_count", 1, MetricType.COUNTER, {"endpoint": endpoint, "status": str(status_code)})
        )
        
        # Record errors
        if status_code >= 400:
            self.error_count += 1
            await self.metrics_collector.collect_metric(
                MetricData("app_error_count", 1, MetricType.COUNTER, 
                          {"endpoint": endpoint, "status": str(status_code)})
            )
        
        # Record active connections (simplified)
        await self.metrics_collector.collect_metric(
            MetricData("app_active_connections", len(self.request_times), MetricType.GAUGE)
        )
    
    async def record_database_metrics(self, connection_count: int, query_time: float):
        """Record database metrics"""
        await self.metrics_collector.collect_metric(
            MetricData("app_db_connections", connection_count, MetricType.GAUGE)
        )
        await self.metrics_collector.collect_metric(
            MetricData("app_db_query_time_ms", query_time * 1000, MetricType.HISTOGRAM)
        )
    
    async def record_cache_metrics(self, hit_rate: float):
        """Record cache metrics"""
        await self.metrics_collector.collect_metric(
            MetricData("app_cache_hit_rate", hit_rate, MetricType.GAUGE)
        )
    
    async def record_memory_usage(self, memory_mb: float):
        """Record application memory usage"""
        await self.metrics_collector.collect_metric(
            MetricData("app_memory_usage_mb", memory_mb, MetricType.GAUGE)
        )

class MonitoringDashboard:
    """Generate monitoring dashboard data"""
    
    def __init__(self, metrics_collector: MetricsCollector, alert_manager: AlertManager):
        self.metrics_collector = metrics_collector
        self.alert_manager = alert_manager
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get system overview dashboard data"""
        
        # Get current system metrics
        cpu_usage = self.metrics_collector.get_current_value("system_cpu_usage")
        memory_usage = self.metrics_collector.get_current_value("system_memory_usage")
        disk_usage = self.metrics_collector.get_current_value("system_disk_usage")
        load_avg = self.metrics_collector.get_current_value("system_load_average")
        
        return {
            'cpu_usage_percent': cpu_usage or 0,
            'memory_usage_percent': memory_usage or 0,
            'disk_usage_percent': disk_usage or 0,
            'load_average': load_avg or 0,
            'active_alerts': len([a for a in self.alert_manager.get_active_alerts() if not a.acknowledged]),
            'system_status': self._get_system_status(cpu_usage, memory_usage, disk_usage)
        }
    
    def _get_system_status(self, cpu: float, memory: float, disk: float) -> str:
        """Determine system status"""
        if any(metric is None for metric in [cpu, memory, disk]):
            return "unknown"
        
        if cpu > 90 or memory > 95 or disk > 95:
            return "critical"
        elif cpu > 80 or memory > 85 or disk > 90:
            return "warning"
        else:
            return "healthy"
    
    def get_performance_metrics(self, time_range: int = 3600) -> Dict[str, Any]:
        """Get performance metrics untuk dashboard"""
        
        # Get request metrics
        request_history = self.metrics_collector.get_metric_history("app_request_count", {}, time_range)
        response_time_history = self.metrics_collector.get_metric_history("app_response_time_ms", {}, time_range)
        
        # Calculate aggregates
        total_requests = len(request_history)
        avg_response_time = statistics.mean([m.value for m in response_time_history]) if response_time_history else 0
        
        # Get error rate
        error_history = self.metrics_collector.get_metric_history("app_error_count", {}, time_range)
        total_errors = sum(m.value for m in error_history)
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_requests': total_requests,
            'error_rate_percent': round(error_rate, 2),
            'avg_response_time_ms': round(avg_response_time, 2),
            'request_trend': self._calculate_trend(request_history),
            'response_time_trend': self._calculate_trend(response_time_history)
        }
    
    def _calculate_trend(self, history: List[MetricData]) -> str:
        """Calculate trend dari metric history"""
        if len(history) < 2:
            return "stable"
        
        # Split into first and second half
        mid_point = len(history) // 2
        first_half = history[:mid_point]
        second_half = history[mid_point:]
        
        first_avg = statistics.mean([m.value for m in first_half]) if first_half else 0
        second_avg = statistics.mean([m.value for m in second_half]) if second_half else 0
        
        if first_avg == 0:
            return "stable"
        
        change_percent = ((second_avg - first_avg) / first_avg) * 100
        
        if change_percent > 10:
            return "increasing"
        elif change_percent < -10:
            return "decreasing"
        else:
            return "stable"
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary untuk dashboard"""
        
        active_alerts = self.alert_manager.get_active_alerts()
        alert_history = self.alert_manager.get_alert_history(100)
        
        # Count by level
        alert_counts = defaultdict(int)
        for alert in active_alerts:
            alert_counts[alert.level] += 1
        
        return {
            'total_active': len(active_alerts),
            'acknowledged': len([a for a in active_alerts if a.acknowledged]),
            'by_level': {
                level.value: alert_counts.get(level, 0) 
                for level in AlertLevel
            },
            'recent_alerts': [a.to_dict() for a in alert_history[:10]]
        }

class MonitoringSystem:
    """
    Main monitoring system untuk SANGKURIANG
    Menggabungkan metrics collection, alerting, dan dashboard generation
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = aioredis.from_url(redis_url + "/3")  # Use DB 3 for monitoring
        self.metrics_collector = MetricsCollector(self.redis_client)
        self.alert_manager = AlertManager()
        self.system_monitor = SystemMonitor(self.metrics_collector)
        self.application_monitor = ApplicationMonitor(self.metrics_collector)
        self.dashboard = MonitoringDashboard(self.metrics_collector, self.alert_manager)
        
        # Monitoring state
        self.monitoring_enabled = False
        self.monitoring_tasks = []
        
        # Setup default alert rules
        self._setup_default_alerts()
    
    def _setup_default_alerts(self):
        """Setup default alert rules"""
        
        default_rules = [
            AlertRule(
                name="high_cpu_usage",
                metric_name="system_cpu_usage",
                condition="greater_than",
                threshold=85.0,
                duration=300,  # 5 minutes
                level=AlertLevel.WARNING,
                message="CPU usage is high: {value:.1f}% (threshold: {threshold}%)"
            ),
            AlertRule(
                name="critical_cpu_usage",
                metric_name="system_cpu_usage",
                condition="greater_than",
                threshold=95.0,
                duration=180,  # 3 minutes
                level=AlertLevel.CRITICAL,
                message="CPU usage is critical: {value:.1f}% (threshold: {threshold}%)"
            ),
            AlertRule(
                name="high_memory_usage",
                metric_name="system_memory_usage",
                condition="greater_than",
                threshold=90.0,
                duration=300,
                level=AlertLevel.WARNING,
                message="Memory usage is high: {value:.1f}% (threshold: {threshold}%)"
            ),
            AlertRule(
                name="high_response_time",
                metric_name="app_response_time_ms",
                condition="greater_than",
                threshold=5000.0,  # 5 seconds
                duration=300,
                level=AlertLevel.ERROR,
                message="Response time is high: {value:.0f}ms (threshold: {threshold}ms)"
            ),
            AlertRule(
                name="high_error_rate",
                metric_name="app_error_count",
                condition="greater_than",
                threshold=10.0,  # 10 errors per evaluation period
                duration=300,
                level=AlertLevel.ERROR,
                message="Error rate is high: {value:.0f} errors (threshold: {threshold})"
            )
        ]
        
        for rule in default_rules:
            self.alert_manager.add_alert_rule(rule)
    
    async def start_monitoring(self):
        """Start monitoring system"""
        
        if self.monitoring_enabled:
            logger.warning("Monitoring already enabled")
            return
        
        self.monitoring_enabled = True
        logger.info("Starting monitoring system")
        
        # Start system monitoring
        system_task = asyncio.create_task(self.system_monitor.start_monitoring())
        self.monitoring_tasks.append(system_task)
        
        # Start alert evaluation
        alert_task = asyncio.create_task(self._alert_evaluation_loop())
        self.monitoring_tasks.append(alert_task)
        
        # Start metrics flush
        flush_task = asyncio.create_task(self._metrics_flush_loop())
        self.monitoring_tasks.append(flush_task)
        
        logger.info("Monitoring system started successfully")
    
    async def stop_monitoring(self):
        """Stop monitoring system"""
        
        if not self.monitoring_enabled:
            return
        
        self.monitoring_enabled = False
        logger.info("Stopping monitoring system")
        
        # Stop system monitor
        self.system_monitor.stop_monitoring()
        
        # Cancel all monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        self.monitoring_tasks.clear()
        
        # Final flush
        await self.metrics_collector.flush_metrics()
        
        # Close Redis connection
        await self.redis_client.close()
        
        logger.info("Monitoring system stopped")
    
    async def _alert_evaluation_loop(self):
        """Alert evaluation loop"""
        
        while self.monitoring_enabled:
            try:
                await self.alert_manager.evaluate_metrics(self.metrics_collector)
                await asyncio.sleep(60)  # Evaluate every minute
            except Exception as e:
                logger.error(f"Alert evaluation error: {e}")
                await asyncio.sleep(60)
    
    async def _metrics_flush_loop(self):
        """Metrics flush loop"""
        
        while self.monitoring_enabled:
            try:
                await self.metrics_collector.flush_metrics()
                await asyncio.sleep(300)  # Flush every 5 minutes
            except Exception as e:
                logger.error(f"Metrics flush error: {e}")
                await asyncio.sleep(300)
    
    # Convenience methods untuk application monitoring
    async def record_request(self, response_time: float, status_code: int, endpoint: str):
        """Record HTTP request"""
        await self.application_monitor.record_request(response_time, status_code, endpoint)
    
    async def record_database_metrics(self, connection_count: int, query_time: float):
        """Record database metrics"""
        await self.application_monitor.record_database_metrics(connection_count, query_time)
    
    async def record_cache_metrics(self, hit_rate: float):
        """Record cache metrics"""
        await self.application_monitor.record_cache_metrics(hit_rate)
    
    async def record_memory_usage(self, memory_mb: float):
        """Record memory usage"""
        await self.application_monitor.record_memory_usage(memory_mb)
    
    # Dashboard methods
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data"""
        
        return {
            'system_overview': self.dashboard.get_system_overview(),
            'performance_metrics': self.dashboard.get_performance_metrics(),
            'alert_summary': self.dashboard.get_alert_summary(),
            'generated_at': datetime.now().isoformat()
        }
    
    def get_metrics_summary(self, time_range: int = 3600) -> Dict[str, Any]:
        """Get metrics summary untuk reporting"""
        
        # Get system metrics
        cpu_history = self.metrics_collector.get_metric_history("system_cpu_usage", {}, time_range)
        memory_history = self.metrics_collector.get_metric_history("system_memory_usage", {}, time_range)
        
        # Get application metrics
        request_history = self.metrics_collector.get_metric_history("app_request_count", {}, time_range)
        response_time_history = self.metrics_collector.get_metric_history("app_response_time_ms", {}, time_range)
        
        return {
            'time_range_seconds': time_range,
            'system_metrics': {
                'avg_cpu_percent': statistics.mean([m.value for m in cpu_history]) if cpu_history else 0,
                'max_cpu_percent': max([m.value for m in cpu_history]) if cpu_history else 0,
                'avg_memory_percent': statistics.mean([m.value for m in memory_history]) if memory_history else 0,
                'max_memory_percent': max([m.value for m in memory_history]) if memory_history else 0,
            },
            'application_metrics': {
                'total_requests': len(request_history),
                'avg_response_time_ms': statistics.mean([m.value for m in response_time_history]) if response_time_history else 0,
                'max_response_time_ms': max([m.value for m in response_time_history]) if response_time_history else 0,
            },
            'alerts': {
                'total_triggered': len(self.alert_manager.get_alert_history(time_range)),
                'currently_active': len(self.alert_manager.get_active_alerts())
            }
        }

# Utility functions
async def create_monitoring_system(redis_url: str = "redis://localhost:6379") -> MonitoringSystem:
    """
    Utility function untuk membuat monitoring system
    
    Args:
        redis_url: Redis connection URL
    
    Returns:
        MonitoringSystem instance yang sudah di-initialize
    """
    
    system = MonitoringSystem(redis_url)
    return system

# Example usage dan testing
if __name__ == "__main__":
    async def test_monitoring_system():
        """Test monitoring system functionality"""
        
        # Create monitoring system
        monitoring = await create_monitoring_system()
        
        try:
            # Start monitoring
            await monitoring.start_monitoring()
            
            # Simulate some activity
            for i in range(10):
                # Simulate requests
                response_time = 0.1 + (i * 0.05)  # Gradually increasing response time
                await monitoring.record_request(response_time, 200, "/api/test")
                
                # Simulate database metrics
                await monitoring.record_database_metrics(5, 0.05)
                
                # Simulate cache metrics
                await monitoring.record_cache_metrics(0.8 + (i * 0.02))
                
                # Simulate memory usage
                await monitoring.record_memory_usage(256 + (i * 10))
                
                await asyncio.sleep(2)
            
            # Get dashboard data
            dashboard_data = monitoring.get_dashboard_data()
            print(f"Dashboard Data: {json.dumps(dashboard_data, indent=2, default=str)}")
            
            # Get metrics summary
            metrics_summary = monitoring.get_metrics_summary(300)  # Last 5 minutes
            print(f"Metrics Summary: {json.dumps(metrics_summary, indent=2, default=str)}")
            
            # Wait a bit more to see alerts
            await asyncio.sleep(10)
            
        finally:
            # Stop monitoring
            await monitoring.stop_monitoring()
    
    # Run test
    asyncio.run(test_monitoring_system())