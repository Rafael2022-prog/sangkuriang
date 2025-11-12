"""
SANGKURIANG Community Proposals System
Sistem proposal komunitas terdesentralisasi untuk DAO dengan verifikasi dan voting
"""

import asyncio
import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from decimal import Decimal
from web3 import Web3
from eth_account import Account
import redis.asyncio as redis
import aiofiles
import ipfshttpclient


class ProposalStatus(Enum):
    """Status proposal komunitas"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    VOTING = "voting"
    PASSED = "passed"
    REJECTED = "rejected"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ProposalType(Enum):
    """Jenis proposal komunitas"""
    FUNDING = "funding"
    TECHNICAL = "technical"
    GOVERNANCE = "governance"
    PARTNERSHIP = "partnership"
    MARKETING = "marketing"
    COMMUNITY = "community"
    EMERGENCY = "emergency"
    CONSTITUTIONAL = "constitutional"


class ProposalCategory(Enum):
    """Kategori proposal untuk klasifikasi"""
    PROTOCOL_UPGRADE = "protocol_upgrade"
    PARAMETER_CHANGE = "parameter_change"
    TREASURY_ALLOCATION = "treasury_allocation"
    COMMUNITY_GRANT = "community_grant"
    PARTNERSHIP_DEAL = "partnership_deal"
    MARKETING_INITIATIVE = "marketing_initiative"
    TECHNICAL_IMPROVEMENT = "technical_improvement"
    GOVERNANCE_MODIFICATION = "governance_modification"
    EMERGENCY_ACTION = "emergency_action"


class VoteType(Enum):
    """Jenis voting untuk proposal"""
    SIMPLE_MAJORITY = "simple_majority"
    SUPER_MAJORITY = "super_majority"
    UNANIMOUS = "unanimous"
    QUADRATIC = "quadratic"
    WEIGHTED = "weighted"
    TIME_WEIGHTED = "time_weighted"


class ProposalPriority(Enum):
    """Prioritas proposal"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    URGENT = "urgent"


@dataclass
class ProposalMetadata:
    """Metadata untuk proposal komunitas"""
    title: str
    description: str
    proposal_type: ProposalType
    category: ProposalCategory
    priority: ProposalPriority
    requested_funding: Optional[Decimal] = None
    implementation_timeline: Optional[str] = None
    expected_outcomes: List[str] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    required_expertise: List[str] = field(default_factory=list)
    budget_breakdown: Dict[str, Decimal] = field(default_factory=dict)
    deliverables: List[str] = field(default_factory=list)
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    team_members: List[str] = field(default_factory=list)
    external_partners: List[str] = field(default_factory=list)
    compliance_requirements: List[str] = field(default_factory=list)
    ipfs_hash: Optional[str] = None
    github_references: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    language: str = "id"  # Bahasa Indonesia default


@dataclass
class CommunityProposal:
    """Proposal komunitas SANGKURIANG"""
    proposal_id: str
    proposer_address: str
    metadata: ProposalMetadata
    status: ProposalStatus = ProposalStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    voting_start_time: Optional[datetime] = None
    voting_end_time: Optional[datetime] = None
    execution_time: Optional[datetime] = None
    required_votes: int = 1000
    current_votes: int = 0
    current_approvals: int = 0
    current_rejections: int = 0
    vote_type: VoteType = VoteType.SIMPLE_MAJORITY
    approval_threshold: float = 0.51  # 51% default
    rejection_threshold: float = 0.40  # 40% rejection threshold
    minimum_participation: float = 0.10  # 10% minimum participation
    required_stake: Decimal = Decimal('100')  # Minimum stake required
    current_stake: Decimal = Decimal('0')
    supporters: Set[str] = field(default_factory=set)
    opponents: Set[str] = field(default_factory=set)
    abstainers: Set[str] = field(default_factory=set)
    comments: List[Dict[str, Any]] = field(default_factory=list)
    revisions: List[Dict[str, Any]] = field(default_factory=list)
    related_proposals: List[str] = field(default_factory=list)
    ipfs_hash: Optional[str] = None
    transaction_hash: Optional[str] = None
    execution_transaction_hash: Optional[str] = None
    verification_score: float = 0.0
    community_score: float = 0.0
    technical_score: float = 0.0
    governance_score: float = 0.0
    
    def __post_init__(self):
        if not self.voting_start_time:
            self.voting_start_time = self.created_at + timedelta(days=7)  # 7 days review period
        if not self.voting_end_time:
            self.voting_end_time = self.voting_start_time + timedelta(days=14)  # 14 days voting period


@dataclass
class ProposalComment:
    """Komentar untuk proposal"""
    comment_id: str
    proposal_id: str
    author_address: str
    content: str
    comment_type: str  # "support", "oppose", "question", "suggestion", "technical_review"
    created_at: datetime = field(default_factory=datetime.now)
    parent_comment_id: Optional[str] = None
    upvotes: int = 0
    downvotes: int = 0
    replies: List[str] = field(default_factory=list)
    expert_verification: Optional[Dict[str, Any]] = None
    ipfs_hash: Optional[str] = None


@dataclass
class ProposalVote:
    """Vote untuk proposal"""
    vote_id: str
    proposal_id: str
    voter_address: str
    vote_choice: str  # "for", "against", "abstain"
    voting_power: Decimal
    vote_timestamp: datetime = field(default_factory=datetime.now)
    justification: Optional[str] = None
    stake_amount: Decimal = Decimal('0')
    delegation_address: Optional[str] = None
    ipfs_hash: Optional[str] = None
    transaction_hash: Optional[str] = None


@dataclass
class ProposalRevision:
    """Revisi proposal"""
    revision_id: str
    proposal_id: str
    revision_number: int
    changes_summary: str
    updated_metadata: Dict[str, Any]
    revised_by: str
    revised_at: datetime = field(default_factory=datetime.now)
    previous_version_hash: str
    new_version_hash: str
    approval_required: bool = True
    ipfs_hash: Optional[str] = None


@dataclass
class CommunityProposalMetrics:
    """Metrik untuk proposal komunitas"""
    total_proposals: int = 0
    active_proposals: int = 0
    pending_proposals: int = 0
    voting_proposals: int = 0
    passed_proposals: int = 0
    rejected_proposals: int = 0
    executed_proposals: int = 0
    average_voting_participation: float = 0.0
    average_approval_rate: float = 0.0
    total_community_votes: int = 0
    total_funding_requested: Decimal = Decimal('0')
    total_funding_approved: Decimal = Decimal('0')
    average_proposal_quality: float = 0.0
    community_engagement_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


class CommunityProposalSystem:
    """Sistem Proposal Komunitas Terdesentralisasi SANGKURIANG"""
    
    def __init__(
        self,
        web3_provider: str,
        governance_contract_address: str,
        voting_contract_address: str,
        ipfs_node: str = "/ip4/127.0.0.1/tcp/5001/http",
        redis_url: str = "redis://localhost:6379"
    ):
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))
        self.governance_contract_address = governance_contract_address
        self.voting_contract_address = voting_contract_address
        self.ipfs_client = ipfshttpclient.connect(ipfs_node)
        self.redis_client = redis.from_url(redis_url)
        
        # Contract ABIs
        self.governance_abi = self._load_governance_abi()
        self.voting_abi = self._load_voting_abi()
        
        # Initialize contracts
        self.governance_contract = self.web3.eth.contract(
            address=governance_contract_address,
            abi=self.governance_abi
        )
        
        self.voting_contract = self.web3.eth.contract(
            address=voting_contract_address,
            abi=self.voting_abi
        )
        
        # Proposal state
        self.proposals: Dict[str, CommunityProposal] = {}
        self.comments: Dict[str, List[ProposalComment]] = {}
        self.votes: Dict[str, List[ProposalVote]] = {}
        self.revisions: Dict[str, List[ProposalRevision]] = {}
        
        # Community state
        self.community_members: Set[str] = set()
        self.expert_verifiers: Set[str] = set()
        self.delegations: Dict[str, str] = {}  # delegator -> delegate
        
        # Configuration
        self.voting_periods = {
            ProposalType.EMERGENCY: timedelta(days=3),
            ProposalType.TECHNICAL: timedelta(days=14),
            ProposalType.GOVERNANCE: timedelta(days=21),
            ProposalType.CONSTITUTIONAL: timedelta(days=30),
            ProposalType.FUNDING: timedelta(days=14),
            ProposalType.PARTNERSHIP: timedelta(days=21),
            ProposalType.MARKETING: timedelta(days=14),
            ProposalType.COMMUNITY: timedelta(days=7)
        }
        
        self.minimum_stakes = {
            ProposalType.FUNDING: Decimal('1000'),
            ProposalType.TECHNICAL: Decimal('500'),
            ProposalType.GOVERNANCE: Decimal('2000'),
            ProposalType.PARTNERSHIP: Decimal('1500'),
            ProposalType.MARKETING: Decimal('500'),
            ProposalType.COMMUNITY: Decimal('100'),
            ProposalType.EMERGENCY: Decimal('5000'),
            ProposalType.CONSTITUTIONAL: Decimal('5000')
        }
        
        self.approval_thresholds = {
            ProposalType.EMERGENCY: 0.66,  # 66% for emergency
            ProposalType.TECHNICAL: 0.60,   # 60% for technical
            ProposalType.GOVERNANCE: 0.66,  # 66% for governance
            ProposalType.CONSTITUTIONAL: 0.75,  # 75% for constitutional
            ProposalType.FUNDING: 0.55,     # 55% for funding
            ProposalType.PARTNERSHIP: 0.60,  # 60% for partnership
            ProposalType.MARKETING: 0.51,    # 51% for marketing
            ProposalType.COMMUNITY: 0.51     # 51% for community
        }
        
        # Metrics
        self.metrics = CommunityProposalMetrics()
        
        # Monitoring
        self.monitoring_active = True
    
    def _load_governance_abi(self) -> List[Dict[str, Any]]:
        """Load Governance Contract ABI"""
        return [
            {
                "inputs": [
                    {"name": "proposalId", "type": "bytes32"},
                    {"name": "metadata", "type": "string"},
                    {"name": "proposalType", "type": "uint8"}
                ],
                "name": "submitProposal",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"name": "proposalId", "type": "bytes32"}],
                "name": "executeProposal",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"name": "proposalId", "type": "bytes32"}],
                "name": "getProposalStatus",
                "outputs": [{"name": "", "type": "uint8"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    def _load_voting_abi(self) -> List[Dict[str, Any]]:
        """Load Voting Contract ABI"""
        return [
            {
                "inputs": [
                    {"name": "proposalId", "type": "bytes32"},
                    {"name": "support", "type": "bool"},
                    {"name": "votingPower", "type": "uint256"}
                ],
                "name": "castVote",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"name": "proposalId", "type": "bytes32"}],
                "name": "getVoteResult",
                "outputs": [
                    {"name": "forVotes", "type": "uint256"},
                    {"name": "againstVotes", "type": "uint256"},
                    {"name": "abstainVotes", "type": "uint256"}
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    async def initialize_system(self, initial_members: List[str], expert_verifiers: List[str]) -> bool:
        """Inisialisasi sistem proposal komunitas"""
        try:
            # Validate Web3 connection
            if not self.web3.is_connected():
                raise Exception("Web3 connection failed")
            
            # Set community members
            self.community_members.update(initial_members)
            self.expert_verifiers.update(expert_verifiers)
            
            # Load existing proposals
            await self._load_existing_proposals()
            await self._load_existing_votes()
            await self._load_existing_comments()
            
            # Start monitoring
            asyncio.create_task(self._proposal_monitoring_loop())
            asyncio.create_task(self._voting_monitoring_loop())
            
            print(f"✅ Community proposal system initialized with {len(initial_members)} members")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize community proposal system: {e}")
            return False
    
    async def submit_proposal(
        self,
        proposer_address: str,
        metadata: ProposalMetadata,
        initial_stake: Decimal,
        private_key: str,
        related_proposals: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Mengajukan proposal komunitas baru"""
        try:
            # Validate proposer
            if proposer_address not in self.community_members:
                return {"success": False, "error": "Proposer not a community member"}
            
            # Validate minimum stake
            minimum_stake = self.minimum_stakes.get(metadata.proposal_type, Decimal('100'))
            if initial_stake < minimum_stake:
                return {
                    "success": False,
                    "error": f"Insufficient stake. Required: {minimum_stake}, Provided: {initial_stake}"
                }
            
            # Generate proposal ID
            proposal_id = self._generate_proposal_id(proposer_address, metadata)
            
            # Create proposal
            proposal = CommunityProposal(
                proposal_id=proposal_id,
                proposer_address=proposer_address,
                metadata=metadata,
                required_stake=minimum_stake,
                current_stake=initial_stake,
                related_proposals=related_proposals or [],
                status=ProposalStatus.PENDING_REVIEW
            )
            
            # Upload metadata to IPFS
            ipfs_data = {
                "proposal_id": proposal_id,
                "proposer": proposer_address,
                "metadata": {
                    "title": metadata.title,
                    "description": metadata.description,
                    "type": metadata.proposal_type.value,
                    "category": metadata.category.value,
                    "priority": metadata.priority.value,
                    "requested_funding": str(metadata.requested_funding) if metadata.requested_funding else None,
                    "implementation_timeline": metadata.implementation_timeline,
                    "expected_outcomes": metadata.expected_outcomes,
                    "success_metrics": metadata.success_metrics,
                    "risks": metadata.risks,
                    "required_expertise": metadata.required_expertise,
                    "budget_breakdown": {k: str(v) for k, v in metadata.budget_breakdown.items()},
                    "deliverables": metadata.deliverables,
                    "milestones": metadata.milestones,
                    "team_members": metadata.team_members,
                    "external_partners": metadata.external_partners,
                    "compliance_requirements": metadata.compliance_requirements,
                    "github_references": metadata.github_references,
                    "attachments": metadata.attachments,
                    "tags": metadata.tags,
                    "language": metadata.language
                },
                "created_at": proposal.created_at.isoformat(),
                "required_stake": str(minimum_stake),
                "vote_type": proposal.vote_type.value,
                "approval_threshold": proposal.approval_threshold,
                "minimum_participation": proposal.minimum_participation
            }
            
            ipfs_hash = await self._upload_to_ipfs(ipfs_data)
            proposal.ipfs_hash = ipfs_hash
            
            # Create on-chain proposal
            tx_hash = await self._create_on_chain_proposal(proposal_id, ipfs_hash, metadata.proposal_type, private_key)
            proposal.transaction_hash = tx_hash
            
            # Store proposal
            self.proposals[proposal_id] = proposal
            self.comments[proposal_id] = []
            self.votes[proposal_id] = []
            self.revisions[proposal_id] = []
            
            # Start review period
            asyncio.create_task(self._review_period_monitoring(proposal_id))
            
            print(f"✅ Proposal submitted: {proposal_id}")
            return {
                "success": True,
                "proposal_id": proposal_id,
                "ipfs_hash": ipfs_hash,
                "transaction_hash": tx_hash,
                "required_stake": str(minimum_stake),
                "voting_start_time": proposal.voting_start_time.isoformat(),
                "voting_end_time": proposal.voting_end_time.isoformat()
            }
            
        except Exception as e:
            print(f"❌ Failed to submit proposal: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def add_comment(
        self,
        proposal_id: str,
        author_address: str,
        content: str,
        comment_type: str,
        parent_comment_id: Optional[str] = None,
        private_key: str = ""
    ) -> Dict[str, Any]:
        """Menambahkan komentar ke proposal"""
        try:
            # Validate proposal exists
            if proposal_id not in self.proposals:
                return {"success": False, "error": "Proposal not found"}
            
            # Validate author
            if author_address not in self.community_members:
                return {"success": False, "error": "Author not a community member"}
            
            # Generate comment ID
            comment_id = self._generate_comment_id(proposal_id, author_address, content)
            
            # Create comment
            comment = ProposalComment(
                comment_id=comment_id,
                proposal_id=proposal_id,
                author_address=author_address,
                content=content,
                comment_type=comment_type,
                parent_comment_id=parent_comment_id
            )
            
            # Upload to IPFS
            ipfs_data = {
                "comment_id": comment_id,
                "proposal_id": proposal_id,
                "author": author_address,
                "content": content,
                "type": comment_type,
                "parent_comment_id": parent_comment_id,
                "created_at": comment.created_at.isoformat()
            }
            
            ipfs_hash = await self._upload_to_ipfs(ipfs_data)
            comment.ipfs_hash = ipfs_hash
            
            # Store comment
            if proposal_id not in self.comments:
                self.comments[proposal_id] = []
            self.comments[proposal_id].append(comment)
            
            # Update proposal engagement score
            await self._update_proposal_engagement_score(proposal_id)
            
            print(f"✅ Comment added to proposal {proposal_id}")
            return {
                "success": True,
                "comment_id": comment_id,
                "ipfs_hash": ipfs_hash
            }
            
        except Exception as e:
            print(f"❌ Failed to add comment: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cast_vote(
        self,
        proposal_id: str,
        voter_address: str,
        vote_choice: str,
        voting_power: Decimal,
        justification: Optional[str] = None,
        stake_amount: Optional[Decimal] = None,
        private_key: str = ""
    ) -> Dict[str, Any]:
        """Memberikan vote untuk proposal"""
        try:
            # Validate proposal exists and is in voting phase
            if proposal_id not in self.proposals:
                return {"success": False, "error": "Proposal not found"}
            
            proposal = self.proposals[proposal_id]
            
            if proposal.status != ProposalStatus.VOTING:
                return {"success": False, "error": "Proposal not in voting phase"}
            
            # Validate voter
            if voter_address not in self.community_members:
                return {"success": False, "error": "Voter not a community member"}
            
            # Check if already voted
            existing_votes = self.votes.get(proposal_id, [])
            for vote in existing_votes:
                if vote.voter_address.lower() == voter_address.lower():
                    return {"success": False, "error": "Already voted on this proposal"}
            
            # Check voting period
            now = datetime.now()
            if now < proposal.voting_start_time or now > proposal.voting_end_time:
                return {"success": False, "error": "Voting period not active"}
            
            # Validate vote choice
            valid_choices = ["for", "against", "abstain"]
            if vote_choice.lower() not in valid_choices:
                return {"success": False, "error": "Invalid vote choice"}
            
            # Generate vote ID
            vote_id = self._generate_vote_id(proposal_id, voter_address, vote_choice)
            
            # Create vote
            vote = ProposalVote(
                vote_id=vote_id,
                proposal_id=proposal_id,
                voter_address=voter_address,
                vote_choice=vote_choice.lower(),
                voting_power=voting_power,
                justification=justification,
                stake_amount=stake_amount or Decimal('0')
            )
            
            # Create on-chain vote
            tx_hash = await self._create_on_chain_vote(proposal_id, vote_choice.lower(), voting_power, private_key)
            vote.transaction_hash = tx_hash
            
            # Store vote
            if proposal_id not in self.votes:
                self.votes[proposal_id] = []
            self.votes[proposal_id].append(vote)
            
            # Update proposal vote counts
            await self._update_proposal_vote_counts(proposal_id)
            
            # Update voter tracking
            if vote_choice.lower() == "for":
                proposal.supporters.add(voter_address)
            elif vote_choice.lower() == "against":
                proposal.opponents.add(voter_address)
            else:
                proposal.abstainers.add(voter_address)
            
            print(f"✅ Vote cast on proposal {proposal_id}: {vote_choice}")
            return {
                "success": True,
                "vote_id": vote_id,
                "transaction_hash": tx_hash,
                "voting_power": str(voting_power)
            }
            
        except Exception as e:
            print(f"❌ Failed to cast vote: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def revise_proposal(
        self,
        proposal_id: str,
        revised_by: str,
        changes_summary: str,
        updated_metadata: Dict[str, Any],
        private_key: str = ""
    ) -> Dict[str, Any]:
        """Merevisi proposal yang ada"""
        try:
            # Validate proposal exists
            if proposal_id not in self.proposals:
                return {"success": False, "error": "Proposal not found"}
            
            proposal = self.proposals[proposal_id]
            
            # Validate reviser
            if revised_by != proposal.proposer_address:
                return {"success": False, "error": "Only proposer can revise proposal"}
            
            # Check if proposal can be revised
            if proposal.status not in [ProposalStatus.DRAFT, ProposalStatus.PENDING_REVIEW]:
                return {"success": False, "error": "Proposal cannot be revised in current status"}
            
            # Generate revision ID and number
            revision_id = self._generate_revision_id(proposal_id, revised_by)
            revision_number = len(self.revisions.get(proposal_id, [])) + 1
            
            # Create previous version hash
            previous_hash = hashlib.sha256(
                json.dumps(proposal.metadata.__dict__, default=str).encode()
            ).hexdigest()
            
            # Create new version hash
            new_hash = hashlib.sha256(
                json.dumps(updated_metadata, default=str).encode()
            ).hexdigest()
            
            # Create revision
            revision = ProposalRevision(
                revision_id=revision_id,
                proposal_id=proposal_id,
                revision_number=revision_number,
                changes_summary=changes_summary,
                updated_metadata=updated_metadata,
                revised_by=revised_by,
                previous_version_hash=previous_hash,
                new_version_hash=new_hash
            )
            
            # Upload to IPFS
            ipfs_data = {
                "revision_id": revision_id,
                "proposal_id": proposal_id,
                "revision_number": revision_number,
                "changes_summary": changes_summary,
                "updated_metadata": updated_metadata,
                "revised_by": revised_by,
                "previous_version_hash": previous_hash,
                "new_version_hash": new_hash,
                "revised_at": revision.revised_at.isoformat()
            }
            
            ipfs_hash = await self._upload_to_ipfs(ipfs_data)
            revision.ipfs_hash = ipfs_hash
            
            # Store revision
            if proposal_id not in self.revisions:
                self.revisions[proposal_id] = []
            self.revisions[proposal_id].append(revision)
            
            # Update proposal with new metadata
            # In real implementation, you'd update the proposal metadata
            
            print(f"✅ Proposal revised: {proposal_id}")
            return {
                "success": True,
                "revision_id": revision_id,
                "revision_number": revision_number,
                "ipfs_hash": ipfs_hash
            }
            
        except Exception as e:
            print(f"❌ Failed to revise proposal: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_proposal(
        self,
        proposal_id: str,
        executor_address: str,
        private_key: str
    ) -> Dict[str, Any]:
        """Mengeksekusi proposal yang disetujui"""
        try:
            # Validate proposal exists and is approved
            if proposal_id not in self.proposals:
                return {"success": False, "error": "Proposal not found"}
            
            proposal = self.proposals[proposal_id]
            
            if proposal.status != ProposalStatus.PASSED:
                return {"success": False, "error": "Proposal not passed"}
            
            # Validate executor
            if executor_address not in self.expert_verifiers:
                return {"success": False, "error": "Executor not authorized"}
            
            # Execute on-chain
            tx_hash = await self._execute_on_chain_proposal(proposal_id, private_key)
            
            if tx_hash:
                # Update proposal status
                proposal.status = ProposalStatus.EXECUTED
                proposal.execution_time = datetime.now()
                proposal.execution_transaction_hash = tx_hash
                
                # Update metrics
                await self._update_community_metrics()
                
                print(f"✅ Proposal executed: {proposal_id}")
                return {
                    "success": True,
                    "proposal_id": proposal_id,
                    "execution_transaction_hash": tx_hash
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to execute on-chain transaction"
                }
                
        except Exception as e:
            print(f"❌ Failed to execute proposal: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_proposal_status(self, proposal_id: str) -> Dict[str, Any]:
        """Dapatkan status proposal"""
        try:
            if proposal_id not in self.proposals:
                return {"success": False, "error": "Proposal not found"}
            
            proposal = self.proposals[proposal_id]
            votes = self.votes.get(proposal_id, [])
            comments = self.comments.get(proposal_id, [])
            
            # Calculate voting results
            for_votes = sum(v.voting_power for v in votes if v.vote_choice == "for")
            against_votes = sum(v.voting_power for v in votes if v.vote_choice == "against")
            abstain_votes = sum(v.voting_power for v in votes if v.vote_choice == "abstain")
            total_votes = for_votes + against_votes + abstain_votes
            
            participation_rate = 0.0
            if proposal.required_votes > 0:
                participation_rate = float(total_votes / proposal.required_votes)
            
            approval_rate = 0.0
            if total_votes > 0:
                approval_rate = float(for_votes / total_votes)
            
            return {
                "success": True,
                "proposal": {
                    "proposal_id": proposal_id,
                    "title": proposal.metadata.title,
                    "status": proposal.status.value,
                    "proposer": proposal.proposer_address,
                    "created_at": proposal.created_at.isoformat(),
                    "voting_period": {
                        "start": proposal.voting_start_time.isoformat() if proposal.voting_start_time else None,
                        "end": proposal.voting_end_time.isoformat() if proposal.voting_end_time else None
                    },
                    "voting_results": {
                        "for_votes": str(for_votes),
                        "against_votes": str(against_votes),
                        "abstain_votes": str(abstain_votes),
                        "total_votes": str(total_votes),
                        "participation_rate": participation_rate,
                        "approval_rate": approval_rate
                    },
                    "required_thresholds": {
                        "approval": proposal.approval_threshold,
                        "participation": proposal.minimum_participation
                    },
                    "engagement": {
                        "total_comments": len(comments),
                        "total_votes": len(votes),
                        "supporters": len(proposal.supporters),
                        "opponents": len(proposal.opponents)
                    },
                    "scores": {
                        "verification": proposal.verification_score,
                        "community": proposal.community_score,
                        "technical": proposal.technical_score,
                        "governance": proposal.governance_score
                    }
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to get proposal status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_community_metrics(self) -> Dict[str, Any]:
        """Dapatkan metrik komunitas"""
        try:
            await self._update_community_metrics()
            
            return {
                "success": True,
                "metrics": {
                    "total_proposals": self.metrics.total_proposals,
                    "active_proposals": self.metrics.active_proposals,
                    "passed_proposals": self.metrics.passed_proposals,
                    "rejected_proposals": self.metrics.rejected_proposals,
                    "executed_proposals": self.metrics.executed_proposals,
                    "average_voting_participation": self.metrics.average_voting_participation,
                    "average_approval_rate": self.metrics.average_approval_rate,
                    "total_community_votes": self.metrics.total_community_votes,
                    "total_funding_requested": str(self.metrics.total_funding_requested),
                    "total_funding_approved": str(self.metrics.total_funding_approved),
                    "community_engagement_score": self.metrics.community_engagement_score,
                    "last_updated": self.metrics.last_updated.isoformat()
                },
                "community_stats": {
                    "total_members": len(self.community_members),
                    "expert_verifiers": len(self.expert_verifiers),
                    "active_proposals": len([p for p in self.proposals.values() if p.status in [ProposalStatus.ACTIVE, ProposalStatus.VOTING]]),
                    "total_comments": sum(len(comments) for comments in self.comments.values())
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to get community metrics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Helper methods
    def _generate_proposal_id(self, proposer: str, metadata: ProposalMetadata) -> str:
        """Generate unique proposal ID"""
        content = f"{proposer}:{metadata.title}:{metadata.proposal_type.value}:{time.time()}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _generate_comment_id(self, proposal_id: str, author: str, content: str) -> str:
        """Generate unique comment ID"""
        content_hash = f"{proposal_id}:{author}:{content}:{time.time()}"
        return hashlib.sha256(content_hash.encode()).hexdigest()
    
    def _generate_vote_id(self, proposal_id: str, voter: str, choice: str) -> str:
        """Generate unique vote ID"""
        vote_data = f"{proposal_id}:{voter}:{choice}:{time.time()}"
        return hashlib.sha256(vote_data.encode()).hexdigest()
    
    def _generate_revision_id(self, proposal_id: str, reviser: str) -> str:
        """Generate unique revision ID"""
        revision_data = f"{proposal_id}:{reviser}:{time.time()}"
        return hashlib.sha256(revision_data.encode()).hexdigest()
    
    async def _upload_to_ipfs(self, data: Dict[str, Any]) -> str:
        """Upload data to IPFS"""
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            result = self.ipfs_client.add_json(json_data)
            return result
        except Exception as e:
            print(f"IPFS upload error: {e}")
            return ""
    
    async def _create_on_chain_proposal(self, proposal_id: str, metadata: str, proposal_type: ProposalType, private_key: str) -> str:
        """Create proposal on blockchain"""
        try:
            account = Account.from_key(private_key)
            
            tx = self.governance_contract.functions.submitProposal(
                proposal_id.encode(),
                metadata,
                list(ProposalType).index(proposal_type)
            ).build_transaction({
                'from': account.address,
                'nonce': self.web3.eth.get_transaction_count(account.address),
                'gas': 300000,
                'gasPrice': self.web3.eth.gas_price
            })
            
            signed_tx = self.web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            return tx_hash.hex()
            
        except Exception as e:
            print(f"Error creating on-chain proposal: {e}")
            return ""
    
    async def _create_on_chain_vote(self, proposal_id: str, support: bool, voting_power: Decimal, private_key: str) -> str:
        """Create vote on blockchain"""
        try:
            account = Account.from_key(private_key)
            
            tx = self.voting_contract.functions.castVote(
                proposal_id.encode(),
                support,
                int(voting_power)
            ).build_transaction({
                'from': account.address,
                'nonce': self.web3.eth.get_transaction_count(account.address),
                'gas': 150000,
                'gasPrice': self.web3.eth.gas_price
            })
            
            signed_tx = self.web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            return tx_hash.hex()
            
        except Exception as e:
            print(f"Error creating on-chain vote: {e}")
            return ""
    
    async def _execute_on_chain_proposal(self, proposal_id: str, private_key: str) -> str:
        """Execute proposal on blockchain"""
        try:
            account = Account.from_key(private_key)
            
            tx = self.governance_contract.functions.executeProposal(
                proposal_id.encode()
            ).build_transaction({
                'from': account.address,
                'nonce': self.web3.eth.get_transaction_count(account.address),
                'gas': 500000,
                'gasPrice': self.web3.eth.gas_price
            })
            
            signed_tx = self.web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            return tx_hash.hex()
            
        except Exception as e:
            print(f"Error executing on-chain proposal: {e}")
            return ""
    
    async def _update_proposal_vote_counts(self, proposal_id: str) -> None:
        """Update proposal vote counts"""
        proposal = self.proposals[proposal_id]
        votes = self.votes.get(proposal_id, [])
        
        proposal.current_votes = len(votes)
        proposal.current_approvals = len([v for v in votes if v.vote_choice == "for"])
        proposal.current_rejections = len([v for v in votes if v.vote_choice == "against"])
    
    async def _update_proposal_engagement_score(self, proposal_id: str) -> None:
        """Update proposal engagement score"""
        proposal = self.proposals[proposal_id]
        comments = self.comments.get(proposal_id, [])
        
        # Calculate engagement based on comments, votes, and activity
        comment_count = len(comments)
        vote_count = len(self.votes.get(proposal_id, []))
        
        # Simple engagement score calculation
        proposal.community_score = min(10.0, (comment_count * 0.5 + vote_count * 2.0) / 10.0)
    
    async def _update_community_metrics(self) -> None:
        """Update community metrics"""
        try:
            self.metrics.total_proposals = len(self.proposals)
            self.metrics.active_proposals = len([
                p for p in self.proposals.values()
                if p.status in [ProposalStatus.ACTIVE, ProposalStatus.VOTING]
            ])
            self.metrics.pending_proposals = len([
                p for p in self.proposals.values()
                if p.status == ProposalStatus.PENDING_REVIEW
            ])
            self.metrics.voting_proposals = len([
                p for p in self.proposals.values()
                if p.status == ProposalStatus.VOTING
            ])
            self.metrics.passed_proposals = len([
                p for p in self.proposals.values()
                if p.status == ProposalStatus.PASSED
            ])
            self.metrics.rejected_proposals = len([
                p for p in self.proposals.values()
                if p.status == ProposalStatus.REJECTED
            ])
            self.metrics.executed_proposals = len([
                p for p in self.proposals.values()
                if p.status == ProposalStatus.EXECUTED
            ])
            
            # Calculate voting participation
            total_votes = sum(len(votes) for votes in self.votes.values())
            self.metrics.total_community_votes = total_votes
            
            # Calculate funding metrics
            total_requested = sum(
                p.metadata.requested_funding or Decimal('0')
                for p in self.proposals.values()
            )
            total_approved = sum(
                p.metadata.requested_funding or Decimal('0')
                for p in self.proposals.values()
                if p.status == ProposalStatus.PASSED
            )
            
            self.metrics.total_funding_requested = total_requested
            self.metrics.total_funding_approved = total_approved
            
            # Calculate average scores
            if self.proposals:
                self.metrics.average_proposal_quality = sum(
                    p.verification_score + p.community_score + p.technical_score + p.governance_score
                    for p in self.proposals.values()
                ) / (len(self.proposals) * 4)
            
            self.metrics.last_updated = datetime.now()
            
        except Exception as e:
            print(f"Error updating community metrics: {e}")
    
    async def _review_period_monitoring(self, proposal_id: str) -> None:
        """Monitor review period for proposal"""
        proposal = self.proposals[proposal_id]
        
        while datetime.now() < proposal.voting_start_time:
            await asyncio.sleep(3600)  # Check every hour
        
        # Move to voting phase
        if proposal.status == ProposalStatus.PENDING_REVIEW:
            proposal.status = ProposalStatus.VOTING
            print(f"✅ Proposal {proposal_id} moved to voting phase")
    
    async def _voting_period_monitoring(self, proposal_id: str) -> None:
        """Monitor voting period for proposal"""
        proposal = self.proposals[proposal_id]
        
        while datetime.now() < proposal.voting_end_time:
            await asyncio.sleep(3600)  # Check every hour
        
        # Process voting results
        await self._process_voting_results(proposal_id)
    
    async def _process_voting_results(self, proposal_id: str) -> None:
        """Process voting results for proposal"""
        proposal = self.proposals[proposal_id]
        votes = self.votes.get(proposal_id, [])
        
        # Calculate results
        for_votes = sum(v.voting_power for v in votes if v.vote_choice == "for")
        against_votes = sum(v.voting_power for v in votes if v.vote_choice == "against")
        abstain_votes = sum(v.voting_power for v in votes if v.vote_choice == "abstain")
        total_votes = for_votes + against_votes + abstain_votes
        
        # Check participation
        participation_rate = 0.0
        if proposal.required_votes > 0:
            participation_rate = float(total_votes / proposal.required_votes)
        
        # Check approval
        approval_rate = 0.0
        if total_votes > 0:
            approval_rate = float(for_votes / total_votes)
        
        # Determine result
        if (participation_rate >= proposal.minimum_participation and
            approval_rate >= proposal.approval_threshold):
            proposal.status = ProposalStatus.PASSED
            print(f"✅ Proposal {proposal_id} PASSED")
        else:
            proposal.status = ProposalStatus.REJECTED
            print(f"❌ Proposal {proposal_id} REJECTED")
        
        # Update metrics
        await self._update_community_metrics()
    
    async def _proposal_monitoring_loop(self) -> None:
        """Monitoring loop for proposals"""
        while self.monitoring_active:
            try:
                await self._check_proposal_status_transitions()
                await self._check_expired_proposals()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                print(f"Proposal monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _voting_monitoring_loop(self) -> None:
        """Monitoring loop for voting"""
        while self.monitoring_active:
            try:
                await self._check_voting_periods()
                await asyncio.sleep(3600)  # Check every hour
            except Exception as e:
                print(f"Voting monitoring error: {e}")
                await asyncio.sleep(300)
    
    async def _load_existing_proposals(self) -> None:
        """Load existing proposals"""
        # Implementation depends on storage mechanism
        pass
    
    async def _load_existing_votes(self) -> None:
        """Load existing votes"""
        # Implementation depends on storage mechanism
        pass
    
    async def _load_existing_comments(self) -> None:
        """Load existing comments"""
        # Implementation depends on storage mechanism
        pass
    
    async def _check_proposal_status_transitions(self) -> None:
        """Check and handle proposal status transitions"""
        now = datetime.now()
        for proposal in self.proposals.values():
            if proposal.status == ProposalStatus.ACTIVE and now >= proposal.voting_start_time:
                proposal.status = ProposalStatus.VOTING
                asyncio.create_task(self._voting_period_monitoring(proposal.proposal_id))
    
    async def _check_expired_proposals(self) -> None:
        """Check and handle expired proposals"""
        now = datetime.now()
        for proposal in self.proposals.values():
            if (proposal.status == ProposalStatus.VOTING and
                now > proposal.voting_end_time):
                await self._process_voting_results(proposal.proposal_id)
    
    async def _check_voting_periods(self) -> None:
        """Check voting periods"""
        # This is handled by individual proposal monitoring tasks
        pass


# Example usage and testing
async def test_community_proposal_system():
    """Test SANGKURIANG Community Proposal System"""
    print("🚀 Testing SANGKURIANG Community Proposal System")
    
    # Initialize system
    proposal_system = CommunityProposalSystem(
        web3_provider="https://mainnet.infura.io/v3/YOUR_PROJECT_ID",
        governance_contract_address="0x...",
        voting_contract_address="0x..."
    )
    
    # Initialize with community members
    community_members = [
        "0x1111111111111111111111111111111111111111",
        "0x2222222222222222222222222222222222222222",
        "0x3333333333333333333333333333333333333333",
        "0x4444444444444444444444444444444444444444",
        "0x5555555555555555555555555555555555555555"
    ]
    
    expert_verifiers = [
        "0x1111111111111111111111111111111111111111",
        "0x2222222222222222222222222222222222222222"
    ]
    
    init_result = await proposal_system.initialize_system(community_members, expert_verifiers)
    if not init_result:
        print("❌ Failed to initialize proposal system")
        return
    
    # Create sample proposals
    proposals_data = [
        {
            "title": "Pengembangan Smart Contract Baru untuk DeFi",
            "description": "Proposal untuk mengembangkan smart contract baru yang akan meningkatkan efisiensi transaksi DeFi di ekosistem SANGKURIANG",
            "type": ProposalType.TECHNICAL,
            "category": ProposalCategory.TECHNICAL_IMPROVEMENT,
            "priority": ProposalPriority.HIGH,
            "requested_funding": Decimal("50000"),
            "implementation_timeline": "3 bulan",
            "expected_outcomes": [
                "Meningkatkan throughput transaksi sebesar 200%",
                "Mengurangi biaya gas sebesar 30%",
                "Meningkatkan keamanan dengan audit otomatis"
            ],
            "success_metrics": [
                "Jumlah transaksi per detik",
                "Biaya transaksi rata-rata",
                "Jumlah bug yang ditemukan"
            ],
            "risks": [
                "Kemungkinan bug dalam smart contract",
                "Keterlambatan implementasi",
                "Resiko keamanan"
            ],
            "team_members": ["0x1111111111111111111111111111111111111111"],
            "budget_breakdown": {
                "development": Decimal("30000"),
                "testing": Decimal("10000"),
                "deployment": Decimal("5000"),
                "contingency": Decimal("5000")
            }
        },
        {
            "title": "Program Edukasi Kriptografi untuk Komunitas",
            "description": "Proposal untuk membuat program edukasi komprehensif tentang kriptografi dan blockchain untuk komunitas Indonesia",
            "type": ProposalType.COMMUNITY,
            "category": ProposalCategory.COMMUNITY_GRANT,
            "priority": ProposalPriority.MEDIUM,
            "requested_funding": Decimal("25000"),
            "implementation_timeline": "6 bulan",
            "expected_outcomes": [
                "Meningkatkan literasi kriptografi komunitas",
                "Menciptakan 1000 developer baru",
                "Meningkatkan adopsi teknologi blockchain"
            ],
            "success_metrics": [
                "Jumlah peserta yang menyelesaikan program",
                "Jumlah developer yang tercipta",
                "Tingkat kepuasan peserta"
            ],
            "risks": [
                "Minimnya partisipasi",
                "Keterbatasan sumber daya",
                "Perubahan regulasi"
            ],
            "team_members": ["0x3333333333333333333333333333333333333333"],
            "budget_breakdown": {
                "content_development": Decimal("10000"),
                "instructor_fees": Decimal("8000"),
                "platform_costs": Decimal("4000"),
                "marketing": Decimal("3000")
            }
        }
    ]
    
    submitted_proposals = []
    for proposal_data in proposals_data:
        metadata = ProposalMetadata(
            title=proposal_data["title"],
            description=proposal_data["description"],
            proposal_type=proposal_data["type"],
            category=proposal_data["category"],
            priority=proposal_data["priority"],
            requested_funding=proposal_data["requested_funding"],
            implementation_timeline=proposal_data["implementation_timeline"],
            expected_outcomes=proposal_data["expected_outcomes"],
            success_metrics=proposal_data["success_metrics"],
            risks=proposal_data["risks"],
            team_members=proposal_data["team_members"],
            budget_breakdown=proposal_data["budget_breakdown"]
        )
        
        result = await proposal_system.submit_proposal(
            proposer_address=community_members[0],
            metadata=metadata,
            initial_stake=Decimal("1000"),
            private_key="private_key_for_proposer"  # Mock private key
        )
        
        if result["success"]:
            submitted_proposals.append(result["proposal_id"])
            print(f"✅ Proposal submitted: {result['proposal_id']}")
    
    # Add comments to proposals
    for proposal_id in submitted_proposals:
        comments = [
            {
                "author": community_members[1],
                "content": "Proposal ini sangat menarik dan dibutuhkan oleh komunitas. Saya mendukung implementasinya.",
                "type": "support"
            },
            {
                "author": community_members[2],
                "content": "Bagaimana dengan keamanan smart contract yang akan dikembangkan? Apakah akan ada audit independen?",
                "type": "question"
            },
            {
                "author": community_members[3],
                "content": "Saya menyarankan untuk menambahkan lebih banyak detail tentang timeline implementasi.",
                "type": "suggestion"
            }
        ]
        
        for comment_data in comments:
            comment_result = await proposal_system.add_comment(
                proposal_id=proposal_id,
                author_address=comment_data["author"],
                content=comment_data["content"],
                comment_type=comment_data["type"],
                private_key="private_key_for_author"  # Mock private key
            )
            
            if comment_result["success"]:
                print(f"✅ Comment added to {proposal_id}")
    
    # Simulate voting (after voting period starts)
    print("⏳ Waiting for voting period to start...")
    await asyncio.sleep(10)  # Simulate waiting
    
    # Cast votes
    for proposal_id in submitted_proposals:
        votes = [
            {
                "voter": community_members[0],
                "choice": "for",
                "voting_power": Decimal("500"),
                "justification": "Saya mendukung proposal ini karena akan memberikan nilai besar bagi komunitas."
            },
            {
                "voter": community_members[1],
                "choice": "for",
                "voting_power": Decimal("300"),
                "justification": "Proposal yang sangat baik dengan rencana implementasi yang jelas."
            },
            {
                "voter": community_members[2],
                "choice": "against",
                "voting_power": Decimal("200"),
                "justification": "Saya khawatir tentang aspek keamanan yang perlu diperkuat."
            },
            {
                "voter": community_members[3],
                "choice": "for",
                "voting_power": Decimal("400"),
                "justification": "Dukungan penuh untuk pengembangan infrastruktur komunitas."
            }
        ]
        
        for vote_data in votes:
            vote_result = await proposal_system.cast_vote(
                proposal_id=proposal_id,
                voter_address=vote_data["voter"],
                vote_choice=vote_data["choice"],
                voting_power=vote_data["voting_power"],
                justification=vote_data["justification"],
                private_key="private_key_for_voter"  # Mock private key
            )
            
            if vote_result["success"]:
                print(f"✅ Vote cast on {proposal_id}: {vote_data['choice']}")
    
    # Get proposal status
    for proposal_id in submitted_proposals:
        status_result = await proposal_system.get_proposal_status(proposal_id)
        if status_result["success"]:
            print(f"📊 Proposal Status: {json.dumps(status_result['proposal'], indent=2, default=str)}")
    
    # Get community metrics
    metrics_result = await proposal_system.get_community_metrics()
    if metrics_result["success"]:
        print(f"📈 Community Metrics: {json.dumps(metrics_result['metrics'], indent=2, default=str)}")
    
    print("\n🎉 Community proposal system test completed!")


if __name__ == "__main__":
    asyncio.run(test_community_proposal_system())