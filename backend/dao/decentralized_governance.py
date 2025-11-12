"""
SANGKURIANG Decentralized Governance System
Implementasi sistem tata kelola terdesentralisasi untuk ekosistem pendanaan kripto Indonesia
"""

import asyncio
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature
import aiofiles
import aiohttp
import ipfshttpclient
from web3 import Web3
from eth_account import Account
import redis.asyncio as redis


class ProposalStatus(Enum):
    """Status proposal dalam sistem governance"""
    DRAFT = "draft"
    PENDING = "pending"
    ACTIVE = "active"
    PASSED = "passed"
    REJECTED = "rejected"
    EXECUTED = "executed"
    CANCELLED = "cancelled"


class ProposalType(Enum):
    """Jenis proposal yang didukung"""
    PARAMETER_CHANGE = "parameter_change"
    TREASURY_SPENDING = "treasury_spending"
    PROTOCOL_UPGRADE = "protocol_upgrade"
    COMMUNITY_GRANT = "community_grant"
    GOVERNANCE_CHANGE = "governance_change"


class VoteOption(Enum):
    """Opsi voting dalam proposal"""
    YES = "yes"
    NO = "no"
    ABSTAIN = "abstain"
    VETO = "veto"


@dataclass
class ProposalMetadata:
    """Metadata untuk proposal"""
    title: str
    description: str
    proposer_address: str
    proposal_type: ProposalType
    created_at: datetime
    voting_start_time: datetime
    voting_end_time: datetime
    execution_delay: timedelta = field(default_factory=lambda: timedelta(days=2))
    minimum_quorum: float = 0.1  # 10% dari total voting power
    minimum_threshold: float = 0.51  # 51% untuk pass
    deposit_required: float = 100.0  # SANG token yang dibutuhkan
    ipfs_hash: Optional[str] = None
    transaction_hash: Optional[str] = None


@dataclass
class VoteRecord:
    """Record untuk setiap vote"""
    voter_address: str
    proposal_id: str
    vote_option: VoteOption
    voting_power: float
    timestamp: datetime
    signature: str
    transaction_hash: Optional[str] = None


@dataclass
class ProposalResult:
    """Hasil dari proposal voting"""
    proposal_id: str
    total_votes: int
    total_voting_power: float
    yes_votes: int = 0
    no_votes: int = 0
    abstain_votes: int = 0
    veto_votes: int = 0
    yes_power: float = 0.0
    no_power: float = 0.0
    abstain_power: float = 0.0
    veto_power: float = 0.0
    quorum_reached: bool = False
    threshold_reached: bool = False
    passed: bool = False
    executed: bool = False
    execution_time: Optional[datetime] = None


@dataclass
class GovernanceParameters:
    """Parameter tata kelola yang dapat diubah melalui voting"""
    voting_period_days: int = 7
    execution_delay_days: int = 2
    minimum_deposit: float = 100.0
    maximum_deposit_period_days: int = 14
    quorum_percentage: float = 10.0
    threshold_percentage: float = 51.0
    veto_threshold_percentage: float = 33.3
    proposal_deposit_burn_percentage: float = 10.0
    max_simultaneous_proposals: int = 5


class DecentralizedGovernance:
    """Sistem tata kelola terdesentralisasi SANGKURIANG"""
    
    def __init__(
        self,
        web3_provider: str,
        contract_address: str,
        ipfs_node: str = "/ip4/127.0.0.1/tcp/5001/http",
        redis_url: str = "redis://localhost:6379"
    ):
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))
        self.contract_address = contract_address
        self.ipfs_client = ipfshttpclient.connect(ipfs_node)
        self.redis_client = redis.from_url(redis_url)
        
        # In-memory storage (akan diganti dengan blockchain storage)
        self.proposals: Dict[str, ProposalMetadata] = {}
        self.votes: Dict[str, List[VoteRecord]] = {}
        self.proposal_results: Dict[str, ProposalResult] = {}
        self.governance_parameters = GovernanceParameters()
        self.active_proposals: Set[str] = set()
        
        # Contract ABI (simplified)
        self.contract_abi = [
            {
                "inputs": [{"name": "proposalId", "type": "bytes32"}],
                "name": "getProposal",
                "outputs": [{"name": "", "type": "tuple"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "proposalId", "type": "bytes32"},
                    {"name": "vote", "type": "uint8"},
                    {"name": "votingPower", "type": "uint256"}
                ],
                "name": "castVote",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        
        self.contract = self.web3.eth.contract(
            address=contract_address,
            abi=self.contract_abi
        )
    
    async def initialize_governance(self) -> bool:
        """Inisialisasi sistem governance"""
        try:
            # Load existing proposals from IPFS
            await self._load_proposals_from_ipfs()
            
            # Setup governance parameters
            await self._setup_default_parameters()
            
            # Start governance monitoring loop
            asyncio.create_task(self._governance_monitoring_loop())
            
            print("✅ Decentralized governance system initialized")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize governance: {e}")
            return False
    
    async def create_proposal(
        self,
        title: str,
        description: str,
        proposer_address: str,
        proposal_type: ProposalType,
        voting_period_days: int = 7,
        deposit_amount: float = 100.0,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Buat proposal baru"""
        try:
            # Generate unique proposal ID
            proposal_id = self._generate_proposal_id(title, proposer_address)
            
            # Check if proposer has enough voting power
            voting_power = await self._get_voting_power(proposer_address)
            if voting_power < deposit_amount:
                return {
                    "success": False,
                    "error": "Insufficient voting power for proposal deposit"
                }
            
            # Create proposal metadata
            now = datetime.now()
            metadata = ProposalMetadata(
                title=title,
                description=description,
                proposer_address=proposer_address,
                proposal_type=proposal_type,
                created_at=now,
                voting_start_time=now + timedelta(hours=24),  # 24 hour delay
                voting_end_time=now + timedelta(days=voting_period_days + 1),
                deposit_required=deposit_amount,
                minimum_quorum=self.governance_parameters.quorum_percentage / 100,
                minimum_threshold=self.governance_parameters.threshold_percentage / 100
            )
            
            # Upload to IPFS
            ipfs_hash = await self._upload_to_ipfs({
                "title": title,
                "description": description,
                "type": proposal_type.value,
                "parameters": parameters or {},
                "created_at": now.isoformat()
            })
            metadata.ipfs_hash = ipfs_hash
            
            # Store proposal
            self.proposals[proposal_id] = metadata
            self.votes[proposal_id] = []
            self.proposal_results[proposal_id] = ProposalResult(
                proposal_id=proposal_id,
                total_votes=0,
                total_voting_power=0.0
            )
            
            # Lock deposit
            await self._lock_deposit(proposer_address, deposit_amount, proposal_id)
            
            # Broadcast to network
            await self._broadcast_proposal(proposal_id, metadata)
            
            print(f"✅ Proposal created: {proposal_id}")
            return {
                "success": True,
                "proposal_id": proposal_id,
                "ipfs_hash": ipfs_hash,
                "voting_start": metadata.voting_start_time.isoformat(),
                "voting_end": metadata.voting_end_time.isoformat()
            }
            
        except Exception as e:
            print(f"❌ Failed to create proposal: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cast_vote(
        self,
        voter_address: str,
        proposal_id: str,
        vote_option: VoteOption,
        signature: str
    ) -> Dict[str, Any]:
        """Memberikan vote pada proposal"""
        try:
            # Validate proposal exists and is active
            if proposal_id not in self.proposals:
                return {
                    "success": False,
                    "error": "Proposal not found"
                }
            
            proposal = self.proposals[proposal_id]
            now = datetime.now()
            
            if now < proposal.voting_start_time:
                return {
                    "success": False,
                    "error": "Voting has not started yet"
                }
            
            if now > proposal.voting_end_time:
                return {
                    "success": False,
                    "error": "Voting period has ended"
                }
            
            # Check if voter has already voted
            existing_votes = self.votes.get(proposal_id, [])
            for vote in existing_votes:
                if vote.voter_address == voter_address:
                    return {
                        "success": False,
                        "error": "Already voted on this proposal"
                    }
            
            # Get voting power
            voting_power = await self._get_voting_power(voter_address)
            if voting_power <= 0:
                return {
                    "success": False,
                    "error": "No voting power available"
                }
            
            # Validate signature
            is_valid = await self._validate_vote_signature(
                voter_address, proposal_id, vote_option, signature
            )
            if not is_valid:
                return {
                    "success": False,
                    "error": "Invalid vote signature"
                }
            
            # Create vote record
            vote_record = VoteRecord(
                voter_address=voter_address,
                proposal_id=proposal_id,
                vote_option=vote_option,
                voting_power=voting_power,
                timestamp=now,
                signature=signature
            )
            
            # Add to votes
            existing_votes.append(vote_record)
            self.votes[proposal_id] = existing_votes
            
            # Update proposal result
            await self._update_proposal_result(proposal_id, vote_record)
            
            # Broadcast vote to blockchain
            tx_hash = await self._broadcast_vote_to_blockchain(vote_record)
            vote_record.transaction_hash = tx_hash
            
            print(f"✅ Vote cast: {voter_address} -> {vote_option.value} on {proposal_id}")
            return {
                "success": True,
                "vote_record": {
                    "voter": voter_address,
                    "option": vote_option.value,
                    "power": voting_power,
                    "timestamp": now.isoformat(),
                    "tx_hash": tx_hash
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to cast vote: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_proposal_status(self, proposal_id: str) -> Dict[str, Any]:
        """Dapatkan status proposal"""
        if proposal_id not in self.proposals:
            return {"error": "Proposal not found"}
        
        proposal = self.proposals[proposal_id]
        result = self.proposal_results[proposal_id]
        now = datetime.now()
        
        # Determine current status
        if now < proposal.voting_start_time:
            status = "pending"
        elif now <= proposal.voting_end_time:
            status = "active"
        else:
            # Voting period ended, calculate final result
            if result.quorum_reached and result.threshold_reached and not result.passed:
                status = "passed"
                result.passed = True
            elif result.quorum_reached and result.veto_power > (result.total_voting_power * 0.33):
                status = "rejected"
            elif not result.quorum_reached:
                status = "rejected"
            else:
                status = "rejected"
        
        return {
            "proposal_id": proposal_id,
            "status": status,
            "title": proposal.title,
            "type": proposal.proposal_type.value,
            "voting_period": {
                "start": proposal.voting_start_time.isoformat(),
                "end": proposal.voting_end_time.isoformat()
            },
            "results": {
                "total_votes": result.total_votes,
                "total_voting_power": result.total_voting_power,
                "yes_power": result.yes_power,
                "no_power": result.no_power,
                "abstain_power": result.abstain_power,
                "veto_power": result.veto_power,
                "quorum_reached": result.quorum_reached,
                "threshold_reached": result.threshold_reached
            },
            "parameters": {
                "minimum_quorum": proposal.minimum_quorum,
                "minimum_threshold": proposal.minimum_threshold,
                "deposit_required": proposal.deposit_required
            }
        }
    
    async def execute_proposal(self, proposal_id: str) -> Dict[str, Any]:
        """Eksekusi proposal yang telah disetujui"""
        try:
            # Validate proposal can be executed
            if proposal_id not in self.proposals:
                return {"success": False, "error": "Proposal not found"}
            
            proposal = self.proposals[proposal_id]
            result = self.proposal_results[proposal_id]
            
            if not result.passed:
                return {"success": False, "error": "Proposal was not passed"}
            
            if result.executed:
                return {"success": False, "error": "Proposal already executed"}
            
            # Check execution delay
            execution_time = proposal.voting_end_time + proposal.execution_delay
            if datetime.now() < execution_time:
                return {
                    "success": False,
                    "error": f"Execution time not reached. Wait until {execution_time}"
                }
            
            # Execute based on proposal type
            execution_result = await self._execute_proposal_by_type(proposal)
            
            if execution_result["success"]:
                result.executed = True
                result.execution_time = datetime.now()
                
                # Return deposit to proposer
                await self._return_deposit(proposal.proposer_address, proposal.deposit_required)
                
                print(f"✅ Proposal executed: {proposal_id}")
                return {
                    "success": True,
                    "execution_result": execution_result,
                    "execution_time": result.execution_time.isoformat()
                }
            else:
                return execution_result
                
        except Exception as e:
            print(f"❌ Failed to execute proposal: {e}")
            return {"success": False, "error": str(e)}
    
    # Helper methods
    async def _get_voting_power(self, address: str) -> float:
        """Dapatkan voting power untuk address"""
        # This would typically query the blockchain for token balance/staking amount
        # For now, return a mock value based on SANG token balance
        try:
            # Mock implementation - replace with actual blockchain query
            balance = await self._query_token_balance(address)
            staked_amount = await self._query_staked_amount(address)
            return balance + (staked_amount * 1.5)  # Staked tokens get 1.5x voting power
        except Exception as e:
            print(f"Error getting voting power for {address}: {e}")
            return 0.0
    
    async def _validate_vote_signature(self, voter: str, proposal_id: str, vote: VoteOption, signature: str) -> bool:
        """Validasi tanda tangan vote"""
        try:
            # Create message to verify
            message = f"vote:{proposal_id}:{vote.value}:{int(time.time())}"
            message_hash = Web3.keccak(text=message).hex()
            
            # Verify signature (simplified - use proper EIP-191/712 in production)
            recovered_address = self.web3.eth.account.recover_message(
                message_hash,
                signature=signature
            )
            
            return recovered_address.lower() == voter.lower()
            
        except Exception as e:
            print(f"Signature validation error: {e}")
            return False
    
    async def _update_proposal_result(self, proposal_id: str, vote: VoteRecord) -> None:
        """Update hasil proposal dengan vote baru"""
        result = self.proposal_results[proposal_id]
        result.total_votes += 1
        result.total_voting_power += vote.voting_power
        
        # Update vote counts by option
        if vote.vote_option == VoteOption.YES:
            result.yes_votes += 1
            result.yes_power += vote.voting_power
        elif vote.vote_option == VoteOption.NO:
            result.no_votes += 1
            result.no_power += vote.voting_power
        elif vote.vote_option == VoteOption.ABSTAIN:
            result.abstain_votes += 1
            result.abstain_power += vote.voting_power
        elif vote.vote_option == VoteOption.VETO:
            result.veto_votes += 1
            result.veto_power += vote.voting_power
        
        # Check quorum and threshold
        proposal = self.proposals[proposal_id]
        total_power = await self._get_total_voting_power()
        
        result.quorum_reached = (result.total_voting_power / total_power) >= proposal.minimum_quorum
        
        if result.yes_power + result.no_power > 0:
            yes_ratio = result.yes_power / (result.yes_power + result.no_power)
            result.threshold_reached = yes_ratio >= proposal.minimum_threshold
    
    async def _execute_proposal_by_type(self, proposal: ProposalMetadata) -> Dict[str, Any]:
        """Eksekusi proposal berdasarkan tipe"""
        try:
            if proposal.proposal_type == ProposalType.PARAMETER_CHANGE:
                return await self._execute_parameter_change(proposal)
            elif proposal.proposal_type == ProposalType.TREASURY_SPENDING:
                return await self._execute_treasury_spending(proposal)
            elif proposal.proposal_type == ProposalType.PROTOCOL_UPGRADE:
                return await self._execute_protocol_upgrade(proposal)
            elif proposal.proposal_type == ProposalType.COMMUNITY_GRANT:
                return await self._execute_community_grant(proposal)
            elif proposal.proposal_type == ProposalType.GOVERNANCE_CHANGE:
                return await self._execute_governance_change(proposal)
            else:
                return {"success": False, "error": "Unknown proposal type"}
                
        except Exception as e:
            return {"success": False, "error": f"Execution failed: {str(e)}"}
    
    # Mock helper methods (implement with actual blockchain integration)
    async def _query_token_balance(self, address: str) -> float:
        """Mock: Query SANG token balance"""
        return 1000.0  # Mock balance
    
    async def _query_staked_amount(self, address: str) -> float:
        """Mock: Query staked SANG amount"""
        return 500.0  # Mock staked amount
    
    async def _get_total_voting_power(self) -> float:
        """Mock: Get total voting power"""
        return 1000000.0  # Mock total voting power
    
    def _generate_proposal_id(self, title: str, proposer: str) -> str:
        """Generate unique proposal ID"""
        content = f"{title}:{proposer}:{time.time()}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def _upload_to_ipfs(self, data: Dict[str, Any]) -> str:
        """Upload data ke IPFS"""
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            result = self.ipfs_client.add_json(json_data)
            return result
        except Exception as e:
            print(f"IPFS upload error: {e}")
            return ""
    
    async def _load_proposals_from_ipfs(self) -> None:
        """Load existing proposals dari IPFS"""
        # Implementation depends on how proposals are stored
        pass
    
    async def _setup_default_parameters(self) -> None:
        """Setup default governance parameters"""
        # Load from configuration or use defaults
        pass
    
    async def _governance_monitoring_loop(self) -> None:
        """Monitoring loop untuk governance"""
        while True:
            try:
                await self._process_active_proposals()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                print(f"Governance monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _process_active_proposals(self) -> None:
        """Process proposals yang sedang aktif"""
        now = datetime.now()
        for proposal_id in list(self.active_proposals):
            if proposal_id in self.proposals:
                proposal = self.proposals[proposal_id]
                if now > proposal.voting_end_time:
                    # Auto-finalize proposal
                    await self._finalize_proposal(proposal_id)
    
    async def _finalize_proposal(self, proposal_id: str) -> None:
        """Finalisasi proposal setelah voting period"""
        result = self.proposal_results[proposal_id]
        if not result.executed and result.passed:
            # Queue for execution
            await self.execute_proposal(proposal_id)
    
    async def _lock_deposit(self, address: str, amount: float, proposal_id: str) -> bool:
        """Lock proposal deposit"""
        # Implementation depends on token contract
        return True
    
    async def _return_deposit(self, address: str, amount: float) -> bool:
        """Return proposal deposit"""
        # Implementation depends on token contract
        return True
    
    async def _broadcast_proposal(self, proposal_id: str, metadata: ProposalMetadata) -> None:
        """Broadcast proposal ke network"""
        # Implementation depends on network architecture
        pass
    
    async def _broadcast_vote_to_blockchain(self, vote: VoteRecord) -> str:
        """Broadcast vote ke blockchain"""
        # Mock transaction hash
        return f"0x{hashlib.sha256(f'{vote.voter_address}:{vote.proposal_id}'.encode()).hexdigest()}"
    
    # Execution methods for different proposal types
    async def _execute_parameter_change(self, proposal: ProposalMetadata) -> Dict[str, Any]:
        """Eksekusi parameter change proposal"""
        try:
            # Load parameters from IPFS
            if proposal.ipfs_hash:
                params_data = await self._download_from_ipfs(proposal.ipfs_hash)
                parameters = params_data.get("parameters", {})
                
                # Update governance parameters
                for key, value in parameters.items():
                    if hasattr(self.governance_parameters, key):
                        setattr(self.governance_parameters, key, value)
                
                return {"success": True, "updated_parameters": parameters}
            
            return {"success": False, "error": "No parameters found"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_treasury_spending(self, proposal: ProposalMetadata) -> Dict[str, Any]:
        """Eksekusi treasury spending proposal"""
        try:
            # Implementation depends on treasury contract
            return {"success": True, "message": "Treasury spending executed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_protocol_upgrade(self, proposal: ProposalMetadata) -> Dict[str, Any]:
        """Eksekusi protocol upgrade proposal"""
        try:
            # Implementation depends on upgrade mechanism
            return {"success": True, "message": "Protocol upgrade executed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_community_grant(self, proposal: ProposalMetadata) -> Dict[str, Any]:
        """Eksekusi community grant proposal"""
        try:
            # Implementation depends on grant system
            return {"success": True, "message": "Community grant executed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_governance_change(self, proposal: ProposalMetadata) -> Dict[str, Any]:
        """Eksekusi governance change proposal"""
        try:
            # Implementation depends on governance system
            return {"success": True, "message": "Governance change executed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _download_from_ipfs(self, ipfs_hash: str) -> Dict[str, Any]:
        """Download data dari IPFS"""
        try:
            data = self.ipfs_client.cat(ipfs_hash)
            return json.loads(data.decode())
        except Exception as e:
            print(f"IPFS download error: {e}")
            return {}


# Example usage and testing
async def test_decentralized_governance():
    """Test sistem governance terdesentralisasi"""
    print("🚀 Testing SANGKURIANG Decentralized Governance System")
    
    # Initialize governance system
    governance = DecentralizedGovernance(
        web3_provider="https://mainnet.infura.io/v3/YOUR_PROJECT_ID",
        contract_address="0x...",  # Governance contract address
        ipfs_node="/ip4/127.0.0.1/tcp/5001/http",
        redis_url="redis://localhost:6379"
    )
    
    # Initialize system
    init_result = await governance.initialize_governance()
    if not init_result:
        print("❌ Failed to initialize governance")
        return
    
    # Create a test proposal
    proposal_result = await governance.create_proposal(
        title="Increase Minimum Deposit to 200 SANG",
        description="Proposal to increase the minimum deposit required for creating proposals from 100 to 200 SANG tokens to ensure higher quality proposals.",
        proposer_address="0x1234567890123456789012345678901234567890",
        proposal_type=ProposalType.PARAMETER_CHANGE,
        voting_period_days=7,
        deposit_amount=100.0,
        parameters={"minimum_deposit": 200.0}
    )
    
    if proposal_result["success"]:
        proposal_id = proposal_result["proposal_id"]
        print(f"✅ Proposal created: {proposal_id}")
        
        # Simulate voting
        voters = [
            ("0x1111111111111111111111111111111111111111", VoteOption.YES),
            ("0x2222222222222222222222222222222222222222", VoteOption.YES),
            ("0x3333333333333333333333333333333333333333", VoteOption.NO),
            ("0x4444444444444444444444444444444444444444", VoteOption.YES),
        ]
        
        for voter_address, vote_option in voters:
            # Mock signature (in production, this would be signed by the voter's private key)
            signature = f"signature_{voter_address}_{proposal_id}_{vote_option.value}"
            
            vote_result = await governance.cast_vote(
                voter_address=voter_address,
                proposal_id=proposal_id,
                vote_option=vote_option,
                signature=signature
            )
            
            if vote_result["success"]:
                print(f"✅ Vote cast: {voter_address} -> {vote_option.value}")
            else:
                print(f"❌ Vote failed: {vote_result['error']}")
        
        # Check proposal status
        status = await governance.get_proposal_status(proposal_id)
        print(f"📊 Proposal Status: {json.dumps(status, indent=2, default=str)}")
        
        # Execute proposal (if passed)
        execution_result = await governance.execute_proposal(proposal_id)
        print(f"⚡ Execution Result: {execution_result}")
    
    print("\n🎉 Decentralized governance test completed!")


if __name__ == "__main__":
    asyncio.run(test_decentralized_governance())