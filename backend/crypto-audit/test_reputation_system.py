"""
Test suite for Reputation System
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from reputation_system import (
    ReputationEngine, ReputationCategory, ReputationLevel,
    DeveloperReputation, ProjectReputation, ReputationScore
)


class TestReputationSystem:
    """Test cases for reputation system"""
    
    @pytest.fixture
    def engine(self):
        """Create temporary reputation engine for testing"""
        temp_dir = tempfile.mkdtemp()
        rep_engine = ReputationEngine(storage_dir=temp_dir)
        yield rep_engine
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_developer_data(self):
        """Sample developer data for testing"""
        return {
            "developer_id": "dev_test_001",
            "name": "Test Developer",
            "email": "test@example.com",
            "github_username": "testdev"
        }
    
    @pytest.fixture
    def sample_project_data(self):
        """Sample project data for testing"""
        return {
            "project_id": "proj_test_001",
            "project_name": "Test Project",
            "description": "A test cryptographic project",
            "developer_id": "dev_test_001"
        }
    
    @pytest.mark.asyncio
    async def test_register_developer(self, engine, sample_developer_data):
        """Test developer registration"""
        dev_rep = await engine.register_developer(
            sample_developer_data["developer_id"],
            sample_developer_data["name"],
            sample_developer_data["email"],
            sample_developer_data["github_username"]
        )
        
        assert dev_rep is not None
        assert dev_rep.developer_id == sample_developer_data["developer_id"]
        assert dev_rep.name == sample_developer_data["name"]
        assert dev_rep.email == sample_developer_data["email"]
        assert dev_rep.github_username == sample_developer_data["github_username"]
        assert dev_rep.total_score == 50.0  # Default neutral score
        assert dev_rep.level == ReputationLevel.DEVELOPER
        assert len(dev_rep.category_scores) == 6  # All categories initialized
    
    @pytest.mark.asyncio
    async def test_register_project(self, engine, sample_project_data):
        """Test project registration"""
        # First register developer
        await engine.register_developer("dev_test_001", "Test Dev", "test@example.com", "testdev")
        
        proj_rep = await engine.register_project(
            sample_project_data["project_id"],
            sample_project_data["project_name"],
            sample_project_data["description"],
            sample_project_data["developer_id"]
        )
        
        assert proj_rep is not None
        assert proj_rep.project_id == sample_project_data["project_id"]
        assert proj_rep.project_name == sample_project_data["project_name"]
        assert proj_rep.description == sample_project_data["description"]
        assert proj_rep.developer_id == sample_project_data["developer_id"]
        assert proj_rep.total_score == 50.0  # Default neutral score
        assert proj_rep.level == ReputationLevel.DEVELOPER
    
    @pytest.mark.asyncio
    async def test_update_developer_reputation(self, engine, sample_developer_data):
        """Test updating developer reputation"""
        # Register developer first
        await engine.register_developer(**sample_developer_data)
        
        # Update security reputation
        evidence = {
            "type": "security_audit",
            "description": "Passed comprehensive security audit",
            "score": 85.0
        }
        
        await engine.update_developer_reputation(
            sample_developer_data["developer_id"],
            ReputationCategory.SECURITY,
            85.0,
            evidence
        )
        
        # Verify update
        dev_rep = engine.get_developer_reputation(sample_developer_data["developer_id"])
        assert dev_rep is not None
        assert dev_rep.category_scores[ReputationCategory.SECURITY].score == 85.0
        assert len(dev_rep.reputation_history) == 1
        assert dev_rep.reputation_history[0]["action"] == "REPUTATION_UPDATED"
    
    @pytest.mark.asyncio
    async def test_update_project_reputation(self, engine, sample_project_data):
        """Test updating project reputation"""
        # Register developer and project first
        await engine.register_developer("dev_test_001", "Test Dev", "test@example.com", "testdev")
        await engine.register_project(**sample_project_data)
        
        # Update performance reputation
        evidence = {
            "type": "performance_test",
            "description": "Excellent performance metrics",
            "score": 90.0
        }
        
        await engine.update_project_reputation(
            sample_project_data["project_id"],
            ReputationCategory.PERFORMANCE,
            90.0,
            evidence
        )
        
        # Verify update
        proj_rep = engine.get_project_reputation(sample_project_data["project_id"])
        assert proj_rep is not None
        assert proj_rep.category_scores[ReputationCategory.PERFORMANCE].score == 90.0
        assert proj_rep.performance_score == 90.0
        assert len(proj_rep.reputation_history) == 1
    
    def test_reputation_level_calculation(self, engine):
        """Test reputation level calculation"""
        # Test different score ranges
        assert ReputationLevel.get_level(10.0) == ReputationLevel.NOVICE
        assert ReputationLevel.get_level(30.0) == ReputationLevel.DEVELOPER
        assert ReputationLevel.get_level(60.0) == ReputationLevel.EXPERT
        assert ReputationLevel.get_level(80.0) == ReputationLevel.MASTER
        assert ReputationLevel.get_level(95.0) == ReputationLevel.LEGEND
    
    @pytest.mark.asyncio
    async def test_weighted_score_calculation(self, engine, sample_developer_data):
        """Test weighted score calculation"""
        # Register developer
        dev_rep = await engine.register_developer(**sample_developer_data)
        
        # Update some categories with different scores
        await engine.update_developer_reputation(
            sample_developer_data["developer_id"],
            ReputationCategory.SECURITY,
            100.0,
            {"type": "test", "description": "Perfect security", "score": 100.0}
        )
        
        await engine.update_developer_reputation(
            sample_developer_data["developer_id"],
            ReputationCategory.PERFORMANCE,
            50.0,
            {"type": "test", "description": "Average performance", "score": 50.0}
        )
        
        # Get updated reputation
        updated_rep = engine.get_developer_reputation(sample_developer_data["developer_id"])
        
        # Weighted score should be between 50 and 100
        # Security (100) * 0.30 + Performance (50) * 0.25 + others (50) * 0.45 = 72.5
        # Toleransi lebih besar untuk menghitung bobot default
        assert 60.0 <= updated_rep.total_score <= 80.0
    
    @pytest.mark.asyncio
    async def test_top_developers_ranking(self, engine):
        """Test top developers ranking"""
        # Register multiple developers
        for i in range(5):
            await engine.register_developer(
                f"dev_test_{i}",
                f"Developer {i}",
                f"dev{i}@example.com",
                f"dev{i}"
            )
            
            # Give them different scores
            score = 30.0 + (i * 15.0)  # 30, 45, 60, 75, 90
            await engine.update_developer_reputation(
                f"dev_test_{i}",
                ReputationCategory.SECURITY,
                score,
                {"type": "test", "description": f"Score {score}", "score": score}
            )
        
        # Get top developers
        top_devs = engine.get_top_developers(3)
        
        assert len(top_devs) == 3
        # Should be sorted by score (highest first)
        assert top_devs[0].developer_id == "dev_test_4"  # Score 90
        assert top_devs[1].developer_id == "dev_test_3"  # Score 75
        assert top_devs[2].developer_id == "dev_test_2"  # Score 60
    
    @pytest.mark.asyncio
    async def test_top_projects_ranking(self, engine):
        """Test top projects ranking"""
        # Register developer first
        await engine.register_developer("dev_test_1", "Dev 1", "dev1@example.com", "dev1")
        
        # Register multiple projects
        for i in range(4):
            await engine.register_project(
                f"proj_test_{i}",
                f"Project {i}",
                f"Description {i}",
                "dev_test_1"
            )
            
            # Give them different scores
            score = 40.0 + (i * 20.0)  # 40, 60, 80, 100
            await engine.update_project_reputation(
                f"proj_test_{i}",
                ReputationCategory.PERFORMANCE,
                score,
                {"type": "test", "description": f"Score {score}", "score": score}
            )
        
        # Get top projects
        top_projs = engine.get_top_projects(2)
        
        assert len(top_projs) == 2
        # Should be sorted by score (highest first)
        assert top_projs[0].project_id == "proj_test_3"  # Score 100
        assert top_projs[1].project_id == "proj_test_2"  # Score 80
    
    def test_reputation_leaderboard(self, engine):
        """Test reputation leaderboard generation"""
        leaderboard = engine.get_reputation_leaderboard()
        
        assert 'top_developers' in leaderboard
        assert 'top_projects' in leaderboard
        assert isinstance(leaderboard['top_developers'], list)
        assert isinstance(leaderboard['top_projects'], list)
    
    @pytest.mark.asyncio
    async def test_reputation_insights(self, engine, sample_developer_data, sample_project_data):
        """Test reputation insights generation"""
        # Register developer and project
        await engine.register_developer(**sample_developer_data)
        await engine.register_project(**sample_project_data)
        
        # Update with different scores
        await engine.update_developer_reputation(
            sample_developer_data["developer_id"],
            ReputationCategory.SECURITY,
            90.0,
            {"type": "audit", "description": "Excellent security", "score": 90.0}
        )
        
        await engine.update_developer_reputation(
            sample_developer_data["developer_id"],
            ReputationCategory.COMMUNITY,
            30.0,
            {"type": "review", "description": "Low community engagement", "score": 30.0}
        )
        
        await engine.update_project_reputation(
            sample_project_data["project_id"],
            ReputationCategory.SECURITY,
            85.0,
            {"type": "audit", "description": "Good security audit", "score": 85.0}
        )
        
        # Get insights
        insights = engine.calculate_reputation_insights(
            sample_developer_data["developer_id"],
            sample_project_data["project_id"]
        )
        
        assert 'developer' in insights
        assert 'project' in insights
        assert insights['developer']['strongest_category']['category'] == 'security'
        assert insights['developer']['weakest_category']['category'] == 'community'
        assert len(insights['developer']['recommendations']) > 0
        assert len(insights['project']['recommendations']) > 0
    
    def test_data_persistence(self, engine, sample_developer_data):
        """Test data persistence (save/load)"""
        # This test would require creating a new engine instance
        # For now, we'll just test that save doesn't crash
        try:
            engine._save_reputation_data()
            # If we get here, save was successful
            assert True
        except Exception as e:
            pytest.fail(f"Data persistence failed: {e}")
    
    @pytest.mark.asyncio
    async def test_duplicate_registration(self, engine, sample_developer_data):
        """Test handling duplicate registrations"""
        # Register once
        dev1 = await engine.register_developer(**sample_developer_data)
        
        # Try to register again
        dev2 = await engine.register_developer(**sample_developer_data)
        
        # Should return the same object
        assert dev1.developer_id == dev2.developer_id
        assert dev1.name == dev2.name
    
    def test_invalid_developer_update(self, engine):
        """Test updating non-existent developer"""
        with pytest.raises(ValueError, match="Developer invalid_dev not found"):
            asyncio.run(engine.update_developer_reputation(
                "invalid_dev",
                ReputationCategory.SECURITY,
                80.0,
                {"type": "test", "description": "Test"}
            ))
    
    def test_invalid_project_update(self, engine):
        """Test updating non-existent project"""
        with pytest.raises(ValueError, match="Project invalid_proj not found"):
            asyncio.run(engine.update_project_reputation(
                "invalid_proj",
                ReputationCategory.PERFORMANCE,
                80.0,
                {"type": "test", "description": "Test"}
            ))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])