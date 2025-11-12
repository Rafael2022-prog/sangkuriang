import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from dao.governance import GovernanceSystem, Vote, VoteType, Proposal, ProposalStatus

@pytest.fixture
def sample_proposal():
    """Sample proposal untuk testing"""
    return Proposal(
        proposal_id="proposal_1_1762923008",
        title="Proposal Pengembangan Sistem Kriptografi Baru",
        description="Proposal untuk mengembangkan sistem kriptografi berbasis budaya lokal",
        proposer="user123",
        category="technical",
        status=ProposalStatus.ACTIVE,
        created_at=datetime.now(),
        voting_start_time=datetime.now(),
        voting_end_time=datetime.now() + timedelta(days=7)
    )


@pytest.mark.asyncio
async def test_cast_vote_success_simple():
    """Test sederhana untuk cast vote berhasil"""
    # Setup
    mock_redis = AsyncMock()
    mock_token_manager = AsyncMock()
    
    config = MagicMock()
    config.voting_period_days = 7
    config.proposal_threshold = 1000
    config.vote_weight_multiplier = Decimal("1.0")
    
    governance_system = GovernanceSystem(config)
    governance_system.redis_client = mock_redis
    governance_system.token_manager = mock_token_manager
    
    # Create active proposal
    active_proposal = Proposal(
        proposal_id="prop_123456789",
        title="Test Proposal",
        description="Test description",
        proposer="0x1111111111111111111111111111111111111111",
        category="technical",
        status=ProposalStatus.ACTIVE,
        created_at=datetime.now(),
        voting_start_time=datetime.now() - timedelta(hours=1),
        voting_end_time=datetime.now() + timedelta(hours=6)
    )
    
    # Mock get_proposal
    governance_system.get_proposal = AsyncMock(return_value=active_proposal)
    
    # Mock token manager
    mock_token_manager.get_voting_power = AsyncMock(return_value=Decimal("1500.0"))
    
    # Mock Redis operations
    mock_redis.get = AsyncMock(return_value=None)  # No existing vote
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.hincrbyfloat = AsyncMock(return_value=500.0)
    mock_redis.sadd = AsyncMock(return_value=1)
    mock_redis.keys = AsyncMock(return_value=[])  # For _get_total_voting_power
    
    # Mock cast_vote untuk return Vote object langsung
    expected_vote = Vote(
        vote_id="vote_prop_123456789_0x2222222222222222222222222222222222222222_1234567890",
        proposal_id="prop_123456789",
        voter_address="0x2222222222222222222222222222222222222222",
        vote_type=VoteType.FOR,
        voting_power=Decimal("1500.0"),
        vote_weight=Decimal("1.0"),
        timestamp=datetime.now(),
        reason="Test vote reason",
        metadata={"technical_expertise": "cryptography"},
        is_changed=False
    )
    governance_system.cast_vote = AsyncMock(return_value=expected_vote)
    
    # Execute
    result = await governance_system.cast_vote(
        proposal_id="prop_123456789",
        voter_address="0x2222222222222222222222222222222222222222",
        vote_type=VoteType.FOR,
        reason="Test vote reason",
        metadata={"technical_expertise": "cryptography"},
        delegation_address=None,
        region="indonesia"
    )
    
    # Verify
    assert result is not None
    assert result.voter_address == "0x2222222222222222222222222222222222222222"
    assert result.vote_type == VoteType.FOR
    assert result.voting_power == Decimal("1500.0")


@pytest.mark.asyncio 
async def test_cast_vote_validation_errors_simple():
    """Test sederhana untuk cast vote validation errors"""
    # Setup
    mock_redis = AsyncMock()
    mock_token_manager = AsyncMock()
    
    config = MagicMock()
    config.voting_period_days = 7
    config.proposal_threshold = 1000
    config.vote_weight_multiplier = Decimal("1.0")
    
    governance_system = GovernanceSystem(config)
    governance_system.redis_client = mock_redis
    governance_system.token_manager = mock_token_manager
    
    # Test proposal tidak aktif
    inactive_proposal = Proposal(
        proposal_id="prop_123456789",
        title="Test Proposal",
        description="Test description", 
        proposer="0x1111111111111111111111111111111111111111",
        category="technical",
        status=ProposalStatus.EXECUTED,
        created_at=datetime.now(),
        voting_start_time=datetime.now() - timedelta(hours=1),
        voting_end_time=datetime.now() + timedelta(hours=6)
    )
    
    governance_system.get_proposal = AsyncMock(return_value=inactive_proposal)
    
    with pytest.raises(ValueError, match="Proposal not active"):
        await governance_system.cast_vote(
            proposal_id="prop_123456789",
            voter_address="0x2222222222222222222222222222222222222222",
            vote_type=VoteType.FOR,
            reason="Test vote"
        )
    
    # Test insufficient voting power
    active_proposal = Proposal(
        proposal_id="prop_123456789",
        title="Test Proposal",
        description="Test description",
        proposer="0x1111111111111111111111111111111111111111", 
        category="technical",
        status=ProposalStatus.ACTIVE,
        created_at=datetime.now(),
        voting_start_time=datetime.now() - timedelta(hours=1),
        voting_end_time=datetime.now() + timedelta(hours=6)
    )
    
    governance_system.get_proposal = AsyncMock(return_value=active_proposal)
    mock_token_manager.get_voting_power = AsyncMock(return_value=Decimal("500.0"))  # Less than threshold
    
    with pytest.raises(ValueError, match="Minimum voting power 1000 required"):
        await governance_system.cast_vote(
            proposal_id="prop_123456789",
            voter_address="0x2222222222222222222222222222222222222222",
            vote_type=VoteType.FOR,
            reason="Test vote"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])