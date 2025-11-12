"""
SANGKURIANG Treasury Management System
Pengelolaan dana komunitas secara transparan dan terdesentralisasi
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import hashlib
import redis.asyncio as redis
from decimal import Decimal


class TransactionType(Enum):
    """Jenis transaksi dalam treasury"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    PROPOSAL_FUNDING = "proposal_funding"
    OPERATIONAL = "operational"
    REWARD = "reward"
    PENALTY = "penalty"


class TransactionStatus(Enum):
    """Status transaksi"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass
class TreasuryTransaction:
    """Representasi transaksi treasury"""
    id: str
    transaction_type: TransactionType
    amount: Decimal
    currency: str
    from_address: Optional[str]
    to_address: Optional[str]
    status: TransactionStatus
    timestamp: float
    block_number: Optional[int]
    transaction_hash: Optional[str]
    proposal_id: Optional[str]
    description: str
    metadata: Optional[Dict] = None
    confirmations: int = 0
    required_confirmations: int = 3
    
    def to_dict(self) -> Dict:
        """Konversi transaksi ke dictionary"""
        return {
            'id': self.id,
            'transaction_type': self.transaction_type.value,
            'amount': str(self.amount),
            'currency': self.currency,
            'from_address': self.from_address,
            'to_address': self.to_address,
            'status': self.status.value,
            'timestamp': self.timestamp,
            'block_number': self.block_number,
            'transaction_hash': self.transaction_hash,
            'proposal_id': self.proposal_id,
            'description': self.description,
            'metadata': self.metadata or {},
            'confirmations': self.confirmations,
            'required_confirmations': self.required_confirmations
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TreasuryTransaction':
        """Buat transaksi dari dictionary"""
        return cls(
            id=data['id'],
            transaction_type=TransactionType(data['transaction_type']),
            amount=Decimal(data['amount']),
            currency=data['currency'],
            from_address=data.get('from_address'),
            to_address=data.get('to_address'),
            status=TransactionStatus(data['status']),
            timestamp=data['timestamp'],
            block_number=data.get('block_number'),
            transaction_hash=data.get('transaction_hash'),
            proposal_id=data.get('proposal_id'),
            description=data['description'],
            metadata=data.get('metadata', {}),
            confirmations=data.get('confirmations', 0),
            required_confirmations=data.get('required_confirmations', 3)
        )


@dataclass
class TreasuryBalance:
    """Saldo treasury"""
    currency: str
    available: Decimal
    locked: Decimal
    pending: Decimal
    total: Decimal


@dataclass
class TreasuryConfig:
    """Konfigurasi treasury"""
    min_deposit_amount: Decimal = Decimal("0.01")
    max_withdrawal_amount: Decimal = Decimal("1000000")
    required_confirmations: int = 3
    withdrawal_delay: int = 24 * 3600  # 24 jam
    treasury_fee_percentage: float = 0.001  # 0.1%
    emergency_threshold: Decimal = Decimal("1000")  # Minimum balance untuk emergency
    supported_tokens: List[str] = None  # List token yang didukung
    
    def __post_init__(self):
        if self.supported_tokens is None:
            self.supported_tokens = ["SANGKURIANG", "ETH", "BTC"]  # Default tokens


class TreasuryWallet:
    """Wallet untuk menyimpan dana treasury"""
    
    def __init__(self, wallet_address: str, private_key: Optional[str] = None):
        self.address = wallet_address
        self.private_key = private_key
        self.balances: Dict[str, TreasuryBalance] = {}
        self.nonce = 0
    
    def get_balance(self, currency: str) -> TreasuryBalance:
        """Dapatkan saldo untuk mata uang tertentu"""
        return self.balances.get(currency, TreasuryBalance(
            currency=currency,
            available=Decimal("0"),
            locked=Decimal("0"),
            pending=Decimal("0"),
            total=Decimal("0")
        ))
    
    def update_balance(self, currency: str, available: Decimal, locked: Decimal, pending: Decimal):
        """Update saldo wallet"""
        self.balances[currency] = TreasuryBalance(
            currency=currency,
            available=available,
            locked=locked,
            pending=pending,
            total=available + locked + pending
        )
    
    def to_dict(self) -> Dict:
        """Konversi wallet ke dictionary"""
        return {
            'address': self.address,
            'nonce': self.nonce,
            'balances': {
                currency: {
                    'currency': balance.currency,
                    'available': str(balance.available),
                    'locked': str(balance.locked),
                    'pending': str(balance.pending),
                    'total': str(balance.total)
                }
                for currency, balance in self.balances.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TreasuryWallet':
        """Buat wallet dari dictionary"""
        wallet = cls(
            wallet_address=data['address'],
            private_key=None  # Private key tidak disimpan dalam serialization
        )
        wallet.nonce = data['nonce']
        
        # Restore balances
        for currency, balance_data in data['balances'].items():
            wallet.balances[currency] = TreasuryBalance(
                currency=currency,
                available=Decimal(balance_data['available']),
                locked=Decimal(balance_data['locked']),
                pending=Decimal(balance_data['pending']),
                total=Decimal(balance_data['total'])
            )
        
        return wallet


class TreasuryManagement:
    """Sistem manajemen treasury utama"""
    
    def __init__(self, redis_client: redis.Redis, config: Optional[TreasuryConfig] = None):
        self.redis = redis_client
        self.config = config or TreasuryConfig()
        self.transaction_prefix = "treasury_tx:"
        self.balance_prefix = "treasury_balance:"
        self.pending_prefix = "treasury_pending:"
        self.transaction_counter_key = "treasury_tx_counter"
        self.treasury_wallet_key = "treasury_main_wallet"
        self.redis_client = redis_client  # Alias untuk context manager
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # Cleanup jika diperlukan
        if hasattr(self.redis, 'close'):
            try:
                await self.redis.close()
            except (TypeError, AttributeError):
                # Handle mock objects in tests
                pass
        return False
    
    async def deposit(
        self,
        amount: Decimal,
        currency: str,
        from_address: str,
        transaction_hash: str,
        block_number: int,
        description: str = "",
        metadata: Optional[Dict] = None
    ) -> str:
        """Melakukan deposit ke treasury"""
        # Validasi amount
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        if amount < self.config.min_deposit_amount:
            raise ValueError(f"Minimum deposit is {self.config.min_deposit_amount}")
        
        # Generate transaction ID
        counter = await self.redis.incr(self.transaction_counter_key)
        tx_id = f"treasury_deposit_{counter}_{int(time.time())}"
        
        # Buat transaksi
        transaction = TreasuryTransaction(
            id=tx_id,
            transaction_type=TransactionType.DEPOSIT,
            amount=amount,
            currency=currency,
            from_address=from_address,
            to_address=None,  # Treasury address
            status=TransactionStatus.PENDING,
            timestamp=time.time(),
            block_number=block_number,
            transaction_hash=transaction_hash,
            proposal_id=None,
            description=description,
            metadata=metadata or {}
        )
        
        # Simpan transaksi
        await self._save_transaction(transaction)
        
        # Update saldo (pending dulu sampai confirmed)
        await self._update_pending_balance(currency, amount)
        
        return tx_id
    
    async def withdraw(
        self,
        amount: Decimal,
        currency: str,
        to_address: str,
        proposal_id: Optional[str] = None,
        description: str = "",
        metadata: Optional[Dict] = None
    ) -> str:
        """Melakukan withdrawal dari treasury"""
        # Validasi currency
        if currency not in self.config.supported_tokens:
            raise ValueError(f"Unsupported token: {currency}")
        
        # Validasi amount
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        if amount > self.config.max_withdrawal_amount:
            raise ValueError(f"Maximum withdrawal is {self.config.max_withdrawal_amount}")
        
        # Cek saldo yang tersedia
        available_balance = await self.get_available_balance(currency)
        if available_balance < amount:
            raise ValueError(f"Insufficient balance. Available: {available_balance}")
        
        # Cek emergency threshold
        if await self.get_available_balance(currency) - amount < self.config.emergency_threshold:
            raise ValueError("Withdrawal would bring balance below emergency threshold")
        
        # Generate transaction ID
        counter = await self.redis.incr(self.transaction_counter_key)
        tx_id = f"treasury_withdrawal_{counter}_{int(time.time())}"
        
        # Buat transaksi
        transaction = TreasuryTransaction(
            id=tx_id,
            transaction_type=TransactionType.WITHDRAWAL,
            amount=amount,
            currency=currency,
            from_address=None,  # Treasury address
            to_address=to_address,
            status=TransactionStatus.PENDING,
            timestamp=time.time(),
            block_number=None,
            transaction_hash=None,
            proposal_id=proposal_id,
            description=description,
            metadata=metadata or {}
        )
        
        # Simpan transaksi
        await self._save_transaction(transaction)
        
        # Lock saldo untuk withdrawal
        await self._lock_balance(currency, amount)
        
        return tx_id
    
    async def confirm_transaction(self, tx_id: str, transaction_hash: str, block_number: int) -> bool:
        """Konfirmasi transaksi"""
        transaction = await self.get_transaction(tx_id)
        if not transaction:
            raise ValueError("Transaction not found")
        
        if transaction.status != TransactionStatus.PENDING:
            raise ValueError("Transaction not in pending status")
        
        # Update status transaksi
        transaction.status = TransactionStatus.CONFIRMED
        transaction.transaction_hash = transaction_hash
        transaction.block_number = block_number
        transaction.confirmations = self.config.required_confirmations
        
        await self._save_transaction(transaction)
        
        # Update saldo
        if transaction.transaction_type == TransactionType.DEPOSIT:
            await self._confirm_deposit(transaction)
        elif transaction.transaction_type == TransactionType.WITHDRAWAL:
            await self._confirm_withdrawal(transaction)
        
        return True
    
    async def reject_transaction(self, tx_id: str, reason: str) -> bool:
        """Reject transaksi"""
        transaction = await self.get_transaction(tx_id)
        if not transaction:
            raise ValueError("Transaction not found")
        
        if transaction.status != TransactionStatus.PENDING:
            raise ValueError("Transaction not in pending status")
        
        # Update status transaksi
        transaction.status = TransactionStatus.REJECTED
        if transaction.metadata is None:
            transaction.metadata = {}
        transaction.metadata["rejection_reason"] = reason
        
        await self._save_transaction(transaction)
        
        # Reverse balance changes
        if transaction.transaction_type == TransactionType.DEPOSIT:
            await self._reverse_pending_deposit(transaction)
        elif transaction.transaction_type == TransactionType.WITHDRAWAL:
            await self._reverse_locked_withdrawal(transaction)
        
        return True
    
    async def get_transaction(self, tx_id: str) -> Optional[TreasuryTransaction]:
        """Dapatkan detail transaksi"""
        key = f"{self.transaction_prefix}{tx_id}"
        data = await self.redis.get(key)
        
        if not data:
            return None
        
        tx_dict = json.loads(data)
        tx_dict['transaction_type'] = TransactionType(tx_dict['transaction_type'])
        tx_dict['status'] = TransactionStatus(tx_dict['status'])
        tx_dict['amount'] = Decimal(tx_dict['amount'])
        
        return TreasuryTransaction(**tx_dict)
    
    async def get_all_transactions(
        self,
        currency: Optional[str] = None,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TreasuryTransaction]:
        """Dapatkan semua transaksi dengan filter"""
        tx_keys = await self.redis.keys(f"{self.transaction_prefix}*")
        transactions = []
        
        for key in tx_keys[offset:offset + limit]:
            data = await self.redis.get(key)
            if data:
                tx_dict = json.loads(data)
                tx_dict['transaction_type'] = TransactionType(tx_dict['transaction_type'])
                tx_dict['status'] = TransactionStatus(tx_dict['status'])
                tx_dict['amount'] = Decimal(tx_dict['amount'])
                
                transaction = TreasuryTransaction(**tx_dict)
                
                # Apply filters
                if currency and transaction.currency != currency:
                    continue
                if transaction_type and transaction.transaction_type != transaction_type:
                    continue
                if status and transaction.status != status:
                    continue
                
                transactions.append(transaction)
        
        # Sort by timestamp (newest first)
        return sorted(transactions, key=lambda x: x.timestamp, reverse=True)
    
    async def get_balance(self, currency: str) -> TreasuryBalance:
        """Dapatkan saldo treasury untuk mata uang tertentu"""
        key = f"{self.balance_prefix}{currency}"
        data = await self.redis.get(key)
        
        if not data:
            return TreasuryBalance(
                currency=currency,
                available=Decimal("0"),
                locked=Decimal("0"),
                pending=Decimal("0"),
                total=Decimal("0")
            )
        
        balance_dict = json.loads(data)
        return TreasuryBalance(
            currency=currency,
            available=Decimal(balance_dict['available']),
            locked=Decimal(balance_dict['locked']),
            pending=Decimal(balance_dict['pending']),
            total=Decimal(balance_dict['total'])
        )
    
    async def get_available_balance(self, currency: str) -> Decimal:
        """Dapatkan saldo yang tersedia untuk withdrawal"""
        balance = await self.get_balance(currency)
        return balance.available
    
    async def get_total_balance(self, currency: str) -> Decimal:
        """Dapatkan total saldo (available + locked + pending)"""
        balance = await self.get_balance(currency)
        return balance.total
    
    async def get_treasury_stats(self) -> Dict:
        """Dapatkan statistik treasury"""
        # Get all currencies
        balance_keys = await self.redis.keys(f"{self.balance_prefix}*")
        currencies = [key.split(":")[-1] for key in balance_keys]
        
        stats = {
            "currencies": {},
            "total_transactions": 0,
            "pending_transactions": 0,
            "confirmed_transactions": 0,
            "total_deposits": Decimal("0"),
            "total_withdrawals": Decimal("0")
        }
        
        # Get balances for each currency
        for currency in currencies:
            balance = await self.get_balance(currency)
            stats["currencies"][currency] = {
                "available": str(balance.available),
                "locked": str(balance.locked),
                "pending": str(balance.pending),
                "total": str(balance.total)
            }
        
        # Get transaction stats
        tx_keys = await self.redis.keys(f"{self.transaction_prefix}*")
        stats["total_transactions"] = len(tx_keys)
        
        total_deposits = Decimal("0")
        total_withdrawals = Decimal("0")
        pending_count = 0
        confirmed_count = 0
        
        for key in tx_keys:
            data = await self.redis.get(key)
            if data:
                tx_dict = json.loads(data)
                amount = Decimal(tx_dict['amount'])
                status = TransactionStatus(tx_dict['status'])
                tx_type = TransactionType(tx_dict['transaction_type'])
                
                if status == TransactionStatus.PENDING:
                    pending_count += 1
                elif status == TransactionStatus.CONFIRMED:
                    confirmed_count += 1
                
                if tx_type == TransactionType.DEPOSIT and status == TransactionStatus.CONFIRMED:
                    total_deposits += amount
                elif tx_type == TransactionType.WITHDRAWAL and status == TransactionStatus.CONFIRMED:
                    total_withdrawals += amount
        
        stats["pending_transactions"] = pending_count
        stats["confirmed_transactions"] = confirmed_count
        stats["total_deposits"] = str(total_deposits)
        stats["total_withdrawals"] = str(total_withdrawals)
        
        return stats
    
    # Private methods
    
    async def _save_transaction(self, transaction: TreasuryTransaction):
        """Simpan transaksi ke Redis"""
        key = f"{self.transaction_prefix}{transaction.id}"
        tx_dict = asdict(transaction)
        tx_dict['transaction_type'] = transaction.transaction_type.value
        tx_dict['status'] = transaction.status.value
        tx_dict['amount'] = str(transaction.amount)
        
        await self.redis.set(key, json.dumps(tx_dict))
    
    async def _update_balance(self, currency: str, available: Decimal, locked: Decimal, pending: Decimal):
        """Update saldo di Redis"""
        key = f"{self.balance_prefix}{currency}"
        balance = TreasuryBalance(
            currency=currency,
            available=available,
            locked=locked,
            pending=pending,
            total=available + locked + pending
        )
        
        balance_dict = asdict(balance)
        balance_dict['available'] = str(balance.available)
        balance_dict['locked'] = str(balance.locked)
        balance_dict['pending'] = str(balance.pending)
        balance_dict['total'] = str(balance.total)
        
        await self.redis.set(key, json.dumps(balance_dict))
    
    async def _update_pending_balance(self, currency: str, amount: Decimal):
        """Update saldo pending untuk deposit"""
        current_balance = await self.get_balance(currency)
        new_pending = current_balance.pending + amount
        
        await self._update_balance(
            currency,
            current_balance.available,
            current_balance.locked,
            new_pending
        )
    
    async def _lock_balance(self, currency: str, amount: Decimal):
        """Lock saldo untuk withdrawal"""
        current_balance = await self.get_balance(currency)
        
        if current_balance.available < amount:
            raise ValueError("Insufficient available balance")
        
        new_available = current_balance.available - amount
        new_locked = current_balance.locked + amount
        
        await self._update_balance(
            currency,
            new_available,
            new_locked,
            current_balance.pending
        )
    
    async def _confirm_deposit(self, transaction: TreasuryTransaction):
        """Konfirmasi deposit dan update saldo"""
        current_balance = await self.get_balance(transaction.currency)
        
        # Kurangi pending, tambahkan ke available
        new_pending = current_balance.pending - transaction.amount
        new_available = current_balance.available + transaction.amount
        
        await self._update_balance(
            transaction.currency,
            new_available,
            current_balance.locked,
            new_pending
        )
    
    async def _confirm_withdrawal(self, transaction: TreasuryTransaction):
        """Konfirmasi withdrawal dan update saldo"""
        current_balance = await self.get_balance(transaction.currency)
        
        # Kurangi locked
        new_locked = current_balance.locked - transaction.amount
        
        await self._update_balance(
            transaction.currency,
            current_balance.available,
            new_locked,
            current_balance.pending
        )
    
    async def _reverse_pending_deposit(self, transaction: TreasuryTransaction):
        """Reverse pending deposit jika transaksi direject"""
        current_balance = await self.get_balance(transaction.currency)
        
        # Kurangi pending
        new_pending = current_balance.pending - transaction.amount
        
        await self._update_balance(
            transaction.currency,
            current_balance.available,
            current_balance.locked,
            new_pending
        )
    
    async def _reverse_locked_withdrawal(self, transaction: TreasuryTransaction):
        """Reverse locked withdrawal jika transaksi direject"""
        current_balance = await self.get_balance(transaction.currency)
        
        # Kembalikan ke available
        new_available = current_balance.available + transaction.amount
        new_locked = current_balance.locked - transaction.amount
        
        await self._update_balance(
            transaction.currency,
            new_available,
            new_locked,
            current_balance.pending
        )


class TreasuryAnalytics:
    """Analytics dan reporting untuk treasury"""
    
    def __init__(self, treasury: TreasuryManagement):
        self.treasury = treasury
    
    async def get_monthly_report(self, year: int, month: int) -> Dict:
        """Generate monthly treasury report"""
        # Get all transactions for the month
        all_transactions = await self.treasury.get_all_transactions()
        
        # Filter by month and year
        monthly_transactions = []
        total_deposits = Decimal("0")
        total_withdrawals = Decimal("0")
        
        for tx in all_transactions:
            tx_date = datetime.fromtimestamp(tx.timestamp)
            if tx_date.year == year and tx_date.month == month and tx.status == TransactionStatus.CONFIRMED:
                monthly_transactions.append(tx)
                
                if tx.transaction_type == TransactionType.DEPOSIT:
                    total_deposits += tx.amount
                elif tx.transaction_type == TransactionType.WITHDRAWAL:
                    total_withdrawals += tx.amount
        
        # Calculate net flow
        net_flow = total_deposits - total_withdrawals
        
        return {
            "year": year,
            "month": month,
            "total_transactions": len(monthly_transactions),
            "total_deposits": str(total_deposits),
            "total_withdrawals": str(total_withdrawals),
            "net_flow": str(net_flow),
            "transactions": [asdict(tx) for tx in monthly_transactions]
        }
    
    async def get_balance_history(self, currency: str, days: int = 30) -> List[Dict]:
        """Get balance history for specified number of days"""
        # This is a simplified implementation
        # In a real system, you'd store historical balance snapshots
        current_balance = await self.treasury.get_balance(currency)
        
        history = []
        current_time = int(time.time())
        
        for i in range(days):
            day_timestamp = current_time - (i * 24 * 3600)
            day_date = datetime.fromtimestamp(day_timestamp)
            
            history.append({
                "date": day_date.strftime("%Y-%m-%d"),
                "timestamp": day_timestamp,
                "available": str(current_balance.available),  # Simplified - same balance for all days
                "locked": str(current_balance.locked),
                "pending": str(current_balance.pending),
                "total": str(current_balance.total)
            })
        
        return list(reversed(history))
    
    async def get_risk_metrics(self) -> Dict:
        """Calculate risk metrics for treasury"""
        stats = await self.treasury.get_treasury_stats()
        
        # Calculate concentration risk (if all funds are in one currency)
        currencies = stats["currencies"]
        total_value = sum(Decimal(balance["total"]) for balance in currencies.values())
        
        concentration_risk = 0
        if total_value > 0:
            max_currency_percentage = max(
                Decimal(balance["total"]) / total_value * 100
                for balance in currencies.values()
            )
            concentration_risk = float(max_currency_percentage)
        
        # Calculate liquidity risk
        total_available = sum(Decimal(balance["available"]) for balance in currencies.values())
        liquidity_ratio = float(total_available / total_value * 100) if total_value > 0 else 0
        
        return {
            "total_value": str(total_value),
            "concentration_risk_percentage": concentration_risk,
            "liquidity_ratio_percentage": liquidity_ratio,
            "pending_transactions": stats["pending_transactions"],
            "emergency_threshold_breached": total_available < self.treasury.config.emergency_threshold
        }