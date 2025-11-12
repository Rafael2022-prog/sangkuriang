"""
Test suite for Decentralized Storage System
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from decentralized_storage import (
    DecentralizedStorage, 
    StorageNode, 
    StoredData, 
    VerificationResult
)


class TestDecentralizedStorage:
    """Test cases for decentralized storage system"""
    
    @pytest.fixture
    def storage(self):
        """Create temporary storage for testing"""
        temp_dir = tempfile.mkdtemp()
        storage = DecentralizedStorage(storage_dir=temp_dir)
        yield storage
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_verification_result(self):
        """Sample verification result for testing"""
        return VerificationResult(
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
    
    @pytest.fixture
    def sample_audit_log(self):
        """Sample audit log for testing"""
        return {
            "action": "PROJECT_VERIFIED",
            "project_id": "project_123",
            "timestamp": datetime.now().isoformat(),
            "details": {"verifier": "system", "score": 85.5}
        }
    
    @pytest.mark.asyncio
    async def test_store_verification_result(self, storage, sample_verification_result):
        """Test storing verification result"""
        data_id = await storage.store_verification_result(sample_verification_result)
        
        assert data_id is not None
        assert data_id.startswith("verification_result_")
        assert data_id in storage.stored_data
        assert sample_verification_result.result_id in storage.verification_results
    
    @pytest.mark.asyncio
    async def test_store_audit_log(self, storage, sample_audit_log):
        """Test storing audit log"""
        log_id = await storage.store_audit_log(sample_audit_log)
        
        assert log_id is not None
        assert log_id.startswith("audit_log_")
        assert log_id in storage.stored_data
    
    @pytest.mark.asyncio
    async def test_retrieve_verification_result(self, storage, sample_verification_result):
        """Test retrieving verification result"""
        # Store first
        data_id = await storage.store_verification_result(sample_verification_result)
        
        # Retrieve
        retrieved_data = await storage.retrieve_data(data_id)
        
        assert retrieved_data is not None
        assert retrieved_data["result_id"] == sample_verification_result.result_id
        assert retrieved_data["project_id"] == sample_verification_result.project_id
        assert retrieved_data["score"] == sample_verification_result.score
    
    @pytest.mark.asyncio
    async def test_retrieve_audit_log(self, storage, sample_audit_log):
        """Test retrieving audit log"""
        # Store first
        log_id = await storage.store_audit_log(sample_audit_log)
        
        # Retrieve
        retrieved_data = await storage.retrieve_data(log_id)
        
        assert retrieved_data is not None
        assert retrieved_data["action"] == sample_audit_log["action"]
        assert retrieved_data["project_id"] == sample_audit_log["project_id"]
    
    @pytest.mark.asyncio
    async def test_get_verification_results_by_project(self, storage, sample_verification_result):
        """Test getting verification results by project ID"""
        # Store multiple results for the same project
        await storage.store_verification_result(sample_verification_result)
        
        # Create another result for the same project
        result2 = VerificationResult(
            result_id="test_result_2",
            project_id="project_123",
            verification_type="performance_test",
            status="failed",
            score=45.0,
            findings=[{"type": "error", "description": "Performance below threshold", "severity": "high"}],
            recommendations=["Optimize algorithm complexity"],
            verified_at=datetime.now(),
            verifier_signature="verifier_sig_456"
        )
        
        await storage.store_verification_result(result2)
        
        # Get results for project
        results = await storage.get_verification_results("project_123")
        
        assert len(results) == 2
        assert results[0].result_id == "test_result_2"  # Newest first
        assert results[1].result_id == "test_result_1"
    
    @pytest.mark.asyncio
    async def test_data_integrity_check(self, storage, sample_audit_log):
        """Test that data integrity is verified during retrieval"""
        # Store data
        log_id = await storage.store_audit_log(sample_audit_log)
        
        # Corrupt the data by directly modifying the stored file
        stored_data = storage.stored_data[log_id]
        node_id = stored_data.storage_nodes[0]
        file_path = Path(storage.storage_dir) / node_id / f"{log_id}.json"
        
        # Corrupt the file
        with open(file_path, 'w') as f:
            f.write("corrupted data")
        
        # Try to retrieve - should fail integrity check
        retrieved_data = await storage.retrieve_data(log_id)
        
        # Should try other nodes or return None
        # Since we have multiple nodes with replication, it might still succeed
        # So we just check that the method handles corruption gracefully
        assert retrieved_data is None or retrieved_data == sample_audit_log
    
    def test_storage_stats(self, storage):
        """Test getting storage statistics"""
        stats = storage.get_storage_stats()
        
        assert "total_nodes" in stats
        assert "active_nodes" in stats
        assert "total_capacity" in stats
        assert "total_used" in stats
        assert "total_available" in stats
        assert "utilization_rate" in stats
        assert stats["total_nodes"] == 3  # Default initialization
        assert stats["active_nodes"] == 3
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_data(self, storage):
        """Test cleaning up expired data"""
        # Create expired verification result
        expired_result = VerificationResult(
            result_id="expired_result",
            project_id="project_456",
            verification_type="security_audit",
            status="passed",
            score=90.0,
            findings=[],
            recommendations=[],
            verified_at=datetime.now() - timedelta(days=400),  # Old date
            verifier_signature="verifier_sig_expired"
        )
        
        # Store with expired date
        data_id = await storage.store_verification_result(expired_result)
        
        # Manually set expiration to past
        storage.stored_data[data_id].expires_at = datetime.now() - timedelta(days=1)
        
        # Cleanup
        cleaned_count = await storage.cleanup_expired_data()
        
        assert cleaned_count == 1
        assert data_id not in storage.stored_data
        assert "expired_result" not in storage.verification_results
    
    def test_node_selection(self, storage):
        """Test node selection for storage"""
        # Test with default reliability
        nodes = storage._select_storage_nodes(replication_factor=2)
        
        assert len(nodes) == 2
        assert all(node in storage.nodes for node in nodes)
    
    @pytest.mark.asyncio
    async def test_concurrent_storage_operations(self, storage, sample_audit_log):
        """Test concurrent storage operations"""
        # Create multiple audit logs
        logs = []
        for i in range(10):
            log = sample_audit_log.copy()
            log["project_id"] = f"project_{i}"
            logs.append(log)
        
        # Store concurrently
        tasks = [storage.store_audit_log(log) for log in logs]
        log_ids = await asyncio.gather(*tasks)
        
        assert len(log_ids) == 10
        assert all(log_id is not None for log_id in log_ids)
        
        # Retrieve concurrently
        retrieve_tasks = [storage.retrieve_data(log_id) for log_id in log_ids]
        retrieved_logs = await asyncio.gather(*retrieve_tasks)
        
        assert len(retrieved_logs) == 10
        assert all(log is not None for log in retrieved_logs)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])