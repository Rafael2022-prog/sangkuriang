"""
Decentralized Storage System for SANGKURIANG
Handles distributed storage of audit logs and verification results
"""

import json
import hashlib
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import asyncio
from pathlib import Path


@dataclass
class StorageNode:
    """Represents a storage node in the decentralized network"""
    node_id: str
    address: str
    capacity: int
    available_space: int
    reliability_score: float
    last_seen: datetime
    is_active: bool


@dataclass
class StoredData:
    """Represents data stored in the decentralized system"""
    data_id: str
    content_hash: str
    storage_nodes: List[str]
    replication_factor: int
    created_at: datetime
    expires_at: Optional[datetime]
    data_type: str  # 'audit_log', 'verification_result', 'backup'
    size: int


@dataclass
class VerificationResult:
    """Represents a cryptographic verification result"""
    result_id: str
    project_id: str
    verification_type: str  # 'security_audit', 'performance_test', 'plagiarism_check'
    status: str  # 'passed', 'failed', 'warning'
    score: float  # 0-100
    findings: List[Dict[str, Any]]
    recommendations: List[str]
    verified_at: datetime
    verifier_signature: str


class DecentralizedStorage:
    """
    Decentralized storage system for audit logs and verification results
    Implements data replication and integrity checking
    """
    
    def __init__(self, storage_dir: str = "./decentralized_data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Storage nodes (simulated for demo)
        self.nodes: Dict[str, StorageNode] = {}
        self.stored_data: Dict[str, StoredData] = {}
        self.verification_results: Dict[str, VerificationResult] = {}
        
        # Initialize with local storage nodes
        self._initialize_nodes()
    
    def _initialize_nodes(self):
        """Initialize storage nodes"""
        for i in range(3):
            node_id = f"node_{i}"
            node = StorageNode(
                node_id=node_id,
                address=f"127.0.0.1:{8000 + i}",
                capacity=1000000,  # 1GB
                available_space=1000000,
                reliability_score=0.95,
                last_seen=datetime.now(),
                is_active=True
            )
            self.nodes[node_id] = node
    
    def _generate_data_id(self, content: str, data_type: str) -> str:
        """Generate unique data ID based on content hash"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        timestamp = str(int(time.time()))
        return f"{data_type}_{content_hash[:16]}_{timestamp}"
    
    def _select_storage_nodes(self, replication_factor: int = 3) -> List[str]:
        """Select nodes for data storage based on reliability and availability"""
        available_nodes = [
            node for node in self.nodes.values() 
            if node.is_active and node.available_space > 0
        ]
        
        # Sort by reliability score
        available_nodes.sort(key=lambda x: x.reliability_score, reverse=True)
        
        # Select top nodes
        selected = available_nodes[:replication_factor]
        return [node.node_id for node in selected]
    
    async def store_audit_log(self, audit_log: Dict[str, Any]) -> str:
        """Store audit log in decentralized system"""
        
        # Convert to JSON for storage
        log_json = json.dumps(audit_log, default=str)
        data_id = self._generate_data_id(log_json, "audit_log")
        
        # Select storage nodes
        storage_nodes = self._select_storage_nodes()
        
        # Create metadata
        stored_data = StoredData(
            data_id=data_id,
            content_hash=hashlib.sha256(log_json.encode()).hexdigest(),
            storage_nodes=storage_nodes,
            replication_factor=len(storage_nodes),
            created_at=datetime.now(),
            expires_at=None,  # Audit logs don't expire
            data_type="audit_log",
            size=len(log_json.encode())
        )
        
        # Store data (simulate distributed storage)
        await self._store_to_nodes(data_id, log_json, storage_nodes)
        
        self.stored_data[data_id] = stored_data
        
        return data_id
    
    async def store_verification_result(self, result: VerificationResult) -> str:
        """Store verification result in decentralized system"""
        
        # Convert to dict
        result_dict = asdict(result)
        result_json = json.dumps(result_dict, default=str)
        data_id = self._generate_data_id(result_json, "verification_result")
        
        # Select storage nodes
        storage_nodes = self._select_storage_nodes()
        
        # Create metadata
        stored_data = StoredData(
            data_id=data_id,
            content_hash=hashlib.sha256(result_json.encode()).hexdigest(),
            storage_nodes=storage_nodes,
            replication_factor=len(storage_nodes),
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=365),  # Results expire after 1 year
            data_type="verification_result",
            size=len(result_json.encode())
        )
        
        # Store data
        await self._store_to_nodes(data_id, result_json, storage_nodes)
        
        self.stored_data[data_id] = stored_data
        self.verification_results[result.result_id] = result
        
        return data_id
    
    async def _store_to_nodes(self, data_id: str, content: str, nodes: List[str]):
        """Simulate storing data to multiple nodes"""
        # In a real implementation, this would make network calls
        # For demo, we'll store locally in separate directories
        
        for node_id in nodes:
            node_dir = self.storage_dir / node_id
            node_dir.mkdir(exist_ok=True)
            
            file_path = node_dir / f"{data_id}.json"
            
            # Simulate network delay
            await asyncio.sleep(0.01)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Update node available space
            if node_id in self.nodes:
                self.nodes[node_id].available_space -= len(content.encode())
    
    async def retrieve_data(self, data_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from decentralized storage"""
        
        stored_data = self.stored_data.get(data_id)
        if not stored_data:
            return None
        
        # Try to retrieve from available nodes
        for node_id in stored_data.storage_nodes:
            if node_id in self.nodes and self.nodes[node_id].is_active:
                file_path = self.storage_dir / node_id / f"{data_id}.json"
                
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Verify integrity
                        content_hash = hashlib.sha256(content.encode()).hexdigest()
                        if content_hash == stored_data.content_hash:
                            return json.loads(content)
                        else:
                            print(f"Data integrity check failed for {data_id}")
                    
                    except Exception as e:
                        print(f"Error retrieving from node {node_id}: {e}")
                        continue
        
        return None
    
    async def get_verification_results(self, project_id: str) -> List[VerificationResult]:
        """Get all verification results for a project"""
        
        results = []
        for result in self.verification_results.values():
            if result.project_id == project_id:
                results.append(result)
        
        # Sort by verification date (newest first)
        results.sort(key=lambda x: x.verified_at, reverse=True)
        return results
    
    async def cleanup_expired_data(self) -> int:
        """Clean up expired data"""
        
        current_time = datetime.now()
        expired_count = 0
        
        expired_data_ids = []
        for data_id, stored_data in self.stored_data.items():
            if (stored_data.expires_at and 
                current_time > stored_data.expires_at):
                expired_data_ids.append(data_id)
        
        for data_id in expired_data_ids:
            # Remove from storage
            stored_data = self.stored_data[data_id]
            
            for node_id in stored_data.storage_nodes:
                file_path = self.storage_dir / node_id / f"{data_id}.json"
                if file_path.exists():
                    file_path.unlink()
                    
                    # Restore node space
                    if node_id in self.nodes:
                        self.nodes[node_id].available_space += stored_data.size
            
            # Remove from metadata
            del self.stored_data[data_id]
            
            # Also remove from verification results if applicable
            for result_id, result in list(self.verification_results.items()):
                result_dict = asdict(result)
                result_json = json.dumps(result_dict, default=str)
                if self._generate_data_id(result_json, "verification_result") == data_id:
                    del self.verification_results[result_id]
            
            expired_count += 1
        
        return expired_count
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage system statistics"""
        
        total_capacity = sum(node.capacity for node in self.nodes.values())
        total_available = sum(node.available_space for node in self.nodes.values())
        total_used = total_capacity - total_available
        
        return {
            'total_nodes': len(self.nodes),
            'active_nodes': len([n for n in self.nodes.values() if n.is_active]),
            'total_capacity': total_capacity,
            'total_used': total_used,
            'total_available': total_available,
            'utilization_rate': (total_used / total_capacity) * 100 if total_capacity > 0 else 0,
            'stored_data_count': len(self.stored_data),
            'verification_results_count': len(self.verification_results),
            'replication_factor': 3  # Default
        }


# Example usage and testing
if __name__ == "__main__":
    async def demo():
        storage = DecentralizedStorage()
        
        # Create sample verification result
        result = VerificationResult(
            result_id="test_result_1",
            project_id="project_123",
            verification_type="security_audit",
            status="passed",
            score=85.5,
            findings=[
                {"type": "warning", "description": "Weak key size detected", "severity": "medium"},
                {"type": "info", "description": "Algorithm is quantum-resistant", "severity": "low"}
            ],
            recommendations=["Consider increasing key size", "Implement additional entropy sources"],
            verified_at=datetime.now(),
            verifier_signature="verifier_sig_123"
        )
        
        # Store verification result
        data_id = await storage.store_verification_result(result)
        print(f"Stored verification result with ID: {data_id}")
        
        # Store audit log
        audit_log = {
            "action": "PROJECT_VERIFIED",
            "project_id": "project_123",
            "timestamp": datetime.now().isoformat(),
            "details": {"verifier": "system", "score": 85.5}
        }
        
        log_id = await storage.store_audit_log(audit_log)
        print(f"Stored audit log with ID: {log_id}")
        
        # Retrieve data
        retrieved_result = await storage.retrieve_data(data_id)
        print(f"Retrieved result: {retrieved_result}")
        
        # Get project verification results
        project_results = await storage.get_verification_results("project_123")
        print(f"Project has {len(project_results)} verification results")
        
        # Get storage stats
        stats = storage.get_storage_stats()
        print(f"Storage stats: {json.dumps(stats, indent=2)}")
    
    asyncio.run(demo())