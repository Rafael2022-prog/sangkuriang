"""
Unit tests untuk Community Proposals System
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..'))

import pytest
import pytest_asyncio
import asyncio
import json
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
import redis.asyncio as redis

from dao.proposals import (
    CommunityProposals,
    CommunityProposal,
    ProposalReview,
    ProposalComment,
    ProposalCategory,
    ProposalPriority,
    ReviewStatus,
    ProposalStage,
    ProposalMetrics
)


@pytest_asyncio.fixture
async def mock_redis():
    """Mock Redis client"""
    redis_mock = AsyncMock(spec=redis.Redis)
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.incr = AsyncMock(return_value=1)
    redis_mock.sadd = AsyncMock(return_value=1)
    redis_mock.srem = AsyncMock(return_value=1)
    redis_mock.keys = AsyncMock(return_value=[])
    redis_mock.smembers = AsyncMock(return_value=set())
    return redis_mock


@pytest_asyncio.fixture
async def proposals_system(mock_redis):
    """Community Proposals System instance"""
    return CommunityProposals(mock_redis)


@pytest.mark.asyncio
async def test_submit_proposal_success(proposals_system, mock_redis):
    """Test submit proposal berhasil"""
    # Setup
    mock_redis.incr.return_value = 1
    
    # Execute
    proposal_id = await proposals_system.submit_proposal(
        title="Proposal Pengembangan Sistem Kriptografi Baru",
        description="Proposal ini bertujuan untuk mengembangkan sistem kriptografi baru berbasis matematika Nusantara dengan implementasi Python yang aman dan efisien. Sistem ini akan digunakan untuk meningkatkan keamanan transaksi dalam ekosistem Sangkuriang.",
        category=ProposalCategory.TECHNICAL,
        priority=ProposalPriority.HIGH,
        author="developer_indonesia",
        co_authors=["crypto_expert", "security_researcher"],
        budget=Decimal("50000000"),
        currency="IDR",
        timeline={"milestone1": 30, "milestone2": 60},
        resources=["https://github.com/example/crypto-system"],
        tags=["cryptography", "security", "indonesia"],
        language="id",
        region="indonesia"
    )
    
    # Verify
    assert proposal_id.startswith("community_proposal_")
    mock_redis.incr.assert_called_once_with("community_proposal_counter")
    mock_redis.set.assert_called()
    mock_redis.sadd.assert_called_once_with("active_community_proposals", proposal_id)


@pytest.mark.asyncio
async def test_submit_proposal_validation_error(proposals_system):
    """Test submit proposal dengan validasi error"""
    # Test title terlalu pendek
    with pytest.raises(ValueError, match="Title must be at least 10 characters"):
        await proposals_system.submit_proposal(
            title="Short",
            description="Valid description yang cukup panjang untuk memenuhi persyaratan minimum karakter",
            category=ProposalCategory.TECHNICAL,
            priority=ProposalPriority.MEDIUM,
            author="test_user"
        )
    
    # Test description terlalu pendek
    with pytest.raises(ValueError, match="Description must be at least 100 characters"):
        await proposals_system.submit_proposal(
            title="Valid Title Yang Cukup Panjang",
            description="Short desc",
            category=ProposalCategory.TECHNICAL,
            priority=ProposalPriority.MEDIUM,
            author="test_user"
        )


@pytest.mark.asyncio
async def test_submit_proposal_invalid_url(proposals_system):
    """Test submit proposal dengan URL invalid"""
    with pytest.raises(ValueError, match="Invalid resource URL"):
        await proposals_system.submit_proposal(
            title="Valid Title Yang Cukup Panjang",
            description="Valid description yang cukup panjang untuk memenuhi persyaratan minimum karakter dan menjelaskan detail proposal dengan baik",
            category=ProposalCategory.TECHNICAL,
            priority=ProposalPriority.MEDIUM,
            author="test_user",
            resources=["invalid-url"]
        )


@pytest.mark.asyncio
async def test_add_review_success(proposals_system, mock_redis):
    """Test add review berhasil"""
    # Setup - mock existing proposal
    proposal_data = {
        "id": "test_proposal_123",
        "title": "Test Proposal",
        "description": "Test description yang cukup panjang untuk memenuhi persyaratan minimum karakter",
        "category": "technical",
        "priority": "high",
        "author": "test_author",
        "co_authors": [],
        "review_status": "submitted",
        "stage": "draft",
        "created_at": 1234567890,
        "updated_at": 1234567890,
        "review_deadline": 1234571490,
        "voting_start": None,
        "voting_end": None,
        "implementation_deadline": None,
        "budget": None,
        "currency": "IDR",
        "timeline": {},
        "resources": [],
        "tags": [],
        "related_proposals": [],
        "review_notes": [],
        "community_score": 0.0,
        "expert_score": 0.0,
        "revision_count": 0,
        "views": 0,
        "comments_count": 0,
        "supporters": [],
        "opposition": [],
        "is_featured": False,
        "language": "id",
        "region": "indonesia"
    }
    
    mock_redis.get.side_effect = [
        json.dumps(proposal_data),  # First call for get_proposal
        None,  # Subsequent calls
        json.dumps(proposal_data)  # Call for _update_proposal_after_review
    ]
    mock_redis.incr.return_value = 1
    mock_redis.keys.return_value = []  # No existing reviews
    
    # Execute
    review_id = await proposals_system.add_review(
        proposal_id="test_proposal_123",
        reviewer="expert_reviewer",
        reviewer_type="expert",
        score=8.5,
        comments="Proposal ini sangat menjanjikan dengan pendekatan kriptografi yang inovatif",
        technical_feedback="Implementasi menggunakan algoritma yang kuat dan aman",
        economic_feedback="Budget realistis dan ROI tinggi",
        risk_assessment="Risiko rendah, teknologi sudah teruji",
        recommendation="approve",
        is_public=True
    )
    
    # Verify
    assert review_id.startswith("proposal_review_")
    mock_redis.incr.assert_called_with("proposal_review_counter")
    mock_redis.set.assert_called()


@pytest.mark.asyncio
async def test_add_review_validation_errors(proposals_system, mock_redis):
    """Test add review dengan validasi error"""
    # Setup - mock non-existing proposal
    mock_redis.get.return_value = None
    
    # Test proposal tidak ditemukan
    with pytest.raises(ValueError, match="Proposal not found"):
        await proposals_system.add_review(
            proposal_id="non_existing",
            reviewer="reviewer",
            reviewer_type="expert",
            score=8.0,
            comments="Good proposal",
            recommendation="approve"
        )
    
    # Setup - mock existing proposal
    proposal_data = {
        "id": "test_proposal_123",
        "title": "Test Proposal",
        "description": "Test description yang cukup panjang",
        "category": "technical",
        "priority": "high",
        "author": "test_author",
        "co_authors": [],
        "review_status": "submitted",
        "stage": "draft",
        "created_at": 1234567890,
        "updated_at": 1234567890,
        "review_deadline": 1234571490,
        "voting_start": None,
        "voting_end": None,
        "implementation_deadline": None,
        "budget": None,
        "currency": "IDR",
        "timeline": {},
        "resources": [],
        "tags": [],
        "related_proposals": [],
        "review_notes": [],
        "community_score": 0.0,
        "expert_score": 0.0,
        "revision_count": 0,
        "views": 0,
        "comments_count": 0,
        "supporters": [],
        "opposition": [],
        "is_featured": False,
        "language": "id",
        "region": "indonesia"
    }
    
    mock_redis.get.side_effect = [
        json.dumps(proposal_data),  # First call for get_proposal (score validation)
        json.dumps(proposal_data),  # Second call for get_proposal (recommendation validation)
        None  # Subsequent calls
    ]
    
    # Test score invalid
    with pytest.raises(ValueError, match="Score must be between 0 and 10"):
        await proposals_system.add_review(
            proposal_id="test_proposal_123",
            reviewer="reviewer",
            reviewer_type="expert",
            score=15.0,  # Invalid score
            comments="Good proposal",
            recommendation="approve"
        )
    
    # Test recommendation invalid
    with pytest.raises(ValueError, match="Recommendation must be one of"):
        await proposals_system.add_review(
            proposal_id="test_proposal_123",
            reviewer="reviewer",
            reviewer_type="expert",
            score=8.0,
            comments="Good proposal",
            recommendation="invalid_recommendation"
        )


@pytest.mark.asyncio
async def test_add_comment_success(proposals_system, mock_redis):
    """Test add comment berhasil"""
    # Setup - mock existing proposal
    proposal_data = {
        "id": "test_proposal_123",
        "title": "Test Proposal",
        "description": "Test description yang cukup panjang",
        "category": "technical",
        "priority": "high",
        "author": "test_author",
        "co_authors": [],
        "review_status": "submitted",
        "stage": "draft",
        "created_at": 1234567890,
        "updated_at": 1234567890,
        "review_deadline": 1234571490,
        "voting_start": None,
        "voting_end": None,
        "implementation_deadline": None,
        "budget": None,
        "currency": "IDR",
        "timeline": {},
        "resources": [],
        "tags": [],
        "related_proposals": [],
        "review_notes": [],
        "community_score": 0.0,
        "expert_score": 0.0,
        "revision_count": 0,
        "views": 0,
        "comments_count": 0,
        "supporters": [],
        "opposition": [],
        "is_featured": False,
        "language": "id",
        "region": "indonesia"
    }
    
    mock_redis.get.side_effect = [
        json.dumps(proposal_data),  # First call for get_proposal
        None,  # Subsequent calls
        json.dumps(proposal_data)  # Call for _update_comment_count
    ]
    mock_redis.incr.return_value = 1
    mock_redis.keys.return_value = []  # No existing comments
    
    # Execute
    comment_id = await proposals_system.add_comment(
        proposal_id="test_proposal_123",
        author="community_member",
        content="Proposal ini sangat menarik dan relevan untuk ekosistem kriptografi Indonesia. Saya mendukung implementasi ini.",
        language="id"
    )
    
    # Verify
    assert comment_id.startswith("proposal_comment_")
    mock_redis.incr.assert_called_with("proposal_comment_counter")
    mock_redis.set.assert_called()


@pytest.mark.asyncio
async def test_vote_proposal_success(proposals_system, mock_redis):
    """Test vote proposal berhasil"""
    # Setup - mock existing proposal
    proposal_data = {
        "id": "test_proposal_123",
        "title": "Test Proposal",
        "description": "Test description yang cukup panjang",
        "category": "technical",
        "priority": "high",
        "author": "test_author",
        "co_authors": [],
        "review_status": "submitted",
        "stage": "draft",
        "created_at": 1234567890,
        "updated_at": 1234567890,
        "review_deadline": 1234571490,
        "voting_start": None,
        "voting_end": None,
        "implementation_deadline": None,
        "budget": None,
        "currency": "IDR",
        "timeline": {},
        "resources": [],
        "tags": [],
        "related_proposals": [],
        "review_notes": [],
        "community_score": 0.0,
        "expert_score": 0.0,
        "revision_count": 0,
        "views": 0,
        "comments_count": 0,
        "supporters": [],
        "opposition": [],
        "is_featured": False,
        "language": "id",
        "region": "indonesia"
    }
    
    mock_redis.get.side_effect = [
        json.dumps(proposal_data),  # First call
        None,  # Subsequent calls
        json.dumps(proposal_data)  # Call for vote update
    ]
    
    # Execute - vote support
    result = await proposals_system.vote_proposal(
        proposal_id="test_proposal_123",
        voter="community_member",
        vote_type="support"
    )
    
    # Verify
    assert result is True
    mock_redis.set.assert_called()


@pytest.mark.asyncio
async def test_vote_proposal_switch_vote(proposals_system, mock_redis):
    """Test vote proposal - switch dari support ke oppose"""
    # Setup - mock existing proposal dengan existing supporter
    proposal_data = {
        "id": "test_proposal_123",
        "title": "Test Proposal",
        "description": "Test description yang cukup panjang",
        "category": "technical",
        "priority": "high",
        "author": "test_author",
        "co_authors": [],
        "review_status": "submitted",
        "stage": "draft",
        "created_at": 1234567890,
        "updated_at": 1234567890,
        "review_deadline": 1234571490,
        "voting_start": None,
        "voting_end": None,
        "implementation_deadline": None,
        "budget": None,
        "currency": "IDR",
        "timeline": {},
        "resources": [],
        "tags": [],
        "related_proposals": [],
        "review_notes": [],
        "community_score": 0.0,
        "expert_score": 0.0,
        "revision_count": 0,
        "views": 0,
        "comments_count": 0,
        "supporters": ["existing_supporter"],
        "opposition": [],
        "is_featured": False,
        "language": "id",
        "region": "indonesia"
    }
    
    mock_redis.get.side_effect = [
        json.dumps(proposal_data),  # First call
        None,  # Subsequent calls
        json.dumps(proposal_data)  # Call for vote update
    ]
    
    # Execute - switch vote dari support ke oppose
    result = await proposals_system.vote_proposal(
        proposal_id="test_proposal_123",
        voter="existing_supporter",  # Existing supporter
        vote_type="oppose"
    )
    
    # Verify
    assert result is True
    mock_redis.set.assert_called()


@pytest.mark.asyncio
async def test_feature_proposal(proposals_system, mock_redis):
    """Test feature/unfeature proposal"""
    # Setup - mock existing proposal
    proposal_data = {
        "id": "test_proposal_123",
        "title": "Test Proposal",
        "description": "Test description yang cukup panjang",
        "category": "technical",
        "priority": "high",
        "author": "test_author",
        "co_authors": [],
        "review_status": "submitted",
        "stage": "draft",
        "created_at": 1234567890,
        "updated_at": 1234567890,
        "review_deadline": 1234571490,
        "voting_start": None,
        "voting_end": None,
        "implementation_deadline": None,
        "budget": None,
        "currency": "IDR",
        "timeline": {},
        "resources": [],
        "tags": [],
        "related_proposals": [],
        "review_notes": [],
        "community_score": 0.0,
        "expert_score": 0.0,
        "revision_count": 0,
        "views": 0,
        "comments_count": 0,
        "supporters": [],
        "opposition": [],
        "is_featured": False,
        "language": "id",
        "region": "indonesia"
    }
    
    mock_redis.get.side_effect = [
        json.dumps(proposal_data),  # First call
        None,  # Subsequent calls
        json.dumps(proposal_data)  # Call for feature update
    ]
    
    # Execute - feature proposal
    result = await proposals_system.feature_proposal(
        proposal_id="test_proposal_123",
        featured=True
    )
    
    # Verify
    assert result is True
    mock_redis.sadd.assert_called_with("featured_community_proposals", "test_proposal_123")
    mock_redis.set.assert_called()


@pytest.mark.asyncio
async def test_get_proposal_not_found(proposals_system, mock_redis):
    """Test get proposal yang tidak ada"""
    mock_redis.get.return_value = None
    
    result = await proposals_system.get_proposal("non_existing")
    
    assert result is None


@pytest.mark.asyncio
async def test_get_proposals_with_filters(proposals_system, mock_redis):
    """Test get proposals dengan berbagai filter"""
    # Setup - mock multiple proposals
    proposal_data_1 = {
        "id": "proposal_1",
        "title": "Technical Proposal",
        "description": "Test description yang cukup panjang",
        "category": "technical",
        "priority": "high",
        "author": "author1",
        "co_authors": [],
        "review_status": "submitted",
        "stage": "draft",
        "created_at": 1234567890,
        "updated_at": 1234567890,
        "review_deadline": 1234571490,
        "voting_start": None,
        "voting_end": None,
        "implementation_deadline": None,
        "budget": None,
        "currency": "IDR",
        "timeline": {},
        "resources": [],
        "tags": [],
        "related_proposals": [],
        "review_notes": [],
        "community_score": 0.0,
        "expert_score": 0.0,
        "revision_count": 0,
        "views": 0,
        "comments_count": 0,
        "supporters": [],
        "opposition": [],
        "is_featured": True,
        "language": "id",
        "region": "indonesia"
    }
    
    proposal_data_2 = {
        "id": "proposal_2",
        "title": "Community Proposal",
        "description": "Test description yang cukup panjang",
        "category": "community",
        "priority": "medium",
        "author": "author2",
        "co_authors": [],
        "review_status": "approved_for_voting",
        "stage": "voting",
        "created_at": 1234567891,
        "updated_at": 1234567891,
        "review_deadline": 1234571491,
        "voting_start": None,
        "voting_end": None,
        "implementation_deadline": None,
        "budget": None,
        "currency": "IDR",
        "timeline": {},
        "resources": [],
        "tags": [],
        "related_proposals": [],
        "review_notes": [],
        "community_score": 8.5,
        "expert_score": 7.0,
        "revision_count": 0,
        "views": 0,
        "comments_count": 0,
        "supporters": [],
        "opposition": [],
        "is_featured": False,
        "language": "en",
        "region": "global"
    }
    
    mock_redis.keys.return_value = ["community_proposal:proposal_1", "community_proposal:proposal_2"]
    mock_redis.get.side_effect = [
        json.dumps(proposal_data_1),
        json.dumps(proposal_data_2)
    ]
    
    # Execute - filter by category
    proposals = await proposals_system.get_proposals(
        category=ProposalCategory.TECHNICAL,
        limit=10
    )
    
    # Verify
    assert len(proposals) == 1
    assert proposals[0].category == ProposalCategory.TECHNICAL
    assert proposals[0].id == "proposal_1"


@pytest.mark.asyncio
async def test_get_metrics(proposals_system, mock_redis):
    """Test get metrics"""
    # Setup - mock multiple proposals
    proposal_data = {
        "id": "test_proposal",
        "title": "Test Proposal",
        "description": "Test description yang cukup panjang",
        "category": "technical",
        "priority": "high",
        "author": "test_author",
        "co_authors": [],
        "review_status": "approved_for_voting",
        "stage": "voting",
        "created_at": 1234567890,
        "updated_at": 1234567890,
        "review_deadline": 1234571490,
        "voting_start": None,
        "voting_end": None,
        "implementation_deadline": None,
        "budget": None,
        "currency": "IDR",
        "timeline": {},
        "resources": [],
        "tags": [],
        "related_proposals": [],
        "review_notes": [],
        "community_score": 8.5,
        "expert_score": 7.5,
        "revision_count": 0,
        "views": 0,
        "comments_count": 0,
        "supporters": ["user1", "user2"],
        "opposition": ["user3"],
        "is_featured": False,
        "language": "id",
        "region": "indonesia"
    }
    
    mock_redis.keys.return_value = ["community_proposal:test_proposal"]
    mock_redis.get.return_value = json.dumps(proposal_data)
    
    # Execute
    metrics = await proposals_system.get_metrics()
    
    # Verify
    assert isinstance(metrics, ProposalMetrics)
    assert metrics.total_proposals == 1
    assert metrics.proposals_by_category["technical"] == 1
    assert metrics.proposals_by_stage["voting"] == 1
    assert metrics.proposals_by_priority["high"] == 1
    assert metrics.average_community_score == 8.5
    assert metrics.average_expert_score == 7.5
    assert metrics.approval_rate == 100.0  # 1 approved out of 1 total
    assert metrics.community_participation == 3.0  # 3 participants / 1 proposal