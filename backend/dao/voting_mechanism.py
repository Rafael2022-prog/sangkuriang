"""
SANGKURIANG Voting Mechanism with Smart Contracts
Implementasi mekanisme voting menggunakan smart contracts untuk keamanan dan transparansi
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
from web3.contract import Contract
import asyncio
import aiohttp
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import redis.asyncio as redis


class VoteWeightStrategy(Enum):
    """Strategi pembobotan voting power"""
    TOKEN_BALANCE = "token_balance"
    STAKED_TOKENS = "staked_tokens"
    LIQUIDITY_PROVISION = "liquidity_provision"
    REPUTATION_SCORE = "reputation_score"
    HYBRID_WEIGHTING = "hybrid_weighting"


class VotingMechanism(Enum):
    """Jenis mekanisme voting"""
    SIMPLE_MAJORITY = "simple_majority"
    SUPER_MAJORITY = "super_majority"
    QUADRATIC_VOTING = "quadratic_voting"
    LIQUID_DEMOCRACY = "liquid_democracy"
    TIME_WEIGHTED_VOTING = "time_weighted_voting"
    CONVICTION_VOTING = "conviction_voting"


@dataclass
class VoteOption:
    """Opsi voting dalam proposal"""
    id: str
    label: str
    description: str
    weight: float = 1.0


@dataclass
class VotingSession:
    """Sesi voting untuk proposal"""
    proposal_id: str
    session_id: str
    start_time: datetime
    end_time: datetime
    vote_options: List[VoteOption]
    voting_mechanism: VotingMechanism
    vote_weight_strategy: VoteWeightStrategy
    minimum_participation: float = 0.1  # 10% minimum participation
    minimum_approval: float = 0.51      # 51% minimum approval
    maximum_votes_per_address: int = 1
    allow_vote_change: bool = False
    allow_abstention: bool = True
    allow_veto: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VoteRecord:
    """Record untuk setiap vote"""
    voter_address: str
    proposal_id: str
    session_id: str
    vote_option_id: str
    voting_power: float
    conviction_multiplier: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    transaction_hash: Optional[str] = None
    signature: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VoteDelegation:
    """Delegasi voting power"""
    delegator_address: str
    delegate_address: str
    proposal_types: List[str] = field(default_factory=list)
    voting_power_percentage: float = 1.0  # 100% delegation
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    is_active: bool = True
    transaction_hash: Optional[str] = None


@dataclass
class VotingResult:
    """Hasil voting untuk proposal"""
    proposal_id: str
    session_id: str
    total_votes: int
    total_voting_power: float
    results_by_option: Dict[str, Dict[str, float]]
    participation_rate: float
    winning_option: Optional[str] = None
    is_passed: bool = False
    execution_ready: bool = False
    finalization_time: Optional[datetime] = None


class SmartContractVotingEngine:
    """Engine voting berbasis smart contract untuk SANGKURIANG DAO"""
    
    def __init__(
        self,
        web3_provider: str,
        governance_contract_address: str,
        voting_contract_address: str,
        token_contract_address: str,
        redis_url: str = "redis://localhost:6379"
    ):
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))
        self.governance_contract_address = governance_contract_address
        self.voting_contract_address = voting_contract_address
        self.token_contract_address = token_contract_address
        self.redis_client = redis.from_url(redis_url)
        
        # Contract ABIs (simplified versions)
        self.governance_abi = self._load_governance_abi()
        self.voting_abi = self._load_voting_abi()
        self.token_abi = self._load_token_abi()
        
        # Initialize contracts
        self.governance_contract = self.web3.eth.contract(
            address=governance_contract_address,
            abi=self.governance_abi
        )
        
        self.voting_contract = self.web3.eth.contract(
            address=voting_contract_address,
            abi=self.voting_abi
        )
        
        self.token_contract = self.web3.eth.contract(
            address=token_contract_address,
            abi=self.token_abi
        )
        
        # Active voting sessions
        self.active_sessions: Dict[str, VotingSession] = {}
        self.vote_records: Dict[str, List[VoteRecord]] = {}
        self.delegations: Dict[str, List[VoteDelegation]] = {}
        
        # Voting strategies configuration
        self.voting_strategies = {
            VotingMechanism.SIMPLE_MAJORITY: self._simple_majority_calculation,
            VotingMechanism.SUPER_MAJORITY: self._super_majority_calculation,
            VotingMechanism.QUADRATIC_VOTING: self._quadratic_voting_calculation,
            VotingMechanism.LIQUID_DEMOCRACY: self._liquid_democracy_calculation,
            VotingMechanism.TIME_WEIGHTED_VOTING: self._time_weighted_calculation,
            VotingMechanism.CONVICTION_VOTING: self._conviction_voting_calculation
        }
        
        self.weight_strategies = {
            VoteWeightStrategy.TOKEN_BALANCE: self._token_balance_weight,
            VoteWeightStrategy.STAKED_TOKENS: self._staked_tokens_weight,
            VoteWeightStrategy.LIQUIDITY_PROVISION: self._liquidity_provision_weight,
            VoteWeightStrategy.REPUTATION_SCORE: self._reputation_score_weight,
            VoteWeightStrategy.HYBRID_WEIGHTING: self._hybrid_weighting
        }
    
    def _load_governance_abi(self) -> List[Dict[str, Any]]:
        """Load Governance Contract ABI"""
        return [
            {
                "inputs": [
                    {"name": "proposalId", "type": "bytes32"},
                    {"name": "description", "type": "string"},
                    {"name": "votingPeriod", "type": "uint256"},
                    {"name": "voteOptions", "type": "string[]"}
                ],
                "name": "createProposal",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"name": "proposalId", "type": "bytes32"}],
                "name": "getProposal",
                "outputs": [
                    {"name": "exists", "type": "bool"},
                    {"name": "status", "type": "uint8"},
                    {"name": "startTime", "type": "uint256"},
                    {"name": "endTime", "type": "uint256"}
                ],
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
                    {"name": "voteOption", "type": "uint8"},
                    {"name": "votingPower", "type": "uint256"}
                ],
                "name": "castVote",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "delegator", "type": "address"},
                    {"name": "delegate", "type": "address"},
                    {"name": "proposalTypes", "type": "uint8[]"}
                ],
                "name": "delegateVote",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"name": "proposalId", "type": "bytes32"}],
                "name": "getVoteResults",
                "outputs": [
                    {"name": "totalVotes", "type": "uint256"},
                    {"name": "totalPower", "type": "uint256"},
                    {"name": "results", "type": "uint256[]"}
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    def _load_token_abi(self) -> List[Dict[str, Any]]:
        """Load Token Contract ABI"""
        return [
            {
                "inputs": [{"name": "account", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"name": "account", "type": "address"}],
                "name": "getStakedBalance",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    async def initialize_voting_system(self) -> bool:
        """Inisialisasi sistem voting"""
        try:
            # Test contract connections
            if not self.web3.is_connected():
                raise Exception("Web3 connection failed")
            
            # Test contract calls
            block_number = self.web3.eth.block_number
            print(f"✅ Connected to blockchain at block {block_number}")
            
            # Load existing voting sessions
            await self._load_active_sessions()
            
            # Start voting monitoring loop
            asyncio.create_task(self._voting_monitoring_loop())
            
            print("✅ Smart contract voting system initialized")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize voting system: {e}")
            return False
    
    async def create_voting_session(
        self,
        proposal_id: str,
        title: str,
        description: str,
        vote_options: List[VoteOption],
        voting_mechanism: VotingMechanism,
        vote_weight_strategy: VoteWeightStrategy,
        voting_period_days: int = 7,
        minimum_participation: float = 0.1,
        minimum_approval: float = 0.51,
        private_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Buat sesi voting baru"""
        try:
            # Generate session ID
            session_id = self._generate_session_id(proposal_id, title)
            
            # Create voting session
            now = datetime.now()
            session = VotingSession(
                proposal_id=proposal_id,
                session_id=session_id,
                start_time=now + timedelta(hours=24),  # 24 hour delay
                end_time=now + timedelta(days=voting_period_days + 1),
                vote_options=vote_options,
                voting_mechanism=voting_mechanism,
                vote_weight_strategy=vote_weight_strategy,
                minimum_participation=minimum_participation,
                minimum_approval=minimum_approval,
                metadata={
                    "title": title,
                    "description": description,
                    "created_at": now.isoformat()
                }
            )
            
            # Store session
            self.active_sessions[session_id] = session
            self.vote_records[session_id] = []
            
            # Create on-chain proposal if private key provided
            if private_key:
                tx_hash = await self._create_on_chain_proposal(
                    session, private_key
                )
                session.metadata["transaction_hash"] = tx_hash
            
            print(f"✅ Voting session created: {session_id}")
            return {
                "success": True,
                "session_id": session_id,
                "proposal_id": proposal_id,
                "voting_period": {
                    "start": session.start_time.isoformat(),
                    "end": session.end_time.isoformat()
                },
                "vote_options": [
                    {"id": opt.id, "label": opt.label, "description": opt.description}
                    for opt in vote_options
                ]
            }
            
        except Exception as e:
            print(f"❌ Failed to create voting session: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cast_vote(
        self,
        voter_address: str,
        session_id: str,
        vote_option_id: str,
        private_key: str,
        conviction_multiplier: float = 1.0
    ) -> Dict[str, Any]:
        """Memberikan vote dalam sesi"""
        try:
            # Validate session exists and is active
            if session_id not in self.active_sessions:
                return {"success": False, "error": "Voting session not found"}
            
            session = self.active_sessions[session_id]
            now = datetime.now()
            
            if now < session.start_time:
                return {"success": False, "error": "Voting has not started"}
            
            if now > session.end_time:
                return {"success": False, "error": "Voting period has ended"}
            
            # Validate vote option
            valid_option = any(opt.id == vote_option_id for opt in session.vote_options)
            if not valid_option:
                return {"success": False, "error": "Invalid vote option"}
            
            # Check if already voted (if vote change not allowed)
            if not session.allow_vote_change:
                existing_votes = self.vote_records.get(session_id, [])
                for vote in existing_votes:
                    if vote.voter_address.lower() == voter_address.lower():
                        return {"success": False, "error": "Already voted"}
            
            # Calculate voting power
            voting_power = await self._calculate_voting_power(
                voter_address, session.vote_weight_strategy, session_id
            )
            
            if voting_power <= 0:
                return {"success": False, "error": "No voting power available"}
            
            # Apply conviction multiplier
            final_voting_power = voting_power * conviction_multiplier
            
            # Create vote record
            vote_record = VoteRecord(
                voter_address=voter_address,
                proposal_id=session.proposal_id,
                session_id=session_id,
                vote_option_id=vote_option_id,
                voting_power=final_voting_power,
                conviction_multiplier=conviction_multiplier,
                timestamp=now
            )
            
            # Sign and broadcast vote to blockchain
            tx_hash = await self._broadcast_vote_to_blockchain(
                vote_record, private_key
            )
            vote_record.transaction_hash = tx_hash
            
            # Store vote record
            if session_id not in self.vote_records:
                self.vote_records[session_id] = []
            self.vote_records[session_id].append(vote_record)
            
            print(f"✅ Vote cast: {voter_address} -> {vote_option_id} (power: {final_voting_power})")
            return {
                "success": True,
                "vote_record": {
                    "voter": voter_address,
                    "option": vote_option_id,
                    "power": final_voting_power,
                    "conviction": conviction_multiplier,
                    "tx_hash": tx_hash
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to cast vote: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delegate_voting_power(
        self,
        delegator_address: str,
        delegate_address: str,
        proposal_types: List[str],
        voting_power_percentage: float = 1.0,
        private_key: str = "",
        delegation_period_days: int = 365
    ) -> Dict[str, Any]:
        """Delegasikan voting power ke delegate lain"""
        try:
            # Validate addresses
            if not Web3.is_address(delegator_address) or not Web3.is_address(delegate_address):
                return {"success": False, "error": "Invalid addresses"}
            
            # Validate percentage
            if voting_power_percentage <= 0 or voting_power_percentage > 1:
                return {"success": False, "error": "Invalid voting power percentage"}
            
            # Create delegation record
            now = datetime.now()
            delegation = VoteDelegation(
                delegator_address=delegator_address,
                delegate_address=delegate_address,
                proposal_types=proposal_types,
                voting_power_percentage=voting_power_percentage,
                start_time=now,
                end_time=now + timedelta(days=delegation_period_days)
            )
            
            # Create on-chain delegation
            tx_hash = await self._create_on_chain_delegation(
                delegation, private_key
            )
            delegation.transaction_hash = tx_hash
            
            # Store delegation
            if delegator_address not in self.delegations:
                self.delegations[delegator_address] = []
            self.delegations[delegator_address].append(delegation)
            
            print(f"✅ Voting power delegated: {delegator_address} -> {delegate_address}")
            return {
                "success": True,
                "delegation": {
                    "delegator": delegator_address,
                    "delegate": delegate_address,
                    "percentage": voting_power_percentage,
                    "proposal_types": proposal_types,
                    "tx_hash": tx_hash
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to delegate voting power: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_voting_results(self, session_id: str) -> Dict[str, Any]:
        """Dapatkan hasil voting untuk sesi"""
        try:
            if session_id not in self.active_sessions:
                return {"success": False, "error": "Voting session not found"}
            
            session = self.active_sessions[session_id]
            votes = self.vote_records.get(session_id, [])
            
            # Calculate results based on voting mechanism
            voting_result = await self._calculate_voting_results(session, votes)
            
            # Check if proposal passed
            is_passed = self._evaluate_proposal_outcome(session, voting_result)
            voting_result.is_passed = is_passed
            
            # Check if ready for execution
            now = datetime.now()
            voting_result.execution_ready = (
                now > session.end_time and 
                is_passed and 
                voting_result.participation_rate >= session.minimum_participation
            )
            
            return {
                "success": True,
                "results": {
                    "session_id": session_id,
                    "proposal_id": session.proposal_id,
                    "total_votes": voting_result.total_votes,
                    "total_voting_power": voting_result.total_voting_power,
                    "participation_rate": voting_result.participation_rate,
                    "is_passed": voting_result.is_passed,
                    "execution_ready": voting_result.execution_ready,
                    "results_by_option": voting_result.results_by_option,
                    "winning_option": voting_result.winning_option
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to get voting results: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Voting strategy implementations
    async def _simple_majority_calculation(
        self, session: VotingSession, votes: List[VoteRecord]
    ) -> VotingResult:
        """Hitung hasil dengan simple majority"""
        results_by_option = {}
        total_power = 0.0
        
        # Initialize results for each option
        for option in session.vote_options:
            results_by_option[option.id] = {
                "votes": 0,
                "voting_power": 0.0,
                "percentage": 0.0
            }
        
        # Aggregate votes
        for vote in votes:
            if vote.vote_option_id in results_by_option:
                results_by_option[vote.vote_option_id]["votes"] += 1
                results_by_option[vote.vote_option_id]["voting_power"] += vote.voting_power
                total_power += vote.voting_power
        
        # Calculate percentages and find winner
        winning_option = None
        max_power = 0.0
        
        for option_id, result in results_by_option.items():
            if total_power > 0:
                result["percentage"] = result["voting_power"] / total_power
            if result["voting_power"] > max_power:
                max_power = result["voting_power"]
                winning_option = option_id
        
        # Calculate participation rate
        total_eligible_power = await self._get_total_eligible_voting_power(session)
        participation_rate = total_power / total_eligible_power if total_eligible_power > 0 else 0
        
        return VotingResult(
            proposal_id=session.proposal_id,
            session_id=session.session_id,
            total_votes=len(votes),
            total_voting_power=total_power,
            results_by_option=results_by_option,
            participation_rate=participation_rate,
            winning_option=winning_option
        )
    
    async def _quadratic_voting_calculation(
        self, session: VotingSession, votes: List[VoteRecord]
    ) -> VotingResult:
        """Hitung hasil dengan quadratic voting"""
        results_by_option = {}
        total_power = 0.0
        
        # Initialize results for each option
        for option in session.vote_options:
            results_by_option[option.id] = {
                "votes": 0,
                "voting_power": 0.0,
                "quadratic_power": 0.0,
                "percentage": 0.0
            }
        
        # Aggregate votes with quadratic weighting
        for vote in votes:
            if vote.vote_option_id in results_by_option:
                quadratic_power = vote.voting_power ** 0.5  # Square root
                results_by_option[vote.vote_option_id]["votes"] += 1
                results_by_option[vote.vote_option_id]["voting_power"] += vote.voting_power
                results_by_option[vote.vote_option_id]["quadratic_power"] += quadratic_power
                total_power += quadratic_power
        
        # Calculate percentages and find winner
        winning_option = None
        max_quadratic_power = 0.0
        
        for option_id, result in results_by_option.items():
            if total_power > 0:
                result["percentage"] = result["quadratic_power"] / total_power
            if result["quadratic_power"] > max_quadratic_power:
                max_quadratic_power = result["quadratic_power"]
                winning_option = option_id
        
        # Calculate participation rate
        total_eligible_power = await self._get_total_eligible_voting_power(session)
        participation_rate = (len(votes) * 100) / total_eligible_power if total_eligible_power > 0 else 0
        
        return VotingResult(
            proposal_id=session.proposal_id,
            session_id=session.session_id,
            total_votes=len(votes),
            total_voting_power=total_power,
            results_by_option=results_by_option,
            participation_rate=participation_rate,
            winning_option=winning_option
        )
    
    # Voting power calculation strategies
    async def _token_balance_weight(self, address: str) -> float:
        """Hitung voting power berdasarkan token balance"""
        try:
            balance = self.token_contract.functions.balanceOf(address).call()
            return float(self.web3.from_wei(balance, 'ether'))
        except Exception as e:
            print(f"Error getting token balance for {address}: {e}")
            return 0.0
    
    async def _staked_tokens_weight(self, address: str) -> float:
        """Hitung voting power berdasarkan staked tokens"""
        try:
            staked_balance = self.token_contract.functions.getStakedBalance(address).call()
            return float(self.web3.from_wei(staked_balance, 'ether')) * 1.5  # 1.5x multiplier for staked tokens
        except Exception as e:
            print(f"Error getting staked balance for {address}: {e}")
            return 0.0
    
    async def _liquidity_provision_weight(self, address: str) -> float:
        """Hitung voting power berdasarkan liquidity provision"""
        # Implementation depends on liquidity pool contracts
        return 0.0
    
    async def _reputation_score_weight(self, address: str) -> float:
        """Hitung voting power berdasarkan reputation score"""
        # Implementation depends on reputation system
        return 0.0
    
    async def _hybrid_weighting(self, address: str) -> float:
        """Hitung voting power dengan hybrid weighting"""
        token_weight = await self._token_balance_weight(address)
        staked_weight = await self._staked_tokens_weight(address)
        liquidity_weight = await self._liquidity_provision_weight(address)
        reputation_weight = await self._reputation_score_weight(address)
        
        # Weighted combination
        total_weight = (
            token_weight * 0.4 +
            staked_weight * 0.3 +
            liquidity_weight * 0.2 +
            reputation_weight * 0.1
        )
        
        return total_weight
    
    # Helper methods
    async def _calculate_voting_power(
        self, address: str, strategy: VoteWeightStrategy, session_id: str
    ) -> float:
        """Hitung total voting power untuk address"""
        base_power = await self.weight_strategies[strategy](address)
        
        # Apply delegations
        delegated_power = await self._get_delegated_power(address, session_id)
        
        # Apply any active delegations from this address
        delegated_away = await self._get_delegated_away_power(address, session_id)
        
        final_power = base_power + delegated_power - delegated_away
        return max(0, final_power)
    
    async def _get_delegated_power(self, address: str, session_id: str) -> float:
        """Dapatkan voting power yang didelegasikan ke address"""
        total_delegated = 0.0
        
        for delegator, delegations in self.delegations.items():
            for delegation in delegations:
                if (delegation.delegate_address.lower() == address.lower() and
                    delegation.is_active and
                    delegation.end_time > datetime.now()):
                    
                    delegator_power = await self._calculate_voting_power(
                        delegator, VoteWeightStrategy.HYBRID_WEIGHTING, session_id
                    )
                    total_delegated += delegator_power * delegation.voting_power_percentage
        
        return total_delegated
    
    async def _get_delegated_away_power(self, address: str, session_id: str) -> float:
        """Dapatkan voting power yang didelegasikan dari address"""
        total_delegated_away = 0.0
        
        if address in self.delegations:
            for delegation in self.delegations[address]:
                if (delegation.is_active and
                    delegation.end_time > datetime.now()):
                    
                    delegator_power = await self._calculate_voting_power(
                        address, VoteWeightStrategy.HYBRID_WEIGHTING, session_id
                    )
                    total_delegated_away += delegator_power * delegation.voting_power_percentage
        
        return total_delegated_away
    
    async def _calculate_voting_results(
        self, session: VotingSession, votes: List[VoteRecord]
    ) -> VotingResult:
        """Hitung hasil voting berdasarkan mekanisme yang dipilih"""
        strategy_func = self.voting_strategies.get(session.voting_mechanism)
        if not strategy_func:
            raise Exception(f"Unknown voting mechanism: {session.voting_mechanism}")
        
        return await strategy_func(session, votes)
    
    def _evaluate_proposal_outcome(
        self, session: VotingSession, result: VotingResult
    ) -> bool:
        """Evaluasi apakah proposal lolos"""
        # Check minimum participation
        if result.participation_rate < session.minimum_participation:
            return False
        
        # Check minimum approval based on mechanism
        if session.voting_mechanism in [VotingMechanism.SIMPLE_MAJORITY, VotingMechanism.SUPER_MAJORITY]:
            if not result.winning_option:
                return False
            
            winning_power = result.results_by_option[result.winning_option]["voting_power"]
            approval_rate = winning_power / result.total_voting_power if result.total_voting_power > 0 else 0
            
            return approval_rate >= session.minimum_approval
        
        return False
    
    async def _get_total_eligible_voting_power(self, session: VotingSession) -> float:
        """Dapatkan total voting power yang eligible untuk sesi"""
        # This would typically query the total token supply or eligible addresses
        # For now, return a mock value
        return 1000000.0
    
    async def _create_on_chain_proposal(
        self, session: VotingSession, private_key: str
    ) -> str:
        """Buat proposal di blockchain"""
        try:
            account = Account.from_key(private_key)
            
            # Prepare transaction
            transaction = self.governance_contract.functions.createProposal(
                Web3.to_bytes(text=session.session_id),
                session.metadata.get("description", ""),
                int(session.voting_period.days * 24 * 60 * 60),  # Convert to seconds
                [opt.label for opt in session.vote_options]
            ).build_transaction({
                'from': account.address,
                'nonce': self.web3.eth.get_transaction_count(account.address),
                'gas': 200000,
                'gasPrice': self.web3.eth.gas_price
            })
            
            # Sign and send transaction
            signed_tx = self.web3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            return tx_hash.hex()
            
        except Exception as e:
            print(f"Error creating on-chain proposal: {e}")
            return ""
    
    async def _broadcast_vote_to_blockchain(
        self, vote: VoteRecord, private_key: str
    ) -> str:
        """Broadcast vote ke blockchain"""
        try:
            account = Account.from_key(private_key)
            
            # Map vote option to uint8
            vote_option_uint = self._map_vote_option_to_uint(vote.vote_option_id)
            
            # Prepare transaction
            transaction = self.voting_contract.functions.castVote(
                Web3.to_bytes(text=vote.session_id),
                vote_option_uint,
                int(vote.voting_power * 10**18)  # Convert to wei
            ).build_transaction({
                'from': account.address,
                'nonce': self.web3.eth.get_transaction_count(account.address),
                'gas': 100000,
                'gasPrice': self.web3.eth.gas_price
            })
            
            # Sign and send transaction
            signed_tx = self.web3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            return tx_hash.hex()
            
        except Exception as e:
            print(f"Error broadcasting vote to blockchain: {e}")
            return ""
    
    async def _create_on_chain_delegation(
        self, delegation: VoteDelegation, private_key: str
    ) -> str:
        """Buat delegasi di blockchain"""
        try:
            account = Account.from_key(private_key)
            
            # Map proposal types to uint8 array
            proposal_types_uint = [0] * len(delegation.proposal_types)  # Simplified mapping
            
            # Prepare transaction
            transaction = self.voting_contract.functions.delegateVote(
                delegation.delegator_address,
                delegation.delegate_address,
                proposal_types_uint
            ).build_transaction({
                'from': account.address,
                'nonce': self.web3.eth.get_transaction_count(account.address),
                'gas': 150000,
                'gasPrice': self.web3.eth.gas_price
            })
            
            # Sign and send transaction
            signed_tx = self.web3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            return tx_hash.hex()
            
        except Exception as e:
            print(f"Error creating on-chain delegation: {e}")
            return ""
    
    def _map_vote_option_to_uint(self, option_id: str) -> int:
        """Map vote option ID ke uint8"""
        # Simple mapping based on option ID
        if option_id == "yes":
            return 1
        elif option_id == "no":
            return 2
        elif option_id == "abstain":
            return 3
        elif option_id == "veto":
            return 4
        else:
            return 0
    
    def _generate_session_id(self, proposal_id: str, title: str) -> str:
        """Generate unique session ID"""
        content = f"{proposal_id}:{title}:{time.time()}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def _load_active_sessions(self) -> None:
        """Load active voting sessions"""
        # Implementation depends on storage mechanism
        pass
    
    async def _voting_monitoring_loop(self) -> None:
        """Monitoring loop untuk voting sessions"""
        while True:
            try:
                await self._process_active_sessions()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                print(f"Voting monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _process_active_sessions(self) -> None:
        """Process active voting sessions"""
        now = datetime.now()
        for session_id in list(self.active_sessions.keys()):
            session = self.active_sessions[session_id]
            if now > session.end_time:
                # Auto-finalize session
                await self._finalize_voting_session(session_id)
    
    async def _finalize_voting_session(self, session_id: str) -> None:
        """Finalisasi sesi voting"""
        try:
            # Get final results
            result = await self.get_voting_results(session_id)
            
            if result["success"]:
                # Store final results
                session = self.active_sessions[session_id]
                result_data = result["results"]
                
                print(f"✅ Voting session finalized: {session_id}")
                print(f"   Passed: {result_data['is_passed']}")
                print(f"   Participation: {result_data['participation_rate']:.2%}")
                print(f"   Winning option: {result_data['winning_option']}")
                
                # Remove from active sessions
                del self.active_sessions[session_id]
                
        except Exception as e:
            print(f"Error finalizing voting session: {e}")


# Example usage and testing
async def test_smart_contract_voting():
    """Test smart contract voting mechanism"""
    print("🚀 Testing SANGKURIANG Smart Contract Voting Mechanism")
    
    # Initialize voting engine
    voting_engine = SmartContractVotingEngine(
        web3_provider="https://mainnet.infura.io/v3/YOUR_PROJECT_ID",
        governance_contract_address="0x...",
        voting_contract_address="0x...",
        token_contract_address="0x..."
    )
    
    # Initialize system
    init_result = await voting_engine.initialize_voting_system()
    if not init_result:
        print("❌ Failed to initialize voting system")
        return
    
    # Create vote options
    vote_options = [
        VoteOption("yes", "Yes", "Approve the proposal"),
        VoteOption("no", "No", "Reject the proposal"),
        VoteOption("abstain", "Abstain", "Abstain from voting")
    ]
    
    # Create voting session
    session_result = await voting_engine.create_voting_session(
        proposal_id="proposal_123",
        title="Should we increase the minimum deposit?",
        description="Proposal to increase the minimum deposit required for creating proposals",
        vote_options=vote_options,
        voting_mechanism=VotingMechanism.SIMPLE_MAJORITY,
        vote_weight_strategy=VoteWeightStrategy.HYBRID_WEIGHTING,
        voting_period_days=7,
        minimum_participation=0.1,
        minimum_approval=0.51
    )
    
    if session_result["success"]:
        session_id = session_result["session_id"]
        print(f"✅ Voting session created: {session_id}")
        
        # Simulate voting
        voters = [
            ("0x1111111111111111111111111111111111111111", "yes", "private_key_1"),
            ("0x2222222222222222222222222222222222222222", "yes", "private_key_2"),
            ("0x3333333333333333333333333333333333333333", "no", "private_key_3"),
            ("0x4444444444444444444444444444444444444444", "yes", "private_key_4"),
        ]
        
        for voter_address, vote_option, private_key in voters:
            vote_result = await voting_engine.cast_vote(
                voter_address=voter_address,
                session_id=session_id,
                vote_option_id=vote_option,
                private_key=private_key,
                conviction_multiplier=1.0
            )
            
            if vote_result["success"]:
                print(f"✅ Vote cast: {voter_address} -> {vote_option}")
            else:
                print(f"❌ Vote failed: {vote_result['error']}")
        
        # Get voting results
        results = await voting_engine.get_voting_results(session_id)
        print(f"📊 Voting Results: {json.dumps(results, indent=2, default=str)}")
        
        # Test delegation
        delegation_result = await voting_engine.delegate_voting_power(
            delegator_address="0x5555555555555555555555555555555555555555",
            delegate_address="0x1111111111111111111111111111111111111111",
            proposal_types=["parameter_change", "treasury_spending"],
            voting_power_percentage=0.8,
            private_key="private_key_5"
        )
        
        if delegation_result["success"]:
            print(f"✅ Voting power delegated successfully")
    
    print("\n🎉 Smart contract voting test completed!")


if __name__ == "__main__":
    asyncio.run(test_smart_contract_voting())