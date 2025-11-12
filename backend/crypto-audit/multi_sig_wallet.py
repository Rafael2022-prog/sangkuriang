"""
Multi-Signature Wallet System for SANGKURIANG
Provides secure transaction approval with multiple signatures
"""

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from enum import Enum
from datetime import datetime, timedelta
import hmac


class TransactionStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    EXECUTED = "executed"


class SignatureType(Enum):
    ECDSA = "ecdsa"
    ED25519 = "ed25519"
    RSA = "rsa"


@dataclass
class WalletOwner:
    """Represents a wallet owner with their signing capabilities"""
    address: str
    public_key: str
    signature_type: SignatureType
    weight: int = 1  # Voting weight
    metadata: Dict[str, Any] = field(default_factory=dict)
    added_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)


@dataclass
class Transaction:
    """Represents a multi-signature transaction"""
    transaction_id: str
    from_address: str
    to_address: str
    amount: float
    data: Optional[Dict[str, Any]] = None
    status: TransactionStatus = TransactionStatus.PENDING
    required_signatures: int = 2
    current_signatures: int = 0
    signatures: List[Dict[str, Any]] = field(default_factory=list)
    signers: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))
    executed_at: Optional[datetime] = None
    rejection_count: int = 0
    rejection_reasons: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary"""
        return {
            'transaction_id': self.transaction_id,
            'from_address': self.from_address,
            'to_address': self.to_address,
            'amount': self.amount,
            'data': self.data,
            'status': self.status.value,
            'required_signatures': self.required_signatures,
            'current_signatures': self.current_signatures,
            'signatures': self.signatures,
            'signers': list(self.signers),
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'rejection_count': self.rejection_count,
            'rejection_reasons': self.rejection_reasons,
            'metadata': self.metadata
        }


@dataclass
class MultiSigWallet:
    """Represents a multi-signature wallet"""
    wallet_address: str
    owners: Dict[str, WalletOwner]
    threshold: int  # Minimum signatures required
    total_weight: int
    transactions: Dict[str, Transaction] = field(default_factory=dict)
    transaction_history: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_active_transactions(self) -> List[Transaction]:
        """Get all active (pending) transactions"""
        return [tx for tx in self.transactions.values() 
                if tx.status in [TransactionStatus.PENDING, TransactionStatus.APPROVED]]
    
    def get_owner_weight(self, address: str) -> int:
        """Get voting weight for an owner"""
        owner = self.owners.get(address)
        return owner.weight if owner else 0
    
    def can_sign_transaction(self, address: str, transaction: Transaction) -> bool:
        """Check if owner can sign a transaction"""
        if address not in self.owners:
            return False
        if address in transaction.signers:
            return False  # Already signed
        if transaction.status != TransactionStatus.PENDING:
            return False
        if datetime.now() > transaction.expires_at:
            return False
        return True


@dataclass
class SignatureRequest:
    """Request for transaction signature"""
    transaction_id: str
    wallet_address: str
    signer_address: str
    signature_data: str
    signature_type: SignatureType
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditLog:
    """Audit log entry for wallet activities"""
    log_id: str
    wallet_address: str
    action: str
    actor: str
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True


class MultiSigWalletManager:
    """Manages multiple multi-signature wallets"""
    
    def __init__(self):
        self.wallets: Dict[str, MultiSigWallet] = {}
        self.audit_logs: List[AuditLog] = []
        self.signature_verifiers = {
            SignatureType.ECDSA: self._verify_ecdsa_signature,
            SignatureType.ED25519: self._verify_ed25519_signature,
            SignatureType.RSA: self._verify_rsa_signature
        }
        
    async def create_wallet(
        self,
        initial_owners: List[Dict[str, Any]],
        threshold: int,
        wallet_metadata: Optional[Dict[str, Any]] = None
    ) -> MultiSigWallet:
        """Create a new multi-signature wallet"""
        
        # Validate inputs
        if threshold < 1:
            raise ValueError("Threshold must be at least 1")
        if len(initial_owners) < threshold:
            raise ValueError("Number of owners must be >= threshold")
        
        # Generate wallet address
        wallet_data = json.dumps({
            'owners': initial_owners,
            'threshold': threshold,
            'timestamp': time.time()
        }, sort_keys=True)
        wallet_address = hashlib.sha256(wallet_data.encode()).hexdigest()[:42]
        
        # Create owners
        owners = {}
        total_weight = 0
        
        for owner_data in initial_owners:
            owner = WalletOwner(
                address=owner_data['address'],
                public_key=owner_data['public_key'],
                signature_type=SignatureType(owner_data.get('signature_type', 'ecdsa')),
                weight=owner_data.get('weight', 1),
                metadata=owner_data.get('metadata', {})
            )
            owners[owner.address] = owner
            total_weight += owner.weight
        
        # Validate threshold against total weight
        if threshold > total_weight:
            raise ValueError("Threshold cannot exceed total owner weight")
        
        # Create wallet
        wallet = MultiSigWallet(
            wallet_address=wallet_address,
            owners=owners,
            threshold=threshold,
            total_weight=total_weight,
            metadata=wallet_metadata or {}
        )
        
        self.wallets[wallet_address] = wallet
        
        # Log creation
        await self._log_activity(
            wallet_address=wallet_address,
            action="WALLET_CREATED",
            actor="system",
            details={
                'threshold': threshold,
                'owner_count': len(initial_owners),
                'total_weight': total_weight
            }
        )
        
        return wallet
    
    async def create_transaction(
        self,
        wallet_address: str,
        to_address: str,
        amount: float,
        data: Optional[Dict[str, Any]] = None,
        required_signatures: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Transaction:
        """Create a new transaction"""
        
        wallet = self.wallets.get(wallet_address)
        if not wallet:
            raise ValueError("Wallet not found")
        
        # Generate transaction ID
        tx_data = json.dumps({
            'wallet_address': wallet_address,
            'to_address': to_address,
            'amount': amount,
            'timestamp': time.time()
        }, sort_keys=True)
        transaction_id = hashlib.sha256(tx_data.encode()).hexdigest()[:64]
        
        # Use wallet threshold if required_signatures not specified
        if required_signatures is None:
            required_signatures = wallet.threshold
        
        transaction = Transaction(
            transaction_id=transaction_id,
            from_address=wallet_address,
            to_address=to_address,
            amount=amount,
            data=data,
            required_signatures=required_signatures,
            metadata=metadata or {}
        )
        
        wallet.transactions[transaction_id] = transaction
        wallet.transaction_history.append(transaction_id)
        
        # Log transaction creation
        await self._log_activity(
            wallet_address=wallet_address,
            action="TRANSACTION_CREATED",
            actor="system",
            details={
                'transaction_id': transaction_id,
                'to_address': to_address,
                'amount': amount,
                'required_signatures': required_signatures
            }
        )
        
        return transaction
    
    async def sign_transaction(
        self,
        wallet_address: str,
        transaction_id: str,
        signer_address: str,
        signature_data: str,
        signature_type: SignatureType = SignatureType.ECDSA
    ) -> bool:
        """Sign a transaction"""
        
        wallet = self.wallets.get(wallet_address)
        if not wallet:
            raise ValueError("Wallet not found")
        
        transaction = wallet.transactions.get(transaction_id)
        if not transaction:
            raise ValueError("Transaction not found")
        
        # Validate signer
        if not wallet.can_sign_transaction(signer_address, transaction):
            raise ValueError("Signer cannot sign this transaction")
        
        # Verify signature (simplified - in production, use proper crypto verification)
        is_valid = await self._verify_signature(
            wallet_address=wallet_address,
            transaction_id=transaction_id,
            signer_address=signer_address,
            signature_data=signature_data,
            signature_type=signature_type
        )
        
        if not is_valid:
            raise ValueError("Invalid signature")
        
        # Add signature
        transaction.signatures.append({
            'signer_address': signer_address,
            'signature_data': signature_data,
            'signature_type': signature_type.value,
            'timestamp': datetime.now().isoformat()
        })
        transaction.signers.add(signer_address)
        transaction.current_signatures += wallet.get_owner_weight(signer_address)
        
        # Update owner activity
        wallet.owners[signer_address].last_activity = datetime.now()
        
        # Check if transaction is approved
        if transaction.current_signatures >= transaction.required_signatures:
            transaction.status = TransactionStatus.APPROVED
            
            # Auto-execute if configured
            if wallet.metadata.get('auto_execute', False):
                await self.execute_transaction(wallet_address, transaction_id)
        
        # Log signing
        await self._log_activity(
            wallet_address=wallet_address,
            action="TRANSACTION_SIGNED",
            actor=signer_address,
            details={
                'transaction_id': transaction_id,
                'signature_weight': wallet.get_owner_weight(signer_address),
                'current_signatures': transaction.current_signatures,
                'required_signatures': transaction.required_signatures
            }
        )
        
        return True
    
    async def reject_transaction(
        self,
        wallet_address: str,
        transaction_id: str,
        rejector_address: str,
        reason: str = ""
    ) -> bool:
        """Reject a transaction"""
        
        wallet = self.wallets.get(wallet_address)
        if not wallet:
            raise ValueError("Wallet not found")
        
        transaction = wallet.transactions.get(transaction_id)
        if not transaction:
            raise ValueError("Transaction not found")
        
        if transaction.status != TransactionStatus.PENDING:
            raise ValueError("Transaction is not pending")
        
        if rejector_address not in wallet.owners:
            raise ValueError("Rejector is not a wallet owner")
        
        transaction.rejection_count += 1
        if reason:
            transaction.rejection_reasons.append(reason)
        
        # If majority rejects, mark as rejected
        if transaction.rejection_count > len(wallet.owners) // 2:
            transaction.status = TransactionStatus.REJECTED
        
        # Log rejection
        await self._log_activity(
            wallet_address=wallet_address,
            action="TRANSACTION_REJECTED",
            actor=rejector_address,
            details={
                'transaction_id': transaction_id,
                'reason': reason,
                'rejection_count': transaction.rejection_count
            }
        )
        
        return True
    
    async def execute_transaction(
        self,
        wallet_address: str,
        transaction_id: str
    ) -> bool:
        """Execute an approved transaction"""
        
        wallet = self.wallets.get(wallet_address)
        if not wallet:
            raise ValueError("Wallet not found")
        
        transaction = wallet.transactions.get(transaction_id)
        if not transaction:
            raise ValueError("Transaction not found")
        
        if transaction.status != TransactionStatus.APPROVED:
            raise ValueError("Transaction is not approved")
        
        # In a real implementation, this would interact with blockchain
        # For now, we'll simulate execution
        transaction.status = TransactionStatus.EXECUTED
        transaction.executed_at = datetime.now()
        
        # Log execution
        await self._log_activity(
            wallet_address=wallet_address,
            action="TRANSACTION_EXECUTED",
            actor="system",
            details={
                'transaction_id': transaction_id,
                'amount': transaction.amount,
                'to_address': transaction.to_address
            }
        )
        
        return True
    
    async def get_wallet_status(self, wallet_address: str) -> Dict[str, Any]:
        """Get comprehensive wallet status"""
        
        wallet = self.wallets.get(wallet_address)
        if not wallet:
            raise ValueError("Wallet not found")
        
        active_transactions = wallet.get_active_transactions()
        pending_count = len([tx for tx in active_transactions if tx.status == TransactionStatus.PENDING])
        approved_count = len([tx for tx in active_transactions if tx.status == TransactionStatus.APPROVED])
        
        return {
            'wallet_address': wallet_address,
            'owner_count': len(wallet.owners),
            'threshold': wallet.threshold,
            'total_weight': wallet.total_weight,
            'created_at': wallet.created_at.isoformat(),
            'transaction_stats': {
                'total': len(wallet.transaction_history),
                'pending': pending_count,
                'approved': approved_count,
                'executed': len([tx for tx in wallet.transactions.values() if tx.status == TransactionStatus.EXECUTED])
            },
            'owner_activity': {
                addr: {
                    'weight': owner.weight,
                    'last_activity': owner.last_activity.isoformat(),
                    'signature_type': owner.signature_type.value
                }
                for addr, owner in wallet.owners.items()
            }
        }
    
    async def cleanup_expired_transactions(self) -> int:
        """Clean up expired transactions"""
        
        cleaned_count = 0
        current_time = datetime.now()
        
        for wallet in self.wallets.values():
            for transaction in wallet.transactions.values():
                if (transaction.status == TransactionStatus.PENDING and 
                    current_time > transaction.expires_at):
                    transaction.status = TransactionStatus.EXPIRED
                    cleaned_count += 1
        
        return cleaned_count
    
    async def get_audit_logs(
        self,
        wallet_address: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs with optional filtering"""
        
        logs = self.audit_logs
        
        if wallet_address:
            logs = [log for log in logs if log.wallet_address == wallet_address]
        
        # Sort by timestamp (newest first)
        logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        return logs[:limit]
    
    async def _verify_signature(
        self,
        wallet_address: str,
        transaction_id: str,
        signer_address: str,
        signature_data: str,
        signature_type: SignatureType
    ) -> bool:
        """Verify transaction signature"""
        
        # In a real implementation, this would use proper cryptographic verification
        # For demonstration, we'll use a simple HMAC-based verification
        
        wallet = self.wallets.get(wallet_address)
        if not wallet:
            return False
        
        owner = wallet.owners.get(signer_address)
        if not owner:
            return False
        
        verifier = self.signature_verifiers.get(signature_type)
        if not verifier:
            return False
        
        return verifier(transaction_id, signature_data, owner.public_key)
    
    def _verify_ecdsa_signature(
        self,
        transaction_id: str,
        signature_data: str,
        public_key: str
    ) -> bool:
        """Verify ECDSA signature (simplified)"""
        # In production, use proper ECDSA verification
        expected_signature = hmac.new(
            public_key.encode(),
            transaction_id.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # For demo purposes, accept if signature starts with expected pattern
        return signature_data.startswith(expected_signature[:16])
    
    def _verify_ed25519_signature(
        self,
        transaction_id: str,
        signature_data: str,
        public_key: str
    ) -> bool:
        """Verify Ed25519 signature (simplified)"""
        # Similar simplified verification
        expected_signature = hmac.new(
            public_key.encode(),
            transaction_id.encode(),
            hashlib.sha512
        ).hexdigest()
        
        return signature_data.startswith(expected_signature[:16])
    
    def _verify_rsa_signature(
        self,
        transaction_id: str,
        signature_data: str,
        public_key: str
    ) -> bool:
        """Verify RSA signature (simplified)"""
        # Similar simplified verification
        expected_signature = hmac.new(
            public_key.encode(),
            transaction_id.encode(),
            hashlib.sha1
        ).hexdigest()
        
        return signature_data.startswith(expected_signature[:16])
    
    async def _log_activity(
        self,
        wallet_address: str,
        action: str,
        actor: str,
        details: Dict[str, Any],
        success: bool = True
    ) -> None:
        """Log wallet activity"""
        
        log_entry = AuditLog(
            log_id=hashlib.sha256(f"{wallet_address}{action}{time.time()}".encode()).hexdigest()[:32],
            wallet_address=wallet_address,
            action=action,
            actor=actor,
            details=details,
            success=success
        )
        
        self.audit_logs.append(log_entry)


# Example usage and testing
if __name__ == "__main__":
    async def demo():
        manager = MultiSigWalletManager()
        
        # Create wallet with 3 owners, threshold of 2
        owners = [
            {
                'address': '0x1234567890123456789012345678901234567890',
                'public_key': 'public_key_1',
                'signature_type': 'ecdsa',
                'weight': 1
            },
            {
                'address': '0x2345678901234567890123456789012345678901',
                'public_key': 'public_key_2',
                'signature_type': 'ecdsa',
                'weight': 1
            },
            {
                'address': '0x3456789012345678901234567890123456789012',
                'public_key': 'public_key_3',
                'signature_type': 'ecdsa',
                'weight': 1
            }
        ]
        
        wallet = await manager.create_wallet(owners, threshold=2)
        print(f"Created wallet: {wallet.wallet_address}")
        
        # Create transaction
        transaction = await manager.create_transaction(
            wallet_address=wallet.wallet_address,
            to_address='0x4567890123456789012345678901234567890123',
            amount=1.5,
            data={'purpose': 'Project funding'}
        )
        print(f"Created transaction: {transaction.transaction_id}")
        
        # Sign transaction (first signature)
        await manager.sign_transaction(
            wallet_address=wallet.wallet_address,
            transaction_id=transaction.transaction_id,
            signer_address='0x1234567890123456789012345678901234567890',
            signature_data='signature_data_1'
        )
        print("First signature added")
        
        # Sign transaction (second signature - should approve)
        await manager.sign_transaction(
            wallet_address=wallet.wallet_address,
            transaction_id=transaction.transaction_id,
            signer_address='0x2345678901234567890123456789012345678901',
            signature_data='signature_data_2'
        )
        print("Second signature added - transaction approved")
        
        # Execute transaction
        await manager.execute_transaction(wallet.wallet_address, transaction.transaction_id)
        print("Transaction executed")
        
        # Get wallet status
        status = await manager.get_wallet_status(wallet.wallet_address)
        print(f"Wallet status: {json.dumps(status, indent=2)}")
        
        # Get audit logs
        logs = await manager.get_audit_logs(wallet.wallet_address)
        print(f"Audit logs: {len(logs)} entries")
    
    asyncio.run(demo())