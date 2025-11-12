"""
SANGKURIANG Decentralized Compute System
Sistem komputasi terdesentralisasi untuk eksekusi smart contract dan DAO operations
"""

import asyncio
import json
import hashlib
import time
import subprocess
import tempfile
import os
import sys
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import redis.asyncio as redis
from web3 import Web3
from eth_account import Account
import aiofiles
import docker
import psutil
import numpy as np
from pathlib import Path
import base64
import pickle
import threading
import queue
import uuid


class ComputeTaskType(Enum):
    """Jenis task komputasi"""
    SMART_CONTRACT = "smart_contract"
    DAO_GOVERNANCE = "dao_governance"
    VOTING_CALCULATION = "voting_calculation"
    TREASURY_OPERATION = "treasury_operation"
    PROPOSAL_EXECUTION = "proposal_execution"
    DATA_ANALYSIS = "data_analysis"
    MACHINE_LEARNING = "machine_learning"
    CRYPTOGRAPHIC_OPERATION = "cryptographic_operation"
    VALIDATION_TASK = "validation_task"
    BACKGROUND_PROCESS = "background_process"


class ComputeTaskStatus(Enum):
    """Status task komputasi"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


class ComputeNodeStatus(Enum):
    """Status node komputasi"""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    SUSPENDED = "suspended"


class ResourceType(Enum):
    """Jenis resource komputasi"""
    CPU = "cpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    GPU = "gpu"
    BANDWIDTH = "bandwidth"


@dataclass
class ComputeTask:
    """Task komputasi"""
    task_id: str
    task_type: ComputeTaskType
    task_name: str
    task_description: str
    task_data: Dict[str, Any]
    task_code: str
    task_hash: str
    priority: int = 1
    timeout_seconds: int = 300
    max_retries: int = 3
    retry_count: int = 0
    status: ComputeTaskStatus = ComputeTaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_node: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    sub_tasks: List[str] = field(default_factory=list)
    parent_task: Optional[str] = None
    validation_required: bool = True
    validation_result: Optional[Dict[str, Any]] = None
    gas_limit: int = 3000000
    gas_used: int = 0
    cost_estimate: float = 0.0
    actual_cost: float = 0.0
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComputeNode:
    """Node komputasi dalam jaringan"""
    node_id: str
    node_address: str
    node_name: str
    node_type: str  # docker, native, cloud, edge
    node_status: ComputeNodeStatus = ComputeNodeStatus.ONLINE
    node_location: str = "unknown"
    node_capabilities: List[str] = field(default_factory=list)
    cpu_cores: int = 1
    memory_gb: float = 1.0
    storage_gb: float = 10.0
    gpu_available: bool = False
    gpu_memory_gb: float = 0.0
    network_bandwidth_mbps: int = 100
    current_load: float = 0.0
    max_concurrent_tasks: int = 5
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_execution_time: float = 0.0
    reliability_score: float = 1.0
    cost_per_hour: float = 0.0
    last_heartbeat: datetime = field(default_factory=datetime.now)
    last_task_completion: Optional[datetime] = None
    supported_task_types: List[ComputeTaskType] = field(default_factory=list)
    security_level: str = "standard"
    encryption_supported: bool = True
    container_runtime: str = "docker"
    node_version: str = "1.0.0"
    custom_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComputeResource:
    """Resource komputasi"""
    resource_id: str
    resource_type: ResourceType
    resource_name: str
    total_capacity: float
    used_capacity: float = 0.0
    available_capacity: float = 0.0
    resource_unit: str = "units"
    resource_status: str = "available"
    resource_location: str = "unknown"
    resource_cost_per_unit: float = 0.0
    resource_efficiency: float = 1.0
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.available_capacity = self.total_capacity - self.used_capacity


@dataclass
class ComputeResult:
    """Hasil komputasi"""
    result_id: str
    task_id: str
    node_id: str
    result_data: Dict[str, Any]
    result_hash: str
    execution_time: float
    resource_usage: Dict[str, Any]
    gas_used: int = 0
    actual_cost: float = 0.0
    validation_status: str = "pending"
    validation_proof: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    result_signature: Optional[str] = None
    error_details: Optional[str] = None
    output_logs: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComputeMetrics:
    """Metrik sistem komputasi"""
    total_tasks: int = 0
    pending_tasks: int = 0
    running_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_nodes: int = 0
    online_nodes: int = 0
    busy_nodes: int = 0
    total_compute_time: float = 0.0
    average_execution_time: float = 0.0
    total_gas_used: int = 0
    total_cost: float = 0.0
    system_efficiency: float = 0.0
    network_utilization: float = 0.0
    task_success_rate: float = 0.0
    node_reliability_score: float = 0.0
    resource_utilization: Dict[str, float] = field(default_factory=dict)
    performance_history: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ComputeConfiguration:
    """Konfigurasi sistem komputasi"""
    max_concurrent_tasks: int = 100
    task_timeout_seconds: int = 300
    max_task_retries: int = 3
    default_gas_limit: int = 3000000
    min_node_reliability: float = 0.8
    max_task_queue_size: int = 1000
    resource_allocation_strategy: str = "balanced"  # balanced, performance, cost, reliability
    task_scheduling_algorithm: str = "priority"  # priority, round_robin, load_balancing
    enable_task_validation: bool = True
    enable_result_verification: bool = True
    enable_cost_optimization: bool = True
    enable_resource_monitoring: bool = True
    enable_performance_profiling: bool = True
    enable_security_scanning: bool = True
    enable_container_isolation: bool = True
    enable_network_encryption: bool = True
    enable_fault_tolerance: bool = True
    enable_auto_scaling: bool = True
    enable_load_balancing: bool = True
    enable_resource_sharing: bool = True
    enable_cross_chain_execution: bool = True
    enable_decentralized_validation: bool = True
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class DecentralizedComputeSystem:
    """Sistem Komputasi Terdesentralisasi SANGKURIANG"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        web3_provider: str = "https://mainnet.infura.io/v3/YOUR_PROJECT_ID",
        docker_enabled: bool = True,
        max_nodes: int = 10,
        enable_monitoring: bool = True
    ):
        # Redis client
        self.redis_client = redis.from_url(redis_url)
        
        # Web3 integration
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))
        
        # Docker client
        self.docker_enabled = docker_enabled
        if docker_enabled:
            try:
                self.docker_client = docker.from_env()
            except Exception as e:
                print(f"Docker not available: {e}")
                self.docker_client = None
        else:
            self.docker_client = None
        
        # System state
        self.task_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.task_registry: Dict[str, ComputeTask] = {}
        self.node_registry: Dict[str, ComputeNode] = {}
        self.resource_registry: Dict[str, ComputeResource] = {}
        self.result_registry: Dict[str, ComputeResult] = {}
        self.pending_operations: List[str] = []
        
        # Configuration
        self.config = ComputeConfiguration()
        self.max_nodes = max_nodes
        self.enable_monitoring = enable_monitoring
        
        # Metrics
        self.metrics = ComputeMetrics()
        
        # Monitoring
        self.monitoring_active = True
        self.task_processor_thread = None
        self.monitoring_thread = None
        
        # Security
        self.enable_encryption = True
        self.enable_validation = True
        
        # Initialize system
        asyncio.create_task(self._initialize_compute_system())
    
    async def _initialize_compute_system(self) -> None:
        """Inisialisasi sistem komputasi"""
        try:
            # Load existing data from Redis
            await self._load_existing_data()
            
            # Initialize compute nodes
            await self._initialize_compute_nodes()
            
            # Initialize resources
            await self._initialize_compute_resources()
            
            # Start task processor
            self.task_processor_thread = threading.Thread(target=self._task_processor_loop, daemon=True)
            self.task_processor_thread.start()
            
            # Start monitoring
            if self.enable_monitoring:
                self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
                self.monitoring_thread.start()
            
            print("✅ Decentralized compute system initialized")
            
        except Exception as e:
            print(f"❌ Failed to initialize compute system: {e}")
    
    async def submit_task(
        self,
        task_type: ComputeTaskType,
        task_name: str,
        task_description: str,
        task_data: Dict[str, Any],
        task_code: str,
        priority: int = 1,
        timeout_seconds: int = 300,
        max_retries: int = 3,
        dependencies: Optional[List[str]] = None,
        validation_required: bool = True,
        gas_limit: int = 3000000,
        custom_metadata: Optional[Dict[str, Any]] = None,
        submitter_address: str = ""
    ) -> Dict[str, Any]:
        """Submit compute task to the system"""
        try:
            # Generate task ID and hash
            task_id = str(uuid.uuid4())
            task_hash = hashlib.sha256(f"{task_type}:{task_name}:{task_code}:{time.time()}".encode()).hexdigest()
            
            # Create compute task
            task = ComputeTask(
                task_id=task_id,
                task_type=task_type,
                task_name=task_name,
                task_description=task_description,
                task_data=task_data,
                task_code=task_code,
                task_hash=task_hash,
                priority=priority,
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
                dependencies=dependencies or [],
                validation_required=validation_required,
                gas_limit=gas_limit,
                custom_metadata=custom_metadata or {},
                status=ComputeTaskStatus.PENDING
            )
            
            # Validate task
            validation_result = await self._validate_task(task)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": validation_result["error"]
                }
            
            # Estimate cost
            cost_estimate = await self._estimate_task_cost(task)
            task.cost_estimate = cost_estimate["estimated_cost"]
            
            # Add to registry
            self.task_registry[task_id] = task
            
            # Add to queue
            self.task_queue.put((-priority, task_id))  # Negative for max-heap behavior
            
            # Update metrics
            self.metrics.total_tasks += 1
            self.metrics.pending_tasks += 1
            
            print(f"✅ Task submitted: {task_id}")
            return {
                "success": True,
                "task_id": task_id,
                "task_hash": task_hash,
                "cost_estimate": cost_estimate["estimated_cost"],
                "estimated_duration": cost_estimate["estimated_duration"],
                "queue_position": self.task_queue.qsize()
            }
            
        except Exception as e:
            print(f"❌ Failed to submit task: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status and details"""
        try:
            if task_id not in self.task_registry:
                return {"success": False, "error": "Task not found"}
            
            task = self.task_registry[task_id]
            
            return {
                "success": True,
                "task": {
                    "task_id": task.task_id,
                    "task_type": task.task_type.value,
                    "task_name": task.task_name,
                    "task_description": task.task_description,
                    "status": task.status.value,
                    "priority": task.priority,
                    "created_at": task.created_at.isoformat(),
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "assigned_node": task.assigned_node,
                    "retry_count": task.retry_count,
                    "execution_time": task.execution_time,
                    "gas_limit": task.gas_limit,
                    "gas_used": task.gas_used,
                    "cost_estimate": task.cost_estimate,
                    "actual_cost": task.actual_cost,
                    "validation_required": task.validation_required,
                    "validation_status": task.validation_result["status"] if task.validation_result else "pending"
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to get task status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """Get task execution result"""
        try:
            if task_id not in self.task_registry:
                return {"success": False, "error": "Task not found"}
            
            task = self.task_registry[task_id]
            
            if task.status != ComputeTaskStatus.COMPLETED:
                return {
                    "success": False,
                    "error": f"Task not completed. Status: {task.status.value}"
                }
            
            return {
                "success": True,
                "result": {
                    "task_id": task.task_id,
                    "result_data": task.result_data,
                    "execution_time": task.execution_time,
                    "gas_used": task.gas_used,
                    "actual_cost": task.actual_cost,
                    "validation_result": task.validation_result,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to get task result: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cancel_task(self, task_id: str, requester_address: str) -> Dict[str, Any]:
        """Cancel a pending or running task"""
        try:
            if task_id not in self.task_registry:
                return {"success": False, "error": "Task not found"}
            
            task = self.task_registry[task_id]
            
            # Check permissions
            if task.task_data.get("submitter_address") != requester_address:
                return {"success": False, "error": "Only task submitter can cancel task"}
            
            # Update task status
            if task.status in [ComputeTaskStatus.PENDING, ComputeTaskStatus.QUEUED]:
                task.status = ComputeTaskStatus.CANCELLED
                self.metrics.pending_tasks -= 1
            elif task.status == ComputeTaskStatus.RUNNING:
                # Task is running, need to stop it
                await self._stop_running_task(task_id)
                task.status = ComputeTaskStatus.CANCELLED
                self.metrics.running_tasks -= 1
            else:
                return {
                    "success": False,
                    "error": f"Cannot cancel task in status: {task.status.value}"
                }
            
            print(f"✅ Task cancelled: {task_id}")
            return {
                "success": True,
                "task_id": task_id,
                "status": task.status.value
            }
            
        except Exception as e:
            print(f"❌ Failed to cancel task: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_tasks(
        self,
        task_type: Optional[ComputeTaskType] = None,
        status: Optional[ComputeTaskStatus] = None,
        submitter_address: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List compute tasks with filtering"""
        try:
            filtered_tasks = []
            
            for task in self.task_registry.values():
                # Filter by task type
                if task_type and task.task_type != task_type:
                    continue
                
                # Filter by status
                if status and task.status != status:
                    continue
                
                # Filter by submitter
                if submitter_address and task.task_data.get("submitter_address") != submitter_address:
                    continue
                
                filtered_tasks.append({
                    "task_id": task.task_id,
                    "task_type": task.task_type.value,
                    "task_name": task.task_name,
                    "status": task.status.value,
                    "priority": task.priority,
                    "created_at": task.created_at.isoformat(),
                    "assigned_node": task.assigned_node,
                    "execution_time": task.execution_time,
                    "cost_estimate": task.cost_estimate,
                    "actual_cost": task.actual_cost
                })
            
            # Apply pagination
            total_tasks = len(filtered_tasks)
            paginated_tasks = filtered_tasks[offset:offset + limit]
            
            return {
                "success": True,
                "tasks": paginated_tasks,
                "total_tasks": total_tasks,
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            print(f"❌ Failed to list tasks: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def register_compute_node(
        self,
        node_name: str,
        node_type: str,
        node_address: str,
        node_location: str = "unknown",
        cpu_cores: int = 1,
        memory_gb: float = 1.0,
        storage_gb: float = 10.0,
        gpu_available: bool = False,
        gpu_memory_gb: float = 0.0,
        network_bandwidth_mbps: int = 100,
        max_concurrent_tasks: int = 5,
        supported_task_types: Optional[List[ComputeTaskType]] = None,
        cost_per_hour: float = 0.0,
        security_level: str = "standard",
        custom_config: Optional[Dict[str, Any]] = None,
        node_version: str = "1.0.0"
    ) -> Dict[str, Any]:
        """Register a new compute node"""
        try:
            # Generate node ID
            node_id = str(uuid.uuid4())
            
            # Create compute node
            node = ComputeNode(
                node_id=node_id,
                node_address=node_address,
                node_name=node_name,
                node_type=node_type,
                node_location=node_location,
                cpu_cores=cpu_cores,
                memory_gb=memory_gb,
                storage_gb=storage_gb,
                gpu_available=gpu_available,
                gpu_memory_gb=gpu_memory_gb,
                network_bandwidth_mbps=network_bandwidth_mbps,
                max_concurrent_tasks=max_concurrent_tasks,
                supported_task_types=supported_task_types or list(ComputeTaskType),
                cost_per_hour=cost_per_hour,
                security_level=security_level,
                custom_config=custom_config or {},
                node_version=node_version
            )
            
            # Add to registry
            self.node_registry[node_id] = node
            
            # Update metrics
            self.metrics.total_nodes += 1
            self.metrics.online_nodes += 1
            
            print(f"✅ Compute node registered: {node_id}")
            return {
                "success": True,
                "node_id": node_id,
                "node_name": node_name,
                "node_type": node_type,
                "capabilities": node.node_capabilities
            }
            
        except Exception as e:
            print(f"❌ Failed to register compute node: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_compute_metrics(self) -> Dict[str, Any]:
        """Get compute system metrics"""
        try:
            await self._update_compute_metrics()
            
            return {
                "success": True,
                "metrics": {
                    "total_tasks": self.metrics.total_tasks,
                    "pending_tasks": self.metrics.pending_tasks,
                    "running_tasks": self.metrics.running_tasks,
                    "completed_tasks": self.metrics.completed_tasks,
                    "failed_tasks": self.metrics.failed_tasks,
                    "total_nodes": self.metrics.total_nodes,
                    "online_nodes": self.metrics.online_nodes,
                    "busy_nodes": self.metrics.busy_nodes,
                    "total_compute_time": self.metrics.total_compute_time,
                    "average_execution_time": self.metrics.average_execution_time,
                    "total_gas_used": self.metrics.total_gas_used,
                    "total_cost": self.metrics.total_cost,
                    "system_efficiency": self.metrics.system_efficiency,
                    "network_utilization": self.metrics.network_utilization,
                    "task_success_rate": self.metrics.task_success_rate,
                    "node_reliability_score": self.metrics.node_reliability_score,
                    "resource_utilization": self.metrics.resource_utilization,
                    "last_updated": self.metrics.last_updated.isoformat()
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to get compute metrics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Helper methods
    async def _validate_task(self, task: ComputeTask) -> Dict[str, Any]:
        """Validate compute task"""
        try:
            # Basic validation
            if not task.task_code or len(task.task_code.strip()) == 0:
                return {"valid": False, "error": "Task code is required"}
            
            if task.timeout_seconds <= 0:
                return {"valid": False, "error": "Invalid timeout"}
            
            if task.priority < 1 or task.priority > 10:
                return {"valid": False, "error": "Priority must be between 1 and 10"}
            
            # Security validation
            if self.config.enable_security_scanning:
                security_result = await self._security_scan_task(task)
                if not security_result["secure"]:
                    return {"valid": False, "error": security_result["error"]}
            
            return {"valid": True, "error": ""}
            
        except Exception as e:
            print(f"Error validating task: {e}")
            return {"valid": False, "error": str(e)}
    
    async def _estimate_task_cost(self, task: ComputeTask) -> Dict[str, Any]:
        """Estimate task execution cost"""
        try:
            # Simple cost estimation based on task type and complexity
            base_cost = 0.01  # Base cost in tokens
            
            # Task type multiplier
            type_multipliers = {
                ComputeTaskType.SMART_CONTRACT: 2.0,
                ComputeTaskType.DAO_GOVERNANCE: 1.5,
                ComputeTaskType.VOTING_CALCULATION: 1.0,
                ComputeTaskType.TREASURY_OPERATION: 3.0,
                ComputeTaskType.PROPOSAL_EXECUTION: 2.5,
                ComputeTaskType.DATA_ANALYSIS: 1.2,
                ComputeTaskType.MACHINE_LEARNING: 4.0,
                ComputeTaskType.CRYPTOGRAPHIC_OPERATION: 2.0,
                ComputeTaskType.VALIDATION_TASK: 1.0,
                ComputeTaskType.BACKGROUND_PROCESS: 0.5
            }
            
            multiplier = type_multipliers.get(task.task_type, 1.0)
            
            # Code complexity factor (simple heuristic)
            code_complexity = len(task.task_code.split('\n')) / 100.0
            complexity_factor = min(code_complexity, 3.0)
            
            # Estimated cost
            estimated_cost = base_cost * multiplier * complexity_factor * (task.priority / 5.0)
            
            # Estimated duration (in seconds)
            estimated_duration = 30 + (len(task.task_code.split('\n')) * 0.5)
            
            return {
                "estimated_cost": estimated_cost,
                "estimated_duration": estimated_duration,
                "base_cost": base_cost,
                "multiplier": multiplier,
                "complexity_factor": complexity_factor
            }
            
        except Exception as e:
            print(f"Error estimating task cost: {e}")
            return {
                "estimated_cost": 0.01,
                "estimated_duration": 60,
                "base_cost": 0.01,
                "multiplier": 1.0,
                "complexity_factor": 1.0
            }
    
    async def _security_scan_task(self, task: ComputeTask) -> Dict[str, Any]:
        """Security scan task code"""
        try:
            # Simple security checks
            dangerous_patterns = [
                "import os",
                "import sys",
                "exec(",
                "eval(",
                "__import__",
                "subprocess",
                "open(",
                "file(",
                "input(",
                "raw_input",
                "socket",
                "urllib",
                "requests"
            ]
            
            for pattern in dangerous_patterns:
                if pattern in task.task_code:
                    return {
                        "secure": False,
                        "error": f"Potentially dangerous pattern found: {pattern}"
                    }
            
            return {"secure": True, "error": ""}
            
        except Exception as e:
            print(f"Error in security scan: {e}")
            return {"secure": False, "error": str(e)}
    
    def _task_processor_loop(self) -> None:
        """Task processor loop (runs in separate thread)"""
        while True:
            try:
                if not self.task_queue.empty():
                    priority, task_id = self.task_queue.get()
                    
                    if task_id in self.task_registry:
                        task = self.task_registry[task_id]
                        
                        if task.status == ComputeTaskStatus.PENDING:
                            asyncio.run(self._execute_task(task))
                
                time.sleep(0.1)  # Small delay to prevent CPU spinning
                
            except Exception as e:
                print(f"Task processor error: {e}")
                time.sleep(1)
    
    async def _execute_task(self, task: ComputeTask) -> None:
        """Execute compute task"""
        try:
            # Update task status
            task.status = ComputeTaskStatus.RUNNING
            task.started_at = datetime.now()
            self.metrics.pending_tasks -= 1
            self.metrics.running_tasks += 1
            
            # Find available node
            node = await self._find_available_node(task)
            if not node:
                task.status = ComputeTaskStatus.FAILED
                task.error_message = "No available compute nodes"
                self.metrics.running_tasks -= 1
                self.metrics.failed_tasks += 1
                return
            
            # Assign task to node
            task.assigned_node = node.node_id
            node.active_tasks += 1
            node.current_load = node.active_tasks / node.max_concurrent_tasks
            
            # Execute task
            start_time = time.time()
            
            try:
                result = await self._execute_task_on_node(task, node)
                
                if result["success"]:
                    # Task completed successfully
                    task.status = ComputeTaskStatus.COMPLETED
                    task.result_data = result["result_data"]
                    task.execution_time = time.time() - start_time
                    task.completed_at = datetime.now()
                    task.gas_used = result.get("gas_used", 0)
                    task.actual_cost = result.get("actual_cost", 0.0)
                    task.validation_result = result.get("validation_result", {})
                    
                    # Update node statistics
                    node.completed_tasks += 1
                    node.last_task_completion = datetime.now()
                    
                    # Update metrics
                    self.metrics.completed_tasks += 1
                    self.metrics.total_compute_time += task.execution_time
                    self.metrics.total_gas_used += task.gas_used
                    self.metrics.total_cost += task.actual_cost
                    
                    print(f"✅ Task completed: {task.task_id}")
                    
                else:
                    # Task failed
                    task.status = ComputeTaskStatus.FAILED
                    task.error_message = result["error"]
                    task.retry_count += 1
                    
                    # Update node statistics
                    node.failed_tasks += 1
                    
                    # Update metrics
                    self.metrics.failed_tasks += 1
                    
                    print(f"❌ Task failed: {task.task_id} - {result['error']}")
                    
            except Exception as e:
                # Task execution error
                task.status = ComputeTaskStatus.FAILED
                task.error_message = str(e)
                task.retry_count += 1
                
                node.failed_tasks += 1
                self.metrics.failed_tasks += 1
                
                print(f"❌ Task execution error: {task.task_id} - {e}")
            
            # Update node load
            node.active_tasks -= 1
            node.current_load = node.active_tasks / node.max_concurrent_tasks
            
            # Update metrics
            self.metrics.running_tasks -= 1
            
        except Exception as e:
            print(f"Error executing task: {e}")
            task.status = ComputeTaskStatus.FAILED
            task.error_message = str(e)
    
    async def _find_available_node(self, task: ComputeTask) -> Optional[ComputeNode]:
        """Find available compute node for task"""
        try:
            available_nodes = []
            
            for node in self.node_registry.values():
                # Check node status
                if node.node_status != ComputeNodeStatus.ONLINE:
                    continue
                
                # Check task type support
                if task.task_type not in node.supported_task_types:
                    continue
                
                # Check node capacity
                if node.active_tasks >= node.max_concurrent_tasks:
                    continue
                
                # Check reliability
                if node.reliability_score < self.config.min_node_reliability:
                    continue
                
                available_nodes.append(node)
            
            if not available_nodes:
                return None
            
            # Select node based on strategy
            if self.config.resource_allocation_strategy == "balanced":
                # Select node with lowest load
                return min(available_nodes, key=lambda n: n.current_load)
            elif self.config.resource_allocation_strategy == "performance":
                # Select node with best performance metrics
                return max(available_nodes, key=lambda n: n.average_execution_time)
            elif self.config.resource_allocation_strategy == "cost":
                # Select node with lowest cost
                return min(available_nodes, key=lambda n: n.cost_per_hour)
            else:
                # Default to balanced
                return min(available_nodes, key=lambda n: n.current_load)
            
        except Exception as e:
            print(f"Error finding available node: {e}")
            return None
    
    async def _execute_task_on_node(self, task: ComputeTask, node: ComputeNode) -> Dict[str, Any]:
        """Execute task on specific node"""
        try:
            # Simulate task execution
            execution_time = 2.0 + (len(task.task_code.split('\n')) * 0.1)
            
            # Simulate result
            result_data = {
                "task_output": f"Task {task.task_id} executed successfully",
                "execution_time": execution_time,
                "node_id": node.node_id,
                "task_type": task.task_type.value,
                "result_hash": hashlib.sha256(f"{task.task_id}:{time.time()}".encode()).hexdigest()
            }
            
            # Simulate gas usage and cost
            gas_used = min(task.gas_limit, 100000 + (len(task.task_code) * 10))
            actual_cost = gas_used * 0.000000001  # Simple cost calculation
            
            # Simulate validation
            validation_result = {
                "status": "validated",
                "validation_hash": hashlib.sha256(f"{result_data['result_hash']}".encode()).hexdigest(),
                "validator_nodes": ["node1", "node2", "node3"]
            }
            
            return {
                "success": True,
                "result_data": result_data,
                "gas_used": gas_used,
                "actual_cost": actual_cost,
                "validation_result": validation_result
            }
            
        except Exception as e:
            print(f"Error executing task on node: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _stop_running_task(self, task_id: str) -> None:
        """Stop a running task"""
        try:
            # In a real implementation, this would stop the task execution
            # For now, we'll just update the task status
            if task_id in self.task_registry:
                task = self.task_registry[task_id]
                task.status = ComputeTaskStatus.CANCELLED
                print(f"Task stopped: {task_id}")
            
        except Exception as e:
            print(f"Error stopping task: {e}")
    
    def _monitoring_loop(self) -> None:
        """Monitoring loop (runs in separate thread)"""
        while self.monitoring_active:
            try:
                asyncio.run(self._update_compute_metrics())
                asyncio.run(self._check_node_health())
                time.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(10)
    
    async def _update_compute_metrics(self) -> None:
        """Update compute metrics"""
        try:
            # Update task metrics
            self.metrics.pending_tasks = len([t for t in self.task_registry.values() if t.status == ComputeTaskStatus.PENDING])
            self.metrics.running_tasks = len([t for t in self.task_registry.values() if t.status == ComputeTaskStatus.RUNNING])
            self.metrics.completed_tasks = len([t for t in self.task_registry.values() if t.status == ComputeTaskStatus.COMPLETED])
            self.metrics.failed_tasks = len([t for t in self.task_registry.values() if t.status == ComputeTaskStatus.FAILED])
            
            # Update node metrics
            self.metrics.online_nodes = len([n for n in self.node_registry.values() if n.node_status == ComputeNodeStatus.ONLINE])
            self.metrics.busy_nodes = len([n for n in self.node_registry.values() if n.active_tasks > 0])
            
            # Calculate success rate
            total_completed = self.metrics.completed_tasks + self.metrics.failed_tasks
            if total_completed > 0:
                self.metrics.task_success_rate = self.metrics.completed_tasks / total_completed
            
            # Calculate average execution time
            completed_tasks = [t for t in self.task_registry.values() if t.status == ComputeTaskStatus.COMPLETED and t.execution_time > 0]
            if completed_tasks:
                self.metrics.average_execution_time = sum(t.execution_time for t in completed_tasks) / len(completed_tasks)
            
            # Calculate node reliability
            if self.node_registry:
                self.metrics.node_reliability_score = sum(n.reliability_score for n in self.node_registry.values()) / len(self.node_registry)
            
            self.metrics.last_updated = datetime.now()
            
        except Exception as e:
            print(f"Error updating compute metrics: {e}")
    
    async def _check_node_health(self) -> None:
        """Check compute node health"""
        try:
            for node in self.node_registry.values():
                # Simple health check - in real implementation, you'd ping the node
                node.last_heartbeat = datetime.now()
                
                # Update reliability score based on recent performance
                if node.completed_tasks + node.failed_tasks > 0:
                    success_rate = node.completed_tasks / (node.completed_tasks + node.failed_tasks)
                    node.reliability_score = success_rate
                
        except Exception as e:
            print(f"Error checking node health: {e}")
    
    async def _load_existing_data(self) -> None:
        """Load existing data from Redis"""
        try:
            # Load task registry
            tasks_data = await self.redis_client.get("compute_tasks")
            if tasks_data:
                self.task_registry = pickle.loads(tasks_data)
            
            # Load node registry
            nodes_data = await self.redis_client.get("compute_nodes")
            if nodes_data:
                self.node_registry = pickle.loads(nodes_data)
            
        except Exception as e:
            print(f"Error loading existing data: {e}")
    
    async def _initialize_compute_nodes(self) -> None:
        """Initialize compute nodes"""
        try:
            # Add local compute node
            await self.register_compute_node(
                node_name="SANGKURIANG Local Node",
                node_type="native",
                node_address="local://localhost:8080",
                cpu_cores=os.cpu_count() or 4,
                memory_gb=psutil.virtual_memory().total / (1024**3),
                storage_gb=psutil.disk_usage('/').total / (1024**3),
                max_concurrent_tasks=10,
                supported_task_types=list(ComputeTaskType),
                cost_per_hour=0.0,
                security_level="high"
            )
            
        except Exception as e:
            print(f"Error initializing compute nodes: {e}")
    
    async def _initialize_compute_resources(self) -> None:
        """Initialize compute resources"""
        try:
            # CPU resource
            cpu_resource = ComputeResource(
                resource_id="cpu_main",
                resource_type=ResourceType.CPU,
                resource_name="Main CPU",
                total_capacity=psutil.cpu_count() or 4,
                resource_unit="cores",
                resource_location="local"
            )
            self.resource_registry[cpu_resource.resource_id] = cpu_resource
            
            # Memory resource
            memory_gb = psutil.virtual_memory().total / (1024**3)
            memory_resource = ComputeResource(
                resource_id="memory_main",
                resource_type=ResourceType.MEMORY,
                resource_name="Main Memory",
                total_capacity=memory_gb,
                resource_unit="GB",
                resource_location="local"
            )
            self.resource_registry[memory_resource.resource_id] = memory_resource
            
        except Exception as e:
            print(f"Error initializing compute resources: {e}")


# Example usage and testing
async def test_decentralized_compute_system():
    """Test SANGKURIANG Decentralized Compute System"""
    print("🚀 Testing SANGKURIANG Decentralized Compute System")
    
    # Initialize system
    compute_system = DecentralizedComputeSystem(
        docker_enabled=False,  # Disable Docker for testing
        enable_monitoring=True
    )
    
    # Wait for system initialization
    await asyncio.sleep(2)
    
    # Test tasks
    test_tasks = [
        {
            "task_type": ComputeTaskType.SMART_CONTRACT,
            "task_name": "DAO Governance Vote",
            "task_description": "Execute DAO governance voting mechanism",
            "task_code": """
def execute_governance_vote(votes, proposal_id):
    total_votes = sum(votes.values())
    if total_votes == 0:
        return {"status": "failed", "reason": "No votes"}
    
    yes_votes = votes.get("yes", 0)
    no_votes = votes.get("no", 0)
    
    approval_rate = yes_votes / total_votes
    
    return {
        "proposal_id": proposal_id,
        "total_votes": total_votes,
        "yes_votes": yes_votes,
        "no_votes": no_votes,
        "approval_rate": approval_rate,
        "approved": approval_rate > 0.5,
        "status": "completed"
    }
            """,
            "task_data": {
                "votes": {"yes": 75, "no": 25},
                "proposal_id": "PROPOSAL_001",
                "submitter_address": "0x1111111111111111111111111111111111111111"
            },
            "priority": 5
        },
        {
            "task_type": ComputeTaskType.VOTING_CALCULATION,
            "task_name": "Treasury Allocation",
            "task_description": "Calculate treasury fund allocation",
            "task_code": """
def calculate_treasury_allocation(total_funds, proposals):
    allocations = {}
    total_requested = sum(p.get("requested_amount", 0) for p in proposals)
    
    if total_requested == 0:
        return {"status": "failed", "reason": "No funding requests"}
    
    for proposal in proposals:
        requested = proposal.get("requested_amount", 0)
        priority = proposal.get("priority", 1)
        
        # Calculate allocation based on priority and available funds
        allocation_ratio = min(requested / total_requested * priority, 1.0)
        allocated_amount = min(requested, total_funds * allocation_ratio)
        
        allocations[proposal["id"]] = {
            "requested": requested,
            "allocated": allocated_amount,
            "priority": priority,
            "allocation_ratio": allocation_ratio
        }
    
    return {
        "total_funds": total_funds,
        "total_requested": total_requested,
        "allocations": allocations,
        "status": "completed"
    }
            """,
            "task_data": {
                "total_funds": 1000000,
                "proposals": [
                    {"id": "PROP_001", "requested_amount": 100000, "priority": 3},
                    {"id": "PROP_002", "requested_amount": 200000, "priority": 2},
                    {"id": "PROP_003", "requested_amount": 150000, "priority": 1}
                ],
                "submitter_address": "0x1111111111111111111111111111111111111111"
            },
            "priority": 7
        },
        {
            "task_type": ComputeTaskType.DATA_ANALYSIS,
            "task_name": "Community Metrics",
            "task_description": "Analyze community engagement metrics",
            "task_code": """
def analyze_community_metrics(member_data, activity_data):
    total_members = len(member_data)
    active_members = len([m for m in member_data if m.get("status") == "active"])
    
    # Calculate engagement metrics
    total_activities = len(activity_data)
    member_activities = {}
    
    for activity in activity_data:
        member_id = activity.get("member_id")
        if member_id not in member_activities:
            member_activities[member_id] = 0
        member_activities[member_id] += 1
    
    avg_activities_per_member = total_activities / total_members if total_members > 0 else 0
    
    # Calculate participation rate
    participating_members = len([count for count in member_activities.values() if count > 0])
    participation_rate = participating_members / total_members if total_members > 0 else 0
    
    return {
        "total_members": total_members,
        "active_members": active_members,
        "total_activities": total_activities,
        "avg_activities_per_member": avg_activities_per_member,
        "participating_members": participating_members,
        "participation_rate": participation_rate,
        "activity_distribution": member_activities,
        "status": "completed"
    }
            """,
            "task_data": {
                "member_data": [
                    {"id": "MEM_001", "status": "active"},
                    {"id": "MEM_002", "status": "active"},
                    {"id": "MEM_003", "status": "inactive"},
                    {"id": "MEM_004", "status": "active"}
                ],
                "activity_data": [
                    {"member_id": "MEM_001", "activity_type": "vote"},
                    {"member_id": "MEM_001", "activity_type": "proposal"},
                    {"member_id": "MEM_002", "activity_type": "vote"},
                    {"member_id": "MEM_004", "activity_type": "comment"}
                ],
                "submitter_address": "0x1111111111111111111111111111111111111111"
            },
            "priority": 3
        }
    ]
    
    # Submit tasks
    submitted_tasks = []
    for task_data in test_tasks:
        result = await compute_system.submit_task(
            task_type=task_data["task_type"],
            task_name=task_data["task_name"],
            task_description=task_data["task_description"],
            task_data=task_data["task_data"],
            task_code=task_data["task_code"],
            priority=task_data["priority"],
            submitter_address=task_data["task_data"]["submitter_address"]
        )
        
        if result["success"]:
            submitted_tasks.append(result["task_id"])
            print(f"✅ Task submitted: {result['task_id']}")
    
    # Wait for tasks to complete
    print("⏳ Waiting for tasks to complete...")
    await asyncio.sleep(10)
    
    # Check task status
    for task_id in submitted_tasks:
        status_result = await compute_system.get_task_status(task_id)
        if status_result["success"]:
            print(f"📋 Task {task_id} status: {status_result['task']['status']}")
    
    # Get task results
    for task_id in submitted_tasks:
        result_result = await compute_system.get_task_result(task_id)
        if result_result["success"]:
            print(f"✅ Task {task_id} result:")
            print(json.dumps(result_result["result"], indent=2, default=str))
    
    # List all tasks
    tasks_result = await compute_system.list_tasks()
    if tasks_result["success"]:
        print(f"📋 Total tasks: {tasks_result['total_tasks']}")
        for task in tasks_result["tasks"]:
            print(f"  - {task['task_name']} ({task['status']})")
    
    # Get compute metrics
    metrics_result = await compute_system.get_compute_metrics()
    if metrics_result["success"]:
        print(f"📊 Compute Metrics:")
        print(json.dumps(metrics_result["metrics"], indent=2, default=str))
    
    # Test task cancellation
    print("🧪 Testing task cancellation...")
    cancel_result = await compute_system.cancel_task(
        task_id=submitted_tasks[0],
        requester_address="0x1111111111111111111111111111111111111111"
    )
    print(f"Task cancellation result: {cancel_result}")
    
    print("\n🎉 Decentralized compute system test completed!")


if __name__ == "__main__":
    asyncio.run(test_decentralized_compute_system())