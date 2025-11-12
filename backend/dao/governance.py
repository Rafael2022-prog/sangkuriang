"""
SANGKURIANG DAO Governance System
Implementasi decentralized governance dengan voting mechanism
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import redis.asyncio as redis
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature


class ProposalStatus(Enum):
    """Status proposal dalam sistem governance"""
    PENDING = "pending"
    ACTIVE = "active"
    PASSED = "passed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXECUTED = "executed"


class VoteType(Enum):
    """Jenis vote dalam governance"""
    FOR = "for"
    AGAINST = "against"
    ABSTAIN = "abstain"


@dataclass
class Proposal:
    """Representasi proposal dalam DAO"""
    proposal_id: str
    title: str
    description: str
    proposer: str
    category: str
    status: ProposalStatus
    created_at: datetime
    voting_start_time: datetime
    voting_end_time: datetime
    execution_time: Optional[datetime] = None
    votes_for: Decimal = Decimal("0.0")
    votes_against: Decimal = Decimal("0.0")
    votes_abstain: Decimal = Decimal("0.0")
    total_votes: Decimal = Decimal("0.0")
    quorum_required: Decimal = Decimal("1000.0")
    execution_data: Optional[Dict] = None
    ipfs_hash: Optional[str] = None
    tags: List[str] = None
    priority: str = "medium"
    estimated_cost: Decimal = Decimal("0.0")
    funding_required: bool = False
    related_proposals: List[str] = None
    discussion_period_days: int = 3
    implementation_timeline: str = ""
    success_criteria: Optional[Dict] = None
    risk_assessment: str = "medium"
    compliance_check: str = "pending"
    metadata: Optional[Dict] = None
    version: int = 1
    parent_proposal: Optional[str] = None
    child_proposals: List[str] = None
    review_comments: List[str] = None
    audit_trail: List[Dict] = None
    language: str = "id"
    region: str = "indonesia"
    emergency_type: Optional[str] = None  # For emergency proposals
    immediate_action_required: bool = False
    proposal_type: str = "general"  # Type of proposal: general, parameter_change, treasury_spend, upgrade_contract
    parameters: Optional[Dict] = None  # Parameters for execution
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.related_proposals is None:
            self.related_proposals = []
        if self.success_criteria is None:
            self.success_criteria = {}
        if self.metadata is None:
            self.metadata = {}
        if self.child_proposals is None:
            self.child_proposals = []
        if self.review_comments is None:
            self.review_comments = []
        if self.audit_trail is None:
            self.audit_trail = []
    
    def to_dict(self):
        """Convert proposal to dictionary"""
        result = asdict(self)
        # Convert enum to string
        result['status'] = self.status.value
        # Convert datetime to ISO format string
        datetime_fields = ['created_at', 'voting_start_time', 'voting_end_time', 'execution_time']
        for field in datetime_fields:
            if getattr(self, field):
                result[field] = getattr(self, field).isoformat()
        # Convert Decimal to string for JSON serialization
        result['votes_for'] = str(self.votes_for)
        result['votes_against'] = str(self.votes_against)
        result['votes_abstain'] = str(self.votes_abstain)
        result['total_votes'] = str(self.total_votes)
        result['quorum_required'] = str(self.quorum_required)
        result['estimated_cost'] = str(self.estimated_cost)
        # Convert Decimal in nested dictionaries (success_criteria)
        if isinstance(result.get('success_criteria'), dict):
            for key, value in result['success_criteria'].items():
                if isinstance(value, Decimal):
                    result['success_criteria'][key] = str(value)
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Proposal':
        """Create Proposal from dictionary."""
        print(f"DEBUG from_dict: Input data keys: {list(data.keys())}")
        
        # Remove invalid fields that shouldn't be passed to constructor
        invalid_fields = ['vote_id', 'voter_address', 'vote_type', 'voting_power', 'vote_weight', 'timestamp', 'reason', 'delegation_address', 'previous_vote', 'is_delegated', 'is_changed', 'compliance_verified']
        for field in invalid_fields:
            if field in data:
                print(f"DEBUG from_dict: Removing invalid field: {field}")
                del data[field]

        # Convert string back to enum
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = ProposalStatus(data['status'])
        # Convert string back to datetime
        datetime_fields = ['created_at', 'voting_start_time', 'voting_end_time', 'execution_time', 'executed_at']
        for field in datetime_fields:
            if field in data and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])
        # Convert string back to Decimal
        decimal_fields = ['votes_for', 'votes_against', 'votes_abstain', 'total_votes', 'quorum_required', 'estimated_cost']
        for field in decimal_fields:
            if field in data and isinstance(data[field], str):
                data[field] = Decimal(data[field])
        # Convert Decimal in nested dictionaries (success_criteria)
        if 'success_criteria' in data and isinstance(data['success_criteria'], dict):
            for key, value in data['success_criteria'].items():
                if isinstance(value, str):
                    try:
                        data['success_criteria'][key] = Decimal(value)
                    except (ValueError, TypeError):
                        pass  # Keep as string if not a valid decimal
        # Ensure proposal_type has default value
        if 'proposal_type' not in data:
            data['proposal_type'] = 'general'
        # Ensure parameters is properly handled
        if 'parameters' in data and data['parameters'] is None:
            data['parameters'] = {}
        
        print(f"DEBUG from_dict: Final data keys before constructor: {list(data.keys())}")
        print(f"DEBUG from_dict: Required fields check:")
        required_fields = ['title', 'description', 'proposer', 'category', 'status', 'created_at', 'voting_start_time', 'voting_end_time']
        for field in required_fields:
            print(f"  {field}: {'✓' if field in data else '✗'}")
            if field in data:
                print(f"    type: {type(data[field])}")
                print(f"    value: {data[field]}")
        
        return cls(**data)


@dataclass
class Vote:
    """Representasi vote dalam proposal"""
    vote_id: str
    proposal_id: str
    voter_address: str
    vote_type: VoteType
    voting_power: Decimal
    vote_weight: Decimal
    timestamp: datetime
    reason: Optional[str] = None
    metadata: Optional[Dict] = None
    delegation_address: Optional[str] = None
    previous_vote: Optional[str] = None
    is_delegated: bool = False
    is_changed: bool = False
    compliance_verified: bool = False
    region: str = "indonesia"
    audit_trail: List[Dict] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.audit_trail is None:
            self.audit_trail = []
    
    def to_dict(self):
        """Convert vote to dictionary"""
        result = asdict(self)
        # Convert enum to string
        result['vote_type'] = self.vote_type.value
        # Convert datetime to ISO format string
        result['timestamp'] = self.timestamp.isoformat()
        # Convert Decimal to string for JSON serialization
        result['voting_power'] = str(self.voting_power)
        result['vote_weight'] = str(self.vote_weight)
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Vote':
        """Create vote from dictionary"""
        # Convert string back to enum
        if 'vote_type' in data and isinstance(data['vote_type'], str):
            data['vote_type'] = VoteType(data['vote_type'])
        # Convert string back to datetime
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        # Convert string back to Decimal
        decimal_fields = ['voting_power', 'vote_weight']
        for field in decimal_fields:
            if field in data and isinstance(data[field], str):
                data[field] = Decimal(data[field])
        return cls(**data)


@dataclass
class GovernanceConfig:
    """Konfigurasi sistem governance"""
    governance_token_address: str = "0x0000000000000000000000000000000000000000"
    voting_period_days: int = 7
    proposal_threshold: Decimal = Decimal("1000.0")
    quorum_percentage: Decimal = Decimal("10.0")
    proposal_fee: Decimal = Decimal("10.0")
    execution_delay_hours: int = 24
    emergency_voting_period_hours: int = 24
    max_active_proposals: int = 10
    min_participation_rate: Decimal = Decimal("5.0")
    vote_weight_multiplier: Decimal = Decimal("1.0")
    delegation_enabled: bool = True
    vote_change_allowed: bool = True
    proposal_categories: List[str] = None
    required_staking_period_days: int = 30
    unstaking_period_days: int = 7
    slashing_percentage: Decimal = Decimal("10.0")
    reward_pool_percentage: Decimal = Decimal("2.0")
    treasury_address: str = "0x0000000000000000000000000000000000000000"
    multisig_required: int = 3
    audit_log_retention_days: int = 365
    compliance_mode: bool = True
    region_specific_rules: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.proposal_categories is None:
            self.proposal_categories = ["technical", "financial", "governance", "emergency"]
        if self.region_specific_rules is None:
            self.region_specific_rules = {"indonesia": {"min_participation": Decimal("15.0")}}


@dataclass
class GovernanceToken:
    """Token governance untuk voting power"""
    token_address: str
    token_symbol: str
    total_supply: Decimal
    circulating_supply: Decimal
    decimals: int
    holder_count: int
    staking_contract: str
    reward_pool: Decimal
    governance_weight: Decimal
    voting_power_multiplier: Decimal
    delegation_enabled: bool
    unstaking_period_days: int
    min_staking_amount: Decimal
    max_staking_amount: Decimal
    staking_apy: Decimal
    last_updated: datetime
    
    def to_dict(self):
        """Convert token to dictionary"""
        result = asdict(self)
        # Convert Decimal to string for JSON serialization
        result['total_supply'] = str(self.total_supply)
        result['circulating_supply'] = str(self.circulating_supply)
        result['reward_pool'] = str(self.reward_pool)
        result['governance_weight'] = str(self.governance_weight)
        result['voting_power_multiplier'] = str(self.voting_power_multiplier)
        result['staking_apy'] = str(self.staking_apy)
        result['min_staking_amount'] = str(self.min_staking_amount)
        result['max_staking_amount'] = str(self.max_staking_amount)
        # Convert datetime to ISO format string
        result['last_updated'] = self.last_updated.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GovernanceToken':
        """Create governance token from dictionary"""
        # Convert string back to Decimal
        decimal_fields = ['total_supply', 'circulating_supply', 'reward_pool', 
                         'governance_weight', 'voting_power_multiplier', 'staking_apy',
                         'min_staking_amount', 'max_staking_amount']
        for field in decimal_fields:
            if field in data and isinstance(data[field], str):
                data[field] = Decimal(data[field])
        
        # Convert ISO string back to datetime
        if 'last_updated' in data and isinstance(data['last_updated'], str):
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        
        return cls(**data)


class TokenManager:
    """Manager untuk token governance dan voting power"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.token_prefix = "governance_token:"
    
    async def get_voting_power(self, address: str) -> int:
        """Mendapatkan voting power dari address"""
        key = f"{self.token_prefix}{address}"
        voting_power = await self.redis_client.get(key)
        return int(voting_power) if voting_power else 0
    
    async def set_voting_power(self, address: str, amount: int):
        """Set voting power untuk address"""
        key = f"{self.token_prefix}{address}"
        await self.redis_client.set(key, amount)
    
    async def transfer_voting_power(self, from_address: str, to_address: str, amount: int):
        """Transfer voting power antar address"""
        from_power = await self.get_voting_power(from_address)
        if from_power < amount:
            raise ValueError("Insufficient voting power")
        
        to_power = await self.get_voting_power(to_address)
        
        await self.set_voting_power(from_address, from_power - amount)
        await self.set_voting_power(to_address, to_power + amount)


class GovernanceSystem:
    """Sistem governance DAO utama"""
    
    def __init__(self, config: GovernanceConfig):
        self.config = config
        self.redis_client = None
        self.token_manager = None
        self.proposal_prefix = "proposal:"
        self.vote_prefix = "vote:"
        self.active_proposals_key = "active_proposals"
        self.proposal_counter_key = "proposal_counter"
    
    def initialize_redis(self, redis_client: redis.Redis):
        """Inisialisasi Redis client dan token manager"""
        self.redis_client = redis_client
        self.token_manager = TokenManager(redis_client)
    
    async def create_proposal(
        self,
        title: str,
        description: str,
        proposer: str,
        category: str,
        ipfs_hash: Optional[str] = None,
        **kwargs
    ) -> str:
        """Membuat proposal baru"""
        if not self.redis_client or not self.token_manager:
            raise RuntimeError("Redis not initialized")
            
        # Validasi kategori
        if category not in self.config.proposal_categories:
            raise ValueError("Invalid proposal category")
            
        # Validasi voting power proposer
        proposer_power = await self.token_manager.get_voting_power(proposer)
        if proposer_power < self.config.proposal_threshold:
            raise ValueError(f"Minimum voting power {self.config.proposal_threshold} required")
        
        # Generate proposal ID
        counter = await self.redis_client.incr(self.proposal_counter_key)
        proposal_id = f"proposal_{counter}_{int(time.time())}"
        
        # Hitung waktu voting
        current_time = datetime.now()
        voting_start_time = current_time
        voting_end_time = current_time + timedelta(days=self.config.voting_period_days)
        
        # Buat proposal
        proposal = Proposal(
            proposal_id=proposal_id,
            title=title,
            description=description,
            proposer=proposer,
            category=category,
            status=ProposalStatus.PENDING,
            created_at=current_time,
            voting_start_time=voting_start_time,
            voting_end_time=voting_end_time,
            ipfs_hash=ipfs_hash,
            **kwargs
        )
        
        # Simpan proposal
        await self._save_proposal(proposal)
        
        # Tambahkan ke active proposals
        await self.redis_client.sadd(self.active_proposals_key, proposal_id)
        
        return proposal_id
    
    async def vote(
        self,
        proposal_id: str,
        voter_address: str,
        vote_type: VoteType,
        reason: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Memberikan vote pada proposal"""
        if not self.redis_client or not self.token_manager:
            raise RuntimeError("Redis not initialized")
            
        # Validasi proposal
        print(f"DEBUG: vote() called with proposal_id={proposal_id}")
        proposal = await self.get_proposal(proposal_id)
        print(f"DEBUG: get_proposal returned: {type(proposal)}")
        if not proposal:
            raise ValueError("Proposal not found")
        
        if proposal.status != ProposalStatus.ACTIVE:
            raise ValueError("Proposal is not active")
        
        # Validasi waktu voting
        current_time = datetime.now()
        if current_time < proposal.voting_start_time or current_time > proposal.voting_end_time:
            raise ValueError("Voting period not active")
        
        # Validasi voting power
        voting_power = await self.token_manager.get_voting_power(voter_address)
        if voting_power < self.config.proposal_threshold:
            raise ValueError(f"Minimum voting power {self.config.proposal_threshold} required")
        
        # Cek apakah sudah pernah vote
        vote_key = f"{self.vote_prefix}{proposal_id}:{voter_address}"
        existing_vote = await self.redis_client.get(vote_key)
        if existing_vote:
            raise ValueError("Already voted on this proposal")
        
        # Buat vote
        vote = Vote(
            vote_id=f"vote_{proposal_id}_{voter_address}_{int(time.time())}",
            proposal_id=proposal_id,
            voter_address=voter_address,
            vote_type=vote_type,
            voting_power=Decimal(str(voting_power)),
            vote_weight=self.config.vote_weight_multiplier,
            timestamp=current_time,
            reason=reason,
            **kwargs
        )
        
        # Simpan vote
        await self.redis_client.set(vote_key, json.dumps(vote.to_dict()))
        
        # Update vote counts
        await self._update_vote_counts(proposal_id, vote_type, voting_power)
        
        return True
    
    async def execute_proposal(self, proposal_id: str, executor: str) -> bool:
        """Menjalankan proposal yang telah disetujui"""
        # Get proposal
        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError("Proposal not found")
        
        # Validasi status
        if proposal.status != ProposalStatus.PASSED:
            raise ValueError("Proposal is not passed")
        
        # Validasi waktu eksekusi
        if datetime.now() < proposal.voting_end_time + timedelta(hours=self.config.execution_delay_hours):
            raise ValueError("Execution time not reached")
        
        # Validasi executor
        if executor != proposal.proposer:
            raise ValueError("Only proposer can execute")
        
        # Eksekusi proposal berdasarkan tipe
        execution_result = await self._execute_proposal_by_type(proposal)
        
        # Update status
        proposal.status = ProposalStatus.EXECUTED
        proposal.execution_time = datetime.now()
        proposal.execution_data = execution_result
        
        await self._save_proposal(proposal)
        
        # Hapus dari active proposals
        await self.redis_client.srem(self.active_proposals_key, proposal_id)
        
        return True
    
    async def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        """Mendapatkan detail proposal"""
        print(f"DEBUG get_proposal: Getting proposal {proposal_id}")
        key = f"{self.proposal_prefix}{proposal_id}"
        data = await self.redis_client.get(key)
        print(f"DEBUG get_proposal: Raw data from Redis: {data}")
        
        if not data:
            return None
        
        proposal_dict = json.loads(data)
        print(f"DEBUG get_proposal: Parsed data keys: {list(proposal_dict.keys())}")
        return Proposal.from_dict(proposal_dict)
    
    async def get_all_proposals(self) -> List[Proposal]:
        """Mendapatkan semua proposal"""
        proposal_keys = await self.redis_client.keys(f"{self.proposal_prefix}*")
        proposals = []
        
        for key in proposal_keys:
            data = await self.redis_client.get(key)
            if data:
                proposal_dict = json.loads(data)
                proposals.append(Proposal.from_dict(proposal_dict))
        
        return sorted(proposals, key=lambda x: x.created_at, reverse=True)
    
    async def get_active_proposals(self, limit: Optional[int] = None, offset: int = 0) -> List[Proposal]:
        """Mendapatkan proposal aktif"""
        active_ids = await self.redis_client.smembers(self.active_proposals_key)
        proposals = []
        
        for proposal_id in active_ids:
            proposal = await self.get_proposal(proposal_id)
            if proposal:
                proposals.append(proposal)
        
        # Sort by created_at descending
        sorted_proposals = sorted(proposals, key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        if limit is not None:
            start = offset
            end = offset + limit
            return sorted_proposals[start:end]
        else:
            # Return all proposals starting from offset
            return sorted_proposals[offset:]
    
    async def get_proposals_by_category(self, category: str, limit: Optional[int] = None) -> List[Proposal]:
        """Mendapatkan proposal berdasarkan kategori"""
        all_proposals = await self.get_all_proposals()
        filtered_proposals = [p for p in all_proposals if p.category == category]
        sorted_proposals = sorted(filtered_proposals, key=lambda x: x.created_at, reverse=True)
        
        if limit:
            return sorted_proposals[:limit]
        return sorted_proposals
    
    async def get_proposal_status(self, proposal_id: str) -> Dict:
        """Mendapatkan status proposal"""
        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError("Proposal not found")
        
        total_voting_power = await self._get_total_voting_power()
        quorum_required = int(total_voting_power * self.config.quorum_percentage / 100)
        
        return {
            "status": proposal.status.value,
            "title": proposal.title,
            "category": proposal.category,
            "votes_for": str(proposal.votes_for),
            "votes_against": str(proposal.votes_against),
            "votes_abstain": str(proposal.votes_abstain),
            "quorum_required": str(quorum_required),
            "participation_rate": str((proposal.total_votes / total_voting_power * 100) if total_voting_power > 0 else 0)
        }
    
    async def get_proposal_votes(self, proposal_id: str) -> List[Dict]:
        """Mendapatkan semua vote untuk proposal"""
        vote_keys = await self.redis_client.keys(f"{self.vote_prefix}{proposal_id}:*")
        votes = []
        
        for key in vote_keys:
            vote_data = await self.redis_client.get(key)
            if vote_data:
                vote_dict = json.loads(vote_data)
                votes.append(vote_dict)
        
        return votes
    
    async def get_governance_stats(self) -> Dict:
        """Get governance statistics"""
        # Get all proposals
        all_proposals = await self.get_all_proposals()
        active_proposals = await self.get_active_proposals()
        
        # Calculate statistics
        total_proposals = len(all_proposals)
        active_count = len(active_proposals)
        passed_count = len([p for p in all_proposals if p.status == ProposalStatus.PASSED])
        rejected_count = len([p for p in all_proposals if p.status == ProposalStatus.REJECTED])
        
        # Get token statistics if available
        total_voting_power = 0
        token_holder_count = 0
        active_voters = 0
        
        if self.redis_client:
            try:
                # Get total voting power
                token_keys = await self.redis_client.keys("governance_token:*")
                for key in token_keys:
                    power = await self.redis_client.get(key)
                    if power:
                        total_voting_power += int(power)
                
                # Get token holder count from governance token data
                token_data = await self.redis_client.hget("governance:token", "governance_token")
                if token_data:
                    token_dict = json.loads(token_data)
                    token_holder_count = token_dict.get("holder_count", 0)
                
                # Get active voters count
                active_voters = await self.redis_client.scard("governance:active_voters") or 0
                
            except Exception:
                # Fallback to default values if Redis operations fail
                pass
        
        return {
            "total_proposals": total_proposals,
            "active_proposals": active_count,
            "passed_proposals": passed_count,
            "rejected_proposals": rejected_count,
            "total_voting_power": str(total_voting_power),
            "token_holder_count": token_holder_count,
            "active_voters": active_voters,
            "participation_rate": round((passed_count + rejected_count) / total_proposals * 100, 2) if total_proposals > 0 else 0,
            "success_rate": round(passed_count / (passed_count + rejected_count) * 100, 2) if (passed_count + rejected_count) > 0 else 0
        }
    
    async def get_voting_results(self, proposal_id: str) -> Dict:
        """Mendapatkan hasil voting untuk proposal"""
        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError("Proposal not found")
        
        total_voting_power = await self._get_total_voting_power()
        
        return {
            "proposal_id": proposal_id,
            "status": proposal.status.value,
            "votes_for": proposal.votes_for,
            "votes_against": proposal.votes_against,
            "votes_abstain": proposal.votes_abstain,
            "total_votes": proposal.total_votes,
            "quorum_reached": proposal.total_votes >= int(total_voting_power * self.config.quorum_percentage / 100),
            "quorum_required": int(total_voting_power * self.config.quorum_percentage / 100),
            "total_voting_power": total_voting_power,
            "voting_percentage": (proposal.total_votes / total_voting_power * 100) if total_voting_power > 0 else 0
        }
    
    async def cast_vote(self, proposal_id: str, voter_address: str, vote_type: VoteType, **kwargs) -> Vote:
        """Cast vote dengan parameter yang lebih lengkap"""
        await self.vote(proposal_id, voter_address, vote_type, **kwargs)
        
        # Return the created vote
        vote_key = f"{self.vote_prefix}{proposal_id}:{voter_address}"
        vote_data = await self.redis_client.get(vote_key)
        if vote_data:
            vote_dict = json.loads(vote_data)
            return Vote.from_dict(vote_dict)
        return None
    
    async def change_vote(self, proposal_id: str, voter_address: str, new_vote_type: VoteType, **kwargs) -> Vote:
        """Change existing vote"""
        # Get existing vote
        vote_key = f"{self.vote_prefix}{proposal_id}:{voter_address}"
        existing_vote_data = await self.redis_client.get(vote_key)
        
        if not existing_vote_data:
            raise ValueError("No existing vote to change")
        
        existing_vote = json.loads(existing_vote_data)
        
        # Create new vote with change flag
        new_vote = Vote(
            vote_id=f"vote_{proposal_id}_{voter_address}_{int(time.time())}",
            proposal_id=proposal_id,
            voter_address=voter_address,
            vote_type=new_vote_type,
            voting_power=Decimal(str(existing_vote['voting_power'])),
            vote_weight=self.config.vote_weight_multiplier,
            timestamp=datetime.now(),
            is_changed=True,
            previous_vote=existing_vote['vote_type'],
            **kwargs
        )
        
        # Save new vote
        await self.redis_client.set(vote_key, json.dumps(new_vote.to_dict()))
        
        return new_vote
        
    async def delegate_voting_power(self, delegator_address: str, delegate_address: str, amount: int) -> bool:
        """Delegate voting power to another address"""
        if not self.token_manager:
            raise RuntimeError("Token manager not initialized")
        
        # Transfer voting power
        await self.token_manager.transfer_voting_power(delegator_address, delegate_address, amount)
        return True
    
    async def create_emergency_proposal(self, title: str, description: str, proposer: str, category: str, **kwargs) -> str:
        """Create emergency proposal with shorter voting period"""
        # Use emergency voting period
        original_period = self.config.voting_period_days
        self.config.voting_period_days = self.config.emergency_voting_period_hours / 24
        
        try:
            proposal_id = await self.create_proposal(title, description, proposer, category, **kwargs)
            return proposal_id
        finally:
            # Restore original period
            self.config.voting_period_days = original_period
    
    async def __aenter__(self):
        """Async context manager entry"""
        # Initialize Redis client if not already initialized
        if not self.redis_client:
            # Create a new Redis client
            redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.initialize_redis(redis_client)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.redis_client and hasattr(self.redis_client, 'aclose'):
            try:
                await self.redis_client.aclose()
            except Exception:
                # Fallback to close() if aclose() is not available
                await self.redis_client.close()
        return False
        """Get governance statistics"""
        # Get all proposals
        all_proposals = await self.get_all_proposals()
        active_proposals = await self.get_active_proposals()
        
        # Calculate statistics
        total_proposals = len(all_proposals)
        active_count = len(active_proposals)
        passed_count = len([p for p in all_proposals if p.status == ProposalStatus.PASSED])
        rejected_count = len([p for p in all_proposals if p.status == ProposalStatus.REJECTED])
        
        return {
            "total_proposals": total_proposals,
            "active_proposals": active_count,
            "passed_proposals": passed_count,
            "rejected_proposals": rejected_count,
            "participation_rate": (passed_count + rejected_count) / total_proposals * 100 if total_proposals > 0 else 0,
            "success_rate": passed_count / (passed_count + rejected_count) * 100 if (passed_count + rejected_count) > 0 else 0
        }
    
    # Private methods
    
    async def _save_proposal(self, proposal: Proposal):
        """Menyimpan proposal ke Redis"""
        key = f"{self.proposal_prefix}{proposal.proposal_id}"
        proposal_dict = proposal.to_dict()
        await self.redis_client.set(key, json.dumps(proposal_dict))
    
    async def _update_vote_counts(self, proposal_id: str, vote_type: VoteType, voting_power: int):
        """Update jumlah vote pada proposal"""
        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            return
        
        if vote_type == VoteType.FOR:
            proposal.votes_for += voting_power
        elif vote_type == VoteType.AGAINST:
            proposal.votes_against += voting_power
        elif vote_type == VoteType.ABSTAIN:
            proposal.votes_abstain += voting_power
        
        proposal.total_votes = proposal.votes_for + proposal.votes_against + proposal.votes_abstain
        
        await self._save_proposal(proposal)
    
    async def _check_quorum(self, proposal_id: str):
        """Cek apakah quorum tercapai"""
        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            return
        
        total_voting_power = await self._get_total_voting_power()
        quorum_required = int(total_voting_power * self.config.quorum_percentage)
        
        proposal.quorum_reached = proposal.total_votes >= quorum_required
        
        # Cek apakah voting selesai dan hitung hasil
        current_time = time.time()
        if current_time > proposal.voting_end:
            await self._finalize_voting(proposal_id)
        
        await self._save_proposal(proposal)
    
    async def _finalize_voting(self, proposal_id: str):
        """Finalisasi hasil voting"""
        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            return
        
        if proposal.status != ProposalStatus.ACTIVE:
            return
        
        # Hitung hasil
        total_votes = proposal.votes_for + proposal.votes_against + proposal.votes_abstain
        
        if not proposal.quorum_reached:
            proposal.status = ProposalStatus.REJECTED
        elif proposal.votes_for > proposal.votes_against:
            proposal.status = ProposalStatus.PASSED
        else:
            proposal.status = ProposalStatus.REJECTED
        
        await self._save_proposal(proposal)
    
    async def _get_total_voting_power(self) -> int:
        """Mendapatkan total voting power dari semua token holders"""
        # Implementasi sederhana - bisa diperluas dengan snapshot system
        token_keys = await self.redis_client.keys("governance_token:*")
        total_power = 0
        
        for key in token_keys:
            power = await self.redis_client.get(key)
            if power:
                total_power += int(power)
        
        return total_power
    
    async def _execute_proposal_by_type(self, proposal: Proposal) -> Dict:
        """Eksekusi proposal berdasarkan tipe"""
        proposal_type = proposal.proposal_type
        parameters = proposal.parameters
        
        if proposal_type == "parameter_change":
            return await self._execute_parameter_change(parameters)
        elif proposal_type == "treasury_spend":
            return await self._execute_treasury_spend(parameters)
        elif proposal_type == "upgrade_contract":
            return await self._execute_contract_upgrade(parameters)
        else:
            return {"status": "unsupported_type", "message": f"Proposal type {proposal_type} not supported"}
    
    async def _execute_parameter_change(self, parameters: Dict) -> Dict:
        """Eksekusi perubahan parameter governance"""
        try:
            param_name = parameters.get("parameter")
            new_value = parameters.get("value")
            
            if hasattr(self.config, param_name):
                setattr(self.config, param_name, new_value)
                return {
                    "status": "success",
                    "message": f"Parameter {param_name} updated to {new_value}",
                    "parameter": param_name,
                    "new_value": new_value
                }
            else:
                return {
                    "status": "failed",
                    "message": f"Parameter {param_name} not found",
                    "parameter": param_name
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "parameter": param_name if 'param_name' in locals() else "unknown"
            }
    
    async def _execute_treasury_spend(self, parameters: Dict) -> Dict:
        """Eksekusi pengeluaran dari treasury"""
        # Placeholder untuk treasury execution
        return {
            "status": "success",
            "message": "Treasury spend executed",
            "amount": parameters.get("amount", 0),
            "recipient": parameters.get("recipient", "")
        }
    
    async def _execute_contract_upgrade(self, parameters: Dict) -> Dict:
        """Eksekusi upgrade smart contract"""
        # Placeholder untuk contract upgrade
        return {
            "status": "success",
            "message": "Contract upgrade executed",
            "contract_address": parameters.get("contract_address", ""),
            "new_implementation": parameters.get("new_implementation", "")
        }


class GovernanceStats:
    """Statistik dan analytics untuk governance"""
    
    def __init__(self, governance_system: GovernanceSystem):
        self.governance = governance_system
    
    async def get_participation_rate(self, proposal_id: str) -> float:
        """Hitung participation rate untuk proposal"""
        results = await self.governance.get_voting_results(proposal_id)
        total_voting_power = results["total_voting_power"]
        total_votes = results["total_votes"]
        
        return (total_votes / total_voting_power * 100) if total_voting_power > 0 else 0
    
    async def get_governance_metrics(self) -> Dict:
        """Dapatkan metrics governance keseluruhan"""
        all_proposals = await self.governance.get_all_proposals()
        
        total_proposals = len(all_proposals)
        passed_proposals = len([p for p in all_proposals if p.status == ProposalStatus.PASSED])
        rejected_proposals = len([p for p in all_proposals if p.status == ProposalStatus.REJECTED])
        active_proposals = len([p for p in all_proposals if p.status == ProposalStatus.ACTIVE])
        
        total_voting_power = await self.governance._get_total_voting_power()
        
        return {
            "total_proposals": total_proposals,
            "passed_proposals": passed_proposals,
            "rejected_proposals": rejected_proposals,
            "active_proposals": active_proposals,
            "pass_rate": (passed_proposals / total_proposals * 100) if total_proposals > 0 else 0,
            "total_voting_power": total_voting_power,
            "average_participation": await self._calculate_average_participation()
        }
    
    async def _calculate_average_participation(self) -> float:
        """Hitung rata-rata partisipasi dari semua proposal"""
        all_proposals = await self.governance.get_all_proposals()
        
        if not all_proposals:
            return 0
        
        total_participation = 0
        valid_proposals = 0
        
        for proposal in all_proposals:
            if proposal.status in [ProposalStatus.PASSED, ProposalStatus.REJECTED]:
                results = await self.governance.get_voting_results(proposal.proposal_id)
                total_participation += results["voting_percentage"]
                valid_proposals += 1
        
        return total_participation / valid_proposals if valid_proposals > 0 else 0