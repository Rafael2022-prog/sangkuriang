"""
SANGKURIANG Treasury Management System
Sistem manajemen treasury terdesentralisasi untuk DAO dengan multi-signature dan spending limits
"""

import asyncio
import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from decimal import Decimal
from web3 import Web3
from eth_account import Account
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import redis.asyncio as redis
import aiofiles
import ipfshttpclient


class TransactionType(Enum):
    """Jenis transaksi treasury"""
    OPERATIONAL = "operational"
    INVESTMENT = "investment"
    GRANT = "grant"
    EMERGENCY = "emergency"
    SALARY = "salary"
    MARKETING = "marketing"
    DEVELOPMENT = "development"


class TransactionStatus(Enum):
    """Status transaksi treasury"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class SpendingCategory(Enum):
    """Kategori spending untuk budgeting"""
    TECHNOLOGY = "technology"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    LEGAL = "legal"
    COMMUNITY = "community"
    RESEARCH = "research"
    EMERGENCY = "emergency"


@dataclass
class TreasuryTransaction:
    """Transaksi dalam sistem treasury"""
    transaction_id: str
    transaction_type: TransactionType
    amount: Decimal
    recipient_address: str
    category: SpendingCategory
    description: str
    requested_by: str
    requested_at: datetime
    required_approvals: int = 3
    current_approvals: int = 0
    current_rejections: int = 0
    status: TransactionStatus = TransactionStatus.PENDING
    execution_deadline: Optional[datetime] = None
    budget_period: str = "monthly"
    metadata: Dict[str, Any] = field(default_factory=dict)
    ipfs_hash: Optional[str] = None
    transaction_hash: Optional[str] = None


@dataclass
class TreasuryApproval:
    """Approval untuk transaksi treasury"""
    transaction_id: str
    approver_address: str
    approval_status: str  # "approved" or "rejected"
    approval_reason: str
    approval_timestamp: datetime
    signature: str
    transaction_hash: Optional[str] = None


@dataclass
class TreasuryBudget:
    """Budget untuk periode tertentu"""
    budget_id: str
    category: SpendingCategory
    period_start: datetime
    period_end: datetime
    allocated_amount: Decimal
    spent_amount: Decimal = Decimal('0')
    remaining_amount: Decimal = field(init=False)
    approval_threshold: Decimal = Decimal('0.1')  # 10% of budget
    warning_threshold: Decimal = Decimal('0.8')  # 80% of budget
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.remaining_amount = self.allocated_amount - self.spent_amount


@dataclass
class TreasuryMetrics:
    """Metrik treasury untuk monitoring"""
    total_balance: Decimal
    total_transactions: int
    pending_transactions: int
    approved_transactions: int
    executed_transactions: int
    monthly_spending: Decimal
    quarterly_spending: Decimal
    yearly_spending: Decimal
    average_transaction_size: Decimal
    largest_transaction: Decimal
    smallest_transaction: Decimal
    approval_rate: float
    rejection_rate: float
    budget_utilization: Dict[str, float]
    last_updated: datetime


@dataclass
class TreasuryConfiguration:
    """Konfigurasi sistem treasury"""
    minimum_approvers: int = 3
    maximum_approvers: int = 7
    default_approval_threshold: Decimal = Decimal('0.1')  # 10% of treasury balance
    emergency_approval_threshold: Decimal = Decimal('0.05')  # 5% for emergencies
    transaction_timeout_hours: int = 72
    budget_alert_threshold: float = 0.8
    spending_limit_daily: Decimal = Decimal('10000')
    spending_limit_weekly: Decimal = Decimal('50000')
    spending_limit_monthly: Decimal = Decimal('200000')
    auto_execute_threshold: Decimal = Decimal('1000')  # Auto-execute small transactions
    require_ipfs_documentation: bool = True
    enable_emergency_mode: bool = True


class TreasuryManagementSystem:
    """Sistem manajemen treasury terdesentralisasi SANGKURIANG"""
    
    def __init__(
        self,
        web3_provider: str,
        treasury_contract_address: str,
        multi_sig_wallet_address: str,
        ipfs_node: str = "/ip4/127.0.0.1/tcp/5001/http",
        redis_url: str = "redis://localhost:6379"
    ):
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))
        self.treasury_contract_address = treasury_contract_address
        self.multi_sig_wallet_address = multi_sig_wallet_address
        self.ipfs_client = ipfshttpclient.connect(ipfs_node)
        self.redis_client = redis.from_url(redis_url)
        
        # Contract ABIs
        self.treasury_abi = self._load_treasury_abi()
        self.multi_sig_abi = self._load_multi_sig_abi()
        
        # Initialize contracts
        self.treasury_contract = self.web3.eth.contract(
            address=treasury_contract_address,
            abi=self.treasury_abi
        )
        
        self.multi_sig_contract = self.web3.eth.contract(
            address=multi_sig_wallet_address,
            abi=self.multi_sig_abi
        )
        
        # Treasury state
        self.transactions: Dict[str, TreasuryTransaction] = {}
        self.approvals: Dict[str, List[TreasuryApproval]] = {}
        self.budgets: Dict[str, TreasuryBudget] = {}
        self.approved_signers: List[str] = []
        self.emergency_mode: bool = False
        
        # Configuration
        self.configuration = TreasuryConfiguration()
        
        # Transaction queues
        self.pending_transactions: List[str] = []
        self.approved_transactions: List[str] = []
        
        # Metrics
        self.metrics = TreasuryMetrics(
            total_balance=Decimal('0'),
            total_transactions=0,
            pending_transactions=0,
            approved_transactions=0,
            executed_transactions=0,
            monthly_spending=Decimal('0'),
            quarterly_spending=Decimal('0'),
            yearly_spending=Decimal('0'),
            average_transaction_size=Decimal('0'),
            largest_transaction=Decimal('0'),
            smallest_transaction=Decimal('0'),
            approval_rate=0.0,
            rejection_rate=0.0,
            budget_utilization={},
            last_updated=datetime.now()
        )
    
    def _load_treasury_abi(self) -> List[Dict[str, Any]]:
        """Load Treasury Contract ABI"""
        return [
            {
                "inputs": [
                    {"name": "recipient", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "category", "type": "uint8"},
                    {"name": "description", "type": "string"}
                ],
                "name": "proposeTransaction",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"name": "transactionId", "type": "uint256"}],
                "name": "approveTransaction",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"name": "transactionId", "type": "uint256"}],
                "name": "executeTransaction",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "getTreasuryBalance",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    def _load_multi_sig_abi(self) -> List[Dict[str, Any]]:
        """Load Multi-Signature Wallet Contract ABI"""
        return [
            {
                "inputs": [{"name": "owners", "type": "address[]"},
                          {"name": "required", "type": "uint256"}],
                "name": "setup",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"name": "transactionId", "type": "uint256"}],
                "name": "confirmTransaction",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"name": "transactionId", "type": "uint256"}],
                "name": "revokeConfirmation",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "getOwners",
                "outputs": [{"name": "", "type": "address[]"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    async def initialize_treasury(self, approved_signers: List[str]) -> bool:
        """Inisialisasi sistem treasury"""
        try:
            # Validate Web3 connection
            if not self.web3.is_connected():
                raise Exception("Web3 connection failed")
            
            # Set approved signers
            self.approved_signers = approved_signers
            
            # Load existing data
            await self._load_existing_transactions()
            await self._load_existing_budgets()
            await self._update_treasury_metrics()
            
            # Start monitoring loops
            asyncio.create_task(self._treasury_monitoring_loop())
            asyncio.create_task(self._budget_monitoring_loop())
            
            print(f"✅ Treasury system initialized with {len(approved_signers)} signers")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize treasury: {e}")
            return False
    
    async def propose_transaction(
        self,
        transaction_type: TransactionType,
        amount: Decimal,
        recipient_address: str,
        category: SpendingCategory,
        description: str,
        requested_by: str,
        private_key: str,
        required_approvals: Optional[int] = None,
        budget_period: str = "monthly",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Mengusulkan transaksi baru"""
        try:
            # Validate inputs
            if amount <= 0:
                return {"success": False, "error": "Amount must be positive"}
            
            if not Web3.is_address(recipient_address):
                return {"success": False, "error": "Invalid recipient address"}
            
            # Check spending limits
            limit_check = await self._check_spending_limits(amount, category)
            if not limit_check["within_limits"]:
                return {"success": False, "error": limit_check["error"]}
            
            # Check budget availability
            budget_check = await self._check_budget_availability(amount, category, budget_period)
            if not budget_check["available"]:
                return {"success": False, "error": budget_check["error"]}
            
            # Generate transaction ID
            transaction_id = self._generate_transaction_id(
                transaction_type, amount, recipient_address, requested_by
            )
            
            # Determine required approvals
            if required_approvals is None:
                required_approvals = self._calculate_required_approvals(amount)
            
            # Set execution deadline
            execution_deadline = datetime.now() + timedelta(
                hours=self.configuration.transaction_timeout_hours
            )
            
            # Create transaction
            transaction = TreasuryTransaction(
                transaction_id=transaction_id,
                transaction_type=transaction_type,
                amount=amount,
                recipient_address=recipient_address,
                category=category,
                description=description,
                requested_by=requested_by,
                requested_at=datetime.now(),
                required_approvals=required_approvals,
                budget_period=budget_period,
                execution_deadline=execution_deadline,
                metadata=metadata or {}
            )
            
            # Upload documentation to IPFS
            if self.configuration.require_ipfs_documentation:
                ipfs_data = {
                    "transaction_id": transaction_id,
                    "type": transaction_type.value,
                    "amount": str(amount),
                    "description": description,
                    "requested_by": requested_by,
                    "category": category.value,
                    "metadata": metadata or {}
                }
                ipfs_hash = await self._upload_to_ipfs(ipfs_data)
                transaction.ipfs_hash = ipfs_hash
            
            # Create on-chain proposal
            tx_hash = await self._create_on_chain_proposal(transaction, private_key)
            transaction.transaction_hash = tx_hash
            
            # Store transaction
            self.transactions[transaction_id] = transaction
            self.approvals[transaction_id] = []
            self.pending_transactions.append(transaction_id)
            
            print(f"✅ Transaction proposed: {transaction_id}")
            return {
                "success": True,
                "transaction_id": transaction_id,
                "required_approvals": required_approvals,
                "execution_deadline": execution_deadline.isoformat(),
                "transaction_hash": tx_hash
            }
            
        except Exception as e:
            print(f"❌ Failed to propose transaction: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def approve_transaction(
        self,
        transaction_id: str,
        approver_address: str,
        approval_status: str,
        approval_reason: str,
        private_key: str,
        signature: Optional[str] = None
    ) -> Dict[str, Any]:
        """Menyetujui atau menolak transaksi"""
        try:
            # Validate transaction exists
            if transaction_id not in self.transactions:
                return {"success": False, "error": "Transaction not found"}
            
            transaction = self.transactions[transaction_id]
            
            # Check if approver is authorized
            if approver_address not in self.approved_signers:
                return {"success": False, "error": "Unauthorized approver"}
            
            # Check if already approved/rejected
            existing_approvals = self.approvals.get(transaction_id, [])
            for approval in existing_approvals:
                if approval.approver_address.lower() == approver_address.lower():
                    return {"success": False, "error": "Already voted on this transaction"}
            
            # Check deadline
            if datetime.now() > transaction.execution_deadline:
                transaction.status = TransactionStatus.EXPIRED
                return {"success": False, "error": "Transaction has expired"}
            
            # Create approval record
            approval = TreasuryApproval(
                transaction_id=transaction_id,
                approver_address=approver_address,
                approval_status=approval_status,
                approval_reason=approval_reason,
                approval_timestamp=datetime.now(),
                signature=signature or ""
            )
            
            # Create on-chain approval
            tx_hash = await self._create_on_chain_approval(transaction_id, approval_status, private_key)
            approval.transaction_hash = tx_hash
            
            # Store approval
            if transaction_id not in self.approvals:
                self.approvals[transaction_id] = []
            self.approvals[transaction_id].append(approval)
            
            # Update transaction status
            if approval_status.lower() == "approved":
                transaction.current_approvals += 1
            else:
                transaction.current_rejections += 1
            
            # Check if transaction can be executed
            execution_result = await self._check_execution_eligibility(transaction_id)
            
            print(f"✅ Transaction {approval_status}: {transaction_id} by {approver_address}")
            return {
                "success": True,
                "transaction_id": transaction_id,
                "approval_status": approval_status,
                "current_approvals": transaction.current_approvals,
                "current_rejections": transaction.current_rejections,
                "can_execute": execution_result["can_execute"],
                "transaction_hash": tx_hash
            }
            
        except Exception as e:
            print(f"❌ Failed to approve transaction: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_transaction(
        self,
        transaction_id: str,
        executor_address: str,
        private_key: str
    ) -> Dict[str, Any]:
        """Mengeksekusi transaksi yang disetujui"""
        try:
            # Validate transaction exists and is approved
            if transaction_id not in self.transactions:
                return {"success": False, "error": "Transaction not found"}
            
            transaction = self.transactions[transaction_id]
            
            if transaction.status != TransactionStatus.APPROVED:
                return {"success": False, "error": "Transaction not approved"}
            
            # Check if executor is authorized
            if executor_address not in self.approved_signers:
                return {"success": False, "error": "Unauthorized executor"}
            
            # Execute on-chain transaction
            tx_hash = await self._execute_on_chain_transaction(transaction_id, private_key)
            
            if tx_hash:
                # Update transaction status
                transaction.status = TransactionStatus.EXECUTED
                transaction.transaction_hash = tx_hash
                
                # Update budget
                await self._update_budget_spending(transaction)
                
                # Update metrics
                await self._update_treasury_metrics()
                
                # Remove from queues
                if transaction_id in self.pending_transactions:
                    self.pending_transactions.remove(transaction_id)
                if transaction_id in self.approved_transactions:
                    self.approved_transactions.remove(transaction_id)
                
                print(f"✅ Transaction executed: {transaction_id}")
                return {
                    "success": True,
                    "transaction_id": transaction_id,
                    "transaction_hash": tx_hash,
                    "amount": str(transaction.amount),
                    "recipient": transaction.recipient_address
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to execute on-chain transaction"
                }
                
        except Exception as e:
            print(f"❌ Failed to execute transaction: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_budget(
        self,
        category: SpendingCategory,
        period_start: datetime,
        period_end: datetime,
        allocated_amount: Decimal,
        approval_threshold: Optional[Decimal] = None,
        warning_threshold: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Membuat budget untuk kategori spending"""
        try:
            # Validate inputs
            if allocated_amount <= 0:
                return {"success": False, "error": "Allocated amount must be positive"}
            
            if period_start >= period_end:
                return {"success": False, "error": "Invalid period dates"}
            
            # Generate budget ID
            budget_id = self._generate_budget_id(category, period_start)
            
            # Set thresholds
            if approval_threshold is None:
                approval_threshold = allocated_amount * Decimal('0.1')
            
            if warning_threshold is None:
                warning_threshold = allocated_amount * Decimal('0.8')
            
            # Create budget
            budget = TreasuryBudget(
                budget_id=budget_id,
                category=category,
                period_start=period_start,
                period_end=period_end,
                allocated_amount=allocated_amount,
                approval_threshold=approval_threshold,
                warning_threshold=warning_threshold
            )
            
            # Store budget
            self.budgets[budget_id] = budget
            
            print(f"✅ Budget created: {budget_id}")
            return {
                "success": True,
                "budget_id": budget_id,
                "category": category.value,
                "allocated_amount": str(allocated_amount),
                "period": f"{period_start.date()} to {period_end.date()}"
            }
            
        except Exception as e:
            print(f"❌ Failed to create budget: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_treasury_status(self) -> Dict[str, Any]:
        """Dapatkan status treasury saat ini"""
        try:
            # Update metrics
            await self._update_treasury_metrics()
            
            # Get current balance from blockchain
            blockchain_balance = await self._get_blockchain_balance()
            
            # Calculate pending amounts
            pending_amount = sum(
                self.transactions[tx_id].amount
                for tx_id in self.pending_transactions
            )
            
            approved_amount = sum(
                self.transactions[tx_id].amount
                for tx_id in self.approved_transactions
            )
            
            return {
                "success": True,
                "treasury_status": {
                    "blockchain_balance": str(blockchain_balance),
                    "available_balance": str(blockchain_balance - pending_amount - approved_amount),
                    "pending_amount": str(pending_amount),
                    "approved_amount": str(approved_amount),
                    "total_transactions": self.metrics.total_transactions,
                    "pending_transactions": len(self.pending_transactions),
                    "approved_transactions": len(self.approved_transactions),
                    "emergency_mode": self.emergency_mode,
                    "approved_signers": len(self.approved_signers)
                },
                "metrics": {
                    "monthly_spending": str(self.metrics.monthly_spending),
                    "quarterly_spending": str(self.metrics.quarterly_spending),
                    "yearly_spending": str(self.metrics.yearly_spending),
                    "approval_rate": self.metrics.approval_rate,
                    "rejection_rate": self.metrics.rejection_rate
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to get treasury status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_budget_report(self, category: Optional[SpendingCategory] = None) -> Dict[str, Any]:
        """Dapatkan laporan budget"""
        try:
            budgets_to_report = []
            
            if category:
                # Filter by category
                budgets_to_report = [
                    budget for budget in self.budgets.values()
                    if budget.category == category
                ]
            else:
                # All active budgets
                budgets_to_report = [
                    budget for budget in self.budgets.values()
                    if budget.is_active
                ]
            
            budget_report = []
            for budget in budgets_to_report:
                utilization_rate = float(budget.spent_amount / budget.allocated_amount) if budget.allocated_amount > 0 else 0
                
                budget_report.append({
                    "budget_id": budget.budget_id,
                    "category": budget.category.value,
                    "allocated_amount": str(budget.allocated_amount),
                    "spent_amount": str(budget.spent_amount),
                    "remaining_amount": str(budget.remaining_amount),
                    "utilization_rate": utilization_rate,
                    "period": f"{budget.period_start.date()} to {budget.period_end.date()}",
                    "is_active": budget.is_active
                })
            
            return {
                "success": True,
                "budgets": budget_report,
                "summary": {
                    "total_budgets": len(budget_report),
                    "total_allocated": str(sum(budget.allocated_amount for budget in budgets_to_report)),
                    "total_spent": str(sum(budget.spent_amount for budget in budgets_to_report)),
                    "total_remaining": str(sum(budget.remaining_amount for budget in budgets_to_report))
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to get budget report: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Helper methods
    def _generate_transaction_id(self, tx_type: TransactionType, amount: Decimal, recipient: str, requester: str) -> str:
        """Generate unique transaction ID"""
        content = f"{tx_type.value}:{amount}:{recipient}:{requester}:{time.time()}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _generate_budget_id(self, category: SpendingCategory, period_start: datetime) -> str:
        """Generate unique budget ID"""
        content = f"{category.value}:{period_start.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _calculate_required_approvals(self, amount: Decimal) -> int:
        """Hitung jumlah approval yang dibutuhkan berdasarkan jumlah"""
        balance = self.metrics.total_balance
        
        if amount > balance * Decimal('0.5'):  # > 50% of treasury
            return self.configuration.maximum_approvers
        elif amount > balance * Decimal('0.2'):  # > 20% of treasury
            return max(self.configuration.minimum_approvers + 1, self.configuration.maximum_approvers - 1)
        elif amount > balance * Decimal('0.1'):  # > 10% of treasury
            return self.configuration.minimum_approvers + 1
        else:
            return self.configuration.minimum_approvers
    
    async def _check_spending_limits(self, amount: Decimal, category: SpendingCategory) -> Dict[str, Any]:
        """Check if transaction is within spending limits"""
        now = datetime.now()
        
        # Daily limit check
        daily_spending = await self._get_daily_spending(now.date())
        if daily_spending + amount > self.configuration.spending_limit_daily:
            return {
                "within_limits": False,
                "error": "Exceeds daily spending limit"
            }
        
        # Weekly limit check
        weekly_spending = await self._get_weekly_spending(now.date())
        if weekly_spending + amount > self.configuration.spending_limit_weekly:
            return {
                "within_limits": False,
                "error": "Exceeds weekly spending limit"
            }
        
        # Monthly limit check
        monthly_spending = await self._get_monthly_spending(now.date())
        if monthly_spending + amount > self.configuration.spending_limit_monthly:
            return {
                "within_limits": False,
                "error": "Exceeds monthly spending limit"
            }
        
        return {"within_limits": True, "error": None}
    
    async def _check_budget_availability(self, amount: Decimal, category: SpendingCategory, period: str) -> Dict[str, Any]:
        """Check if budget has sufficient funds"""
        # Find applicable budget
        applicable_budget = None
        now = datetime.now()
        
        for budget in self.budgets.values():
            if (budget.category == category and 
                budget.is_active and 
                budget.period_start <= now <= budget.period_end):
                applicable_budget = budget
                break
        
        if not applicable_budget:
            return {
                "available": True,
                "error": None  # No budget constraint
            }
        
        if amount > applicable_budget.remaining_amount:
            return {
                "available": False,
                "error": f"Exceeds remaining budget: {applicable_budget.remaining_amount}"
            }
        
        return {
            "available": True,
            "error": None,
            "budget_id": applicable_budget.budget_id
        }
    
    async def _check_execution_eligibility(self, transaction_id: str) -> Dict[str, Any]:
        """Check if transaction can be executed"""
        transaction = self.transactions[transaction_id]
        approvals = self.approvals.get(transaction_id, [])
        
        approved_count = sum(1 for a in approvals if a.approval_status.lower() == "approved")
        rejected_count = sum(1 for a in approvals if a.approval_status.lower() == "rejected")
        
        can_execute = (
            approved_count >= transaction.required_approvals and
            rejected_count == 0 and
            transaction.status == TransactionStatus.PENDING
        )
        
        if can_execute:
            transaction.status = TransactionStatus.APPROVED
            if transaction_id in self.pending_transactions:
                self.pending_transactions.remove(transaction_id)
            if transaction_id not in self.approved_transactions:
                self.approved_transactions.append(transaction_id)
        
        return {
            "can_execute": can_execute,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "required_approvals": transaction.required_approvals
        }
    
    async def _update_budget_spending(self, transaction: TreasuryTransaction) -> None:
        """Update budget spending after transaction execution"""
        # Find applicable budget
        applicable_budget = None
        
        for budget in self.budgets.values():
            if (budget.category == transaction.category and 
                budget.is_active and 
                budget.period_start <= datetime.now() <= budget.period_end):
                applicable_budget = budget
                break
        
        if applicable_budget:
            applicable_budget.spent_amount += transaction.amount
            applicable_budget.remaining_amount = (
                applicable_budget.allocated_amount - applicable_budget.spent_amount
            )
    
    async def _update_treasury_metrics(self) -> None:
        """Update treasury metrics"""
        try:
            # Get blockchain balance
            blockchain_balance = await self._get_blockchain_balance()
            self.metrics.total_balance = blockchain_balance
            
            # Update transaction counts
            self.metrics.total_transactions = len(self.transactions)
            self.metrics.pending_transactions = len(self.pending_transactions)
            self.metrics.approved_transactions = len(self.approved_transactions)
            self.metrics.executed_transactions = len([
                tx for tx in self.transactions.values()
                if tx.status == TransactionStatus.EXECUTED
            ])
            
            # Calculate spending metrics
            executed_transactions = [
                tx for tx in self.transactions.values()
                if tx.status == TransactionStatus.EXECUTED
            ]
            
            if executed_transactions:
                amounts = [tx.amount for tx in executed_transactions]
                self.metrics.average_transaction_size = sum(amounts) / len(amounts)
                self.metrics.largest_transaction = max(amounts)
                self.metrics.smallest_transaction = min(amounts)
                
                # Calculate approval rates
                total_approvals = sum(len(self.approvals.get(tx_id, [])) for tx_id in self.transactions)
                approved_approvals = sum(
                    sum(1 for a in self.approvals.get(tx_id, []) if a.approval_status.lower() == "approved")
                    for tx_id in self.transactions
                )
                
                if total_approvals > 0:
                    self.metrics.approval_rate = approved_approvals / total_approvals
                    self.metrics.rejection_rate = 1 - self.metrics.approval_rate
            
            # Update budget utilization
            for budget in self.budgets.values():
                if budget.allocated_amount > 0:
                    utilization = float(budget.spent_amount / budget.allocated_amount)
                    self.metrics.budget_utilization[budget.category.value] = utilization
            
            self.metrics.last_updated = datetime.now()
            
        except Exception as e:
            print(f"Error updating treasury metrics: {e}")
    
    async def _get_blockchain_balance(self) -> Decimal:
        """Get treasury balance from blockchain"""
        try:
            balance_wei = self.treasury_contract.functions.getTreasuryBalance().call()
            return Decimal(self.web3.from_wei(balance_wei, 'ether'))
        except Exception as e:
            print(f"Error getting blockchain balance: {e}")
            return Decimal('0')
    
    async def _create_on_chain_proposal(self, transaction: TreasuryTransaction, private_key: str) -> str:
        """Create proposal on blockchain"""
        try:
            account = Account.from_key(private_key)
            
            # Prepare transaction
            tx = self.treasury_contract.functions.proposeTransaction(
                transaction.recipient_address,
                int(transaction.amount * 10**18),  # Convert to wei
                list(SpendingCategory).index(transaction.category),
                transaction.description
            ).build_transaction({
                'from': account.address,
                'nonce': self.web3.eth.get_transaction_count(account.address),
                'gas': 200000,
                'gasPrice': self.web3.eth.gas_price
            })
            
            # Sign and send
            signed_tx = self.web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            return tx_hash.hex()
            
        except Exception as e:
            print(f"Error creating on-chain proposal: {e}")
            return ""
    
    async def _create_on_chain_approval(self, transaction_id: str, status: str, private_key: str) -> str:
        """Create approval on blockchain"""
        try:
            account = Account.from_key(private_key)
            
            # Get transaction ID from contract
            # This is simplified - in real implementation, you'd get the contract transaction ID
            contract_tx_id = 0
            
            # Prepare transaction
            if status.lower() == "approved":
                tx = self.multi_sig_contract.functions.confirmTransaction(contract_tx_id).build_transaction({
                    'from': account.address,
                    'nonce': self.web3.eth.get_transaction_count(account.address),
                    'gas': 100000,
                    'gasPrice': self.web3.eth.gas_price
                })
            else:
                tx = self.multi_sig_contract.functions.revokeConfirmation(contract_tx_id).build_transaction({
                    'from': account.address,
                    'nonce': self.web3.eth.get_transaction_count(account.address),
                    'gas': 100000,
                    'gasPrice': self.web3.eth.gas_price
                })
            
            # Sign and send
            signed_tx = self.web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            return tx_hash.hex()
            
        except Exception as e:
            print(f"Error creating on-chain approval: {e}")
            return ""
    
    async def _execute_on_chain_transaction(self, transaction_id: str, private_key: str) -> str:
        """Execute transaction on blockchain"""
        try:
            account = Account.from_key(private_key)
            
            # Get transaction from contract
            # This is simplified - in real implementation, you'd get the contract transaction ID
            contract_tx_id = 0
            
            # Prepare transaction
            tx = self.treasury_contract.functions.executeTransaction(contract_tx_id).build_transaction({
                'from': account.address,
                'nonce': self.web3.eth.get_transaction_count(account.address),
                'gas': 200000,
                'gasPrice': self.web3.eth.gas_price
            })
            
            # Sign and send
            signed_tx = self.web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            return tx_hash.hex()
            
        except Exception as e:
            print(f"Error executing on-chain transaction: {e}")
            return ""
    
    async def _upload_to_ipfs(self, data: Dict[str, Any]) -> str:
        """Upload data to IPFS"""
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            result = self.ipfs_client.add_json(json_data)
            return result
        except Exception as e:
            print(f"IPFS upload error: {e}")
            return ""
    
    async def _load_existing_transactions(self) -> None:
        """Load existing transactions"""
        # Implementation depends on storage mechanism
        pass
    
    async def _load_existing_budgets(self) -> None:
        """Load existing budgets"""
        # Implementation depends on storage mechanism
        pass
    
    async def _get_daily_spending(self, date: datetime.date) -> Decimal:
        """Get daily spending amount"""
        # Implementation depends on transaction history
        return Decimal('0')
    
    async def _get_weekly_spending(self, date: datetime.date) -> Decimal:
        """Get weekly spending amount"""
        # Implementation depends on transaction history
        return Decimal('0')
    
    async def _get_monthly_spending(self, date: datetime.date) -> Decimal:
        """Get monthly spending amount"""
        # Implementation depends on transaction history
        return Decimal('0')
    
    async def _treasury_monitoring_loop(self) -> None:
        """Monitoring loop for treasury"""
        while True:
            try:
                await self._process_pending_transactions()
                await self._check_expired_transactions()
                await self._update_treasury_metrics()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                print(f"Treasury monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _budget_monitoring_loop(self) -> None:
        """Monitoring loop for budgets"""
        while True:
            try:
                await self._check_budget_alerts()
                await asyncio.sleep(3600)  # Check every hour
            except Exception as e:
                print(f"Budget monitoring error: {e}")
                await asyncio.sleep(300)
    
    async def _process_pending_transactions(self) -> None:
        """Process pending transactions"""
        # Implementation for processing logic
        pass
    
    async def _check_expired_transactions(self) -> None:
        """Check and handle expired transactions"""
        now = datetime.now()
        for transaction_id in list(self.pending_transactions):
            if transaction_id in self.transactions:
                transaction = self.transactions[transaction_id]
                if now > transaction.execution_deadline:
                    transaction.status = TransactionStatus.EXPIRED
                    self.pending_transactions.remove(transaction_id)
    
    async def _check_budget_alerts(self) -> None:
        """Check budget utilization and send alerts"""
        for budget in self.budgets.values():
            if budget.is_active and budget.allocated_amount > 0:
                utilization_rate = float(budget.spent_amount / budget.allocated_amount)
                
                if utilization_rate >= float(budget.warning_threshold):
                    print(f"⚠️ Budget alert: {budget.category.value} utilization at {utilization_rate:.1%}")
                
                if utilization_rate >= 1.0:
                    print(f"🚨 Budget exceeded: {budget.category.value}")


# Example usage and testing
async def test_treasury_management():
    """Test SANGKURIANG Treasury Management System"""
    print("🚀 Testing SANGKURIANG Treasury Management System")
    
    # Initialize treasury system
    treasury = TreasuryManagementSystem(
        web3_provider="https://mainnet.infura.io/v3/YOUR_PROJECT_ID",
        treasury_contract_address="0x...",
        multi_sig_wallet_address="0x..."
    )
    
    # Initialize with approved signers
    approved_signers = [
        "0x1111111111111111111111111111111111111111",
        "0x2222222222222222222222222222222222222222",
        "0x3333333333333333333333333333333333333333",
        "0x4444444444444444444444444444444444444444",
        "0x5555555555555555555555555555555555555555"
    ]
    
    init_result = await treasury.initialize_treasury(approved_signers)
    if not init_result:
        print("❌ Failed to initialize treasury")
        return
    
    # Create budgets
    budget_result = await treasury.create_budget(
        category=SpendingCategory.TECHNOLOGY,
        period_start=datetime.now(),
        period_end=datetime.now() + timedelta(days=30),
        allocated_amount=Decimal('50000'),
        approval_threshold=Decimal('5000'),
        warning_threshold=Decimal('40000')
    )
    
    if budget_result["success"]:
        print(f"✅ Budget created: {budget_result['budget_id']}")
    
    # Propose transactions
    transactions = [
        {
            "type": TransactionType.DEVELOPMENT,
            "amount": Decimal('15000'),
            "recipient": "0x6666666666666666666666666666666666666666",
            "category": SpendingCategory.TECHNOLOGY,
            "description": "Smart contract development costs",
            "requester": approved_signers[0]
        },
        {
            "type": TransactionType.MARKETING,
            "amount": Decimal('8000'),
            "recipient": "0x7777777777777777777777777777777777777777",
            "category": SpendingCategory.MARKETING,
            "description": "Community outreach program",
            "requester": approved_signers[1]
        }
    ]
    
    proposed_transactions = []
    for tx_data in transactions:
        proposal_result = await treasury.propose_transaction(
            transaction_type=tx_data["type"],
            amount=tx_data["amount"],
            recipient_address=tx_data["recipient"],
            category=tx_data["category"],
            description=tx_data["description"],
            requested_by=tx_data["requester"],
            private_key="private_key_for_requester"  # Mock private key
        )
        
        if proposal_result["success"]:
            proposed_transactions.append(proposal_result["transaction_id"])
            print(f"✅ Transaction proposed: {proposal_result['transaction_id']}")
    
    # Approve transactions
    for tx_id in proposed_transactions:
        for approver in approved_signers[:3]:  # First 3 approvers
            approval_result = await treasury.approve_transaction(
                transaction_id=tx_id,
                approver_address=approver,
                approval_status="approved",
                approval_reason="Transaction approved after review",
                private_key=f"private_key_for_{approver}",  # Mock private key
                signature=f"signature_from_{approver}"
            )
            
            if approval_result["success"]:
                print(f"✅ Transaction approved by {approver}")
    
    # Execute transactions
    for tx_id in proposed_transactions:
        execution_result = await treasury.execute_transaction(
            transaction_id=tx_id,
            executor_address=approved_signers[0],
            private_key="private_key_for_executor"  # Mock private key
        )
        
        if execution_result["success"]:
            print(f"✅ Transaction executed: {tx_id}")
    
    # Get treasury status
    status_result = await treasury.get_treasury_status()
    if status_result["success"]:
        print(f"📊 Treasury Status: {json.dumps(status_result['treasury_status'], indent=2)}")
    
    # Get budget report
    budget_report = await treasury.get_budget_report()
    if budget_report["success"]:
        print(f"📈 Budget Report: {json.dumps(budget_report['summary'], indent=2)}")
    
    print("\n🎉 Treasury management test completed!")


if __name__ == "__main__":
    asyncio.run(test_treasury_management())