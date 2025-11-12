"""
Test suite for Multi-Signature Wallet System
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from multi_sig_wallet import (
    MultiSigWalletManager, 
    MultiSigWallet,
    WalletOwner,
    Transaction,
    TransactionStatus,
    SignatureType,
    AuditLog
)


class TestMultiSigWalletManager:
    """Test cases for MultiSigWalletManager"""
    
    @pytest.fixture
    def wallet_manager(self):
        """Create a wallet manager instance"""
        return MultiSigWalletManager()
    
    @pytest.fixture
    def sample_owners(self):
        """Sample wallet owners"""
        return [
            {
                'address': '0x1234567890123456789012345678901234567890',
                'public_key': 'public_key_1_test',
                'signature_type': 'ecdsa',
                'weight': 1
            },
            {
                'address': '0x2345678901234567890123456789012345678901',
                'public_key': 'public_key_2_test',
                'signature_type': 'ecdsa',
                'weight': 1
            },
            {
                'address': '0x3456789012345678901234567890123456789012',
                'public_key': 'public_key_3_test',
                'signature_type': 'ecdsa',
                'weight': 1
            }
        ]
    
    @pytest.fixture
    def sample_wallet(self, wallet_manager, sample_owners):
        """Create a sample wallet"""
        # Use asyncio.run to handle the async call
        import asyncio
        return asyncio.run(wallet_manager.create_wallet(
            initial_owners=sample_owners,
            threshold=2,
            wallet_metadata={'name': 'Test Wallet'}
        ))
    
    @pytest.mark.asyncio
    async def test_create_wallet_success(self, wallet_manager, sample_owners):
        """Test successful wallet creation"""
        wallet = await wallet_manager.create_wallet(
            initial_owners=sample_owners,
            threshold=2
        )
        
        assert wallet is not None
        assert len(wallet.owners) == 3
        assert wallet.threshold == 2
        assert wallet.total_weight == 3
        assert wallet.wallet_address is not None
        assert len(wallet.wallet_address) == 42
    
    @pytest.mark.asyncio
    async def test_create_wallet_invalid_threshold(self, wallet_manager, sample_owners):
        """Test wallet creation with invalid threshold"""
        with pytest.raises(ValueError, match="Threshold must be at least 1"):
            await wallet_manager.create_wallet(sample_owners, threshold=0)
        
        with pytest.raises(ValueError, match="Number of owners must be >= threshold"):
            await wallet_manager.create_wallet(sample_owners, threshold=4)
    
    @pytest.mark.asyncio
    async def test_create_transaction_success(self, wallet_manager, sample_wallet):
        """Test successful transaction creation"""
        transaction = await wallet_manager.create_transaction(
            wallet_address=sample_wallet.wallet_address,
            to_address='0x4567890123456789012345678901234567890123',
            amount=1.5,
            data={'purpose': 'Test transaction'}
        )
        
        assert transaction is not None
        assert transaction.transaction_id is not None
        assert transaction.from_address == sample_wallet.wallet_address
        assert transaction.to_address == '0x4567890123456789012345678901234567890123'
        assert transaction.amount == 1.5
        assert transaction.status == TransactionStatus.PENDING
        assert transaction.required_signatures == 2
        assert transaction.current_signatures == 0
    
    @pytest.mark.asyncio
    async def test_create_transaction_wallet_not_found(self, wallet_manager):
        """Test transaction creation with non-existent wallet"""
        with pytest.raises(ValueError, match="Wallet not found"):
            await wallet_manager.create_transaction(
                wallet_address='0x0000000000000000000000000000000000000000',
                to_address='0x4567890123456789012345678901234567890123',
                amount=1.0
            )
    
    @pytest.mark.asyncio
    async def test_sign_transaction_success(self, wallet_manager, sample_wallet):
        """Test successful transaction signing"""
        # Create transaction
        transaction = await wallet_manager.create_transaction(
            wallet_address=sample_wallet.wallet_address,
            to_address='0x4567890123456789012345678901234567890123',
            amount=1.0
        )
        
        # Sign transaction
        result = await wallet_manager.sign_transaction(
            wallet_address=sample_wallet.wallet_address,
            transaction_id=transaction.transaction_id,
            signer_address='0x1234567890123456789012345678901234567890',
            signature_data='test_signature_1'
        )
        
        assert result is True
        
        # Verify transaction was updated
        updated_transaction = sample_wallet.transactions[transaction.transaction_id]
        assert updated_transaction.current_signatures == 1
        assert '0x1234567890123456789012345678901234567890' in updated_transaction.signers
        assert len(updated_transaction.signatures) == 1
    
    @pytest.mark.asyncio
    async def test_sign_transaction_non_owner(self, wallet_manager, sample_wallet):
        """Test signing transaction by non-owner"""
        transaction = await wallet_manager.create_transaction(
            wallet_address=sample_wallet.wallet_address,
            to_address='0x4567890123456789012345678901234567890123',
            amount=1.0
        )
        
        with pytest.raises(ValueError, match="Signer cannot sign this transaction"):
            await wallet_manager.sign_transaction(
                wallet_address=sample_wallet.wallet_address,
                transaction_id=transaction.transaction_id,
                signer_address='0x9999999999999999999999999999999999999999',
                signature_data='invalid_signature'
            )
    
    @pytest.mark.asyncio
    async def test_transaction_auto_approval(self, wallet_manager, sample_wallet):
        """Test transaction auto-approval after reaching threshold"""
        transaction = await wallet_manager.create_transaction(
            wallet_address=sample_wallet.wallet_address,
            to_address='0x4567890123456789012345678901234567890123',
            amount=1.0
        )
        
        # First signature
        await wallet_manager.sign_transaction(
            wallet_address=sample_wallet.wallet_address,
            transaction_id=transaction.transaction_id,
            signer_address='0x1234567890123456789012345678901234567890',
            signature_data='test_signature_1'
        )
        
        assert transaction.current_signatures == 1
        assert transaction.status == TransactionStatus.PENDING
        
        # Second signature - should approve
        await wallet_manager.sign_transaction(
            wallet_address=sample_wallet.wallet_address,
            transaction_id=transaction.transaction_id,
            signer_address='0x2345678901234567890123456789012345678901',
            signature_data='test_signature_2'
        )
        
        assert transaction.current_signatures == 2
        assert transaction.status == TransactionStatus.APPROVED
    
    @pytest.mark.asyncio
    async def test_execute_transaction_success(self, wallet_manager, sample_wallet):
        """Test successful transaction execution"""
        transaction = await wallet_manager.create_transaction(
            wallet_address=sample_wallet.wallet_address,
            to_address='0x4567890123456789012345678901234567890123',
            amount=1.0
        )
        
        # Approve transaction
        await wallet_manager.sign_transaction(
            wallet_address=sample_wallet.wallet_address,
            transaction_id=transaction.transaction_id,
            signer_address='0x1234567890123456789012345678901234567890',
            signature_data='test_signature_1'
        )
        await wallet_manager.sign_transaction(
            wallet_address=sample_wallet.wallet_address,
            transaction_id=transaction.transaction_id,
            signer_address='0x2345678901234567890123456789012345678901',
            signature_data='test_signature_2'
        )
        
        # Execute transaction
        result = await wallet_manager.execute_transaction(
            wallet_address=sample_wallet.wallet_address,
            transaction_id=transaction.transaction_id
        )
        
        assert result is True
        assert transaction.status == TransactionStatus.EXECUTED
        assert transaction.executed_at is not None
    
    @pytest.mark.asyncio
    async def test_execute_transaction_not_approved(self, wallet_manager, sample_wallet):
        """Test executing non-approved transaction"""
        transaction = await wallet_manager.create_transaction(
            wallet_address=sample_wallet.wallet_address,
            to_address='0x4567890123456789012345678901234567890123',
            amount=1.0
        )
        
        with pytest.raises(ValueError, match="Transaction is not approved"):
            await wallet_manager.execute_transaction(
                wallet_address=sample_wallet.wallet_address,
                transaction_id=transaction.transaction_id
            )
    
    @pytest.mark.asyncio
    async def test_reject_transaction_success(self, wallet_manager, sample_wallet):
        """Test successful transaction rejection"""
        transaction = await wallet_manager.create_transaction(
            wallet_address=sample_wallet.wallet_address,
            to_address='0x4567890123456789012345678901234567890123',
            amount=1.0
        )
        
        # Reject transaction
        result = await wallet_manager.reject_transaction(
            wallet_address=sample_wallet.wallet_address,
            transaction_id=transaction.transaction_id,
            rejector_address='0x1234567890123456789012345678901234567890',
            reason="Suspicious transaction"
        )
        
        assert result is True
        assert transaction.rejection_count == 1
        assert "Suspicious transaction" in transaction.rejection_reasons
    
    @pytest.mark.asyncio
    async def test_wallet_status_report(self, wallet_manager, sample_wallet):
        """Test wallet status reporting"""
        # Create and approve a transaction
        transaction = await wallet_manager.create_transaction(
            wallet_address=sample_wallet.wallet_address,
            to_address='0x4567890123456789012345678901234567890123',
            amount=1.0
        )
        
        await wallet_manager.sign_transaction(
            wallet_address=sample_wallet.wallet_address,
            transaction_id=transaction.transaction_id,
            signer_address='0x1234567890123456789012345678901234567890',
            signature_data='test_signature_1'
        )
        
        # Get status
        status = await wallet_manager.get_wallet_status(sample_wallet.wallet_address)
        
        assert status['wallet_address'] == sample_wallet.wallet_address
        assert status['owner_count'] == 3
        assert status['threshold'] == 2
        assert status['total_weight'] == 3
        assert status['transaction_stats']['total'] == 1
        assert status['transaction_stats']['pending'] == 1
        assert status['transaction_stats']['executed'] == 0
        assert len(status['owner_activity']) == 3
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_transactions(self, wallet_manager, sample_wallet):
        """Test cleanup of expired transactions"""
        # Create transaction with expired date
        transaction = Transaction(
            transaction_id='test_expired_tx',
            from_address=sample_wallet.wallet_address,
            to_address='0x4567890123456789012345678901234567890123',
            amount=1.0,
            status=TransactionStatus.PENDING,
            expires_at=datetime.now() - timedelta(hours=1)  # Expired
        )
        
        sample_wallet.transactions['test_expired_tx'] = transaction
        
        # Run cleanup
        cleaned_count = await wallet_manager.cleanup_expired_transactions()
        
        assert cleaned_count >= 1
        assert transaction.status == TransactionStatus.EXPIRED
    
    @pytest.mark.asyncio
    async def test_audit_logs_creation(self, wallet_manager, sample_wallet):
        """Test audit log creation"""
        # Create a transaction to generate logs
        await wallet_manager.create_transaction(
            wallet_address=sample_wallet.wallet_address,
            to_address='0x4567890123456789012345678901234567890123',
            amount=1.0
        )
        
        # Get audit logs
        logs = await wallet_manager.get_audit_logs(sample_wallet.wallet_address)
        
        assert len(logs) > 0
        assert all(isinstance(log, AuditLog) for log in logs)
        assert any(log.action == "TRANSACTION_CREATED" for log in logs)
        assert any(log.wallet_address == sample_wallet.wallet_address for log in logs)
    
    @pytest.mark.asyncio
    async def test_wallet_with_weighted_owners(self, wallet_manager):
        """Test wallet with weighted owners"""
        weighted_owners = [
            {
                'address': '0x1234567890123456789012345678901234567890',
                'public_key': 'public_key_1',
                'signature_type': 'ecdsa',
                'weight': 2  # Higher weight
            },
            {
                'address': '0x2345678901234567890123456789012345678901',
                'public_key': 'public_key_2',
                'signature_type': 'ecdsa',
                'weight': 1
            }
        ]
        
        wallet = await wallet_manager.create_wallet(weighted_owners, threshold=2)
        
        assert wallet.total_weight == 3
        assert wallet.owners['0x1234567890123456789012345678901234567890'].weight == 2
        assert wallet.owners['0x2345678901234567890123456789012345678901'].weight == 1
        
        # Create transaction
        transaction = await wallet_manager.create_transaction(
            wallet_address=wallet.wallet_address,
            to_address='0x4567890123456789012345678901234567890123',
            amount=1.0,
            required_signatures=2
        )
        
        # Sign with weighted owner (weight=2) - should be enough
        await wallet_manager.sign_transaction(
            wallet_address=wallet.wallet_address,
            transaction_id=transaction.transaction_id,
            signer_address='0x1234567890123456789012345678901234567890',
            signature_data='weighted_signature'
        )
        
        assert transaction.current_signatures == 2
        assert transaction.status == TransactionStatus.APPROVED
    
    @pytest.mark.asyncio
    async def test_transaction_serialization(self, wallet_manager, sample_wallet):
        """Test transaction serialization"""
        transaction = await wallet_manager.create_transaction(
            wallet_address=sample_wallet.wallet_address,
            to_address='0x4567890123456789012345678901234567890123',
            amount=1.0,
            data={'test': 'data'}
        )
        
        # Convert to dict
        tx_dict = transaction.to_dict()
        
        assert tx_dict['transaction_id'] == transaction.transaction_id
        assert tx_dict['from_address'] == sample_wallet.wallet_address
        assert tx_dict['to_address'] == '0x4567890123456789012345678901234567890123'
        assert tx_dict['amount'] == 1.0
        assert tx_dict['data'] == {'test': 'data'}
        assert tx_dict['status'] == 'pending'
        assert tx_dict['required_signatures'] == 2
        assert tx_dict['current_signatures'] == 0
        
        # Test JSON serialization
        json_str = json.dumps(tx_dict)
        assert isinstance(json_str, str)
        
        # Test deserialization
        deserialized = json.loads(json_str)
        assert deserialized['transaction_id'] == transaction.transaction_id
    
    @pytest.mark.asyncio
    async def test_signature_verification(self, wallet_manager, sample_wallet):
        """Test signature verification logic"""
        transaction = await wallet_manager.create_transaction(
            wallet_address=sample_wallet.wallet_address,
            to_address='0x4567890123456789012345678901234567890123',
            amount=1.0
        )
        
        # Test with different signature types
        for sig_type in [SignatureType.ECDSA, SignatureType.ED25519, SignatureType.RSA]:
            result = await wallet_manager.sign_transaction(
                wallet_address=sample_wallet.wallet_address,
                transaction_id=transaction.transaction_id,
                signer_address='0x1234567890123456789012345678901234567890',
                signature_data=f'test_signature_{sig_type.value}',
                signature_type=sig_type
            )
            assert result is True
    
    @pytest.mark.asyncio
    async def test_concurrent_transaction_signing(self, wallet_manager, sample_wallet):
        """Test concurrent signing of transactions"""
        transaction = await wallet_manager.create_transaction(
            wallet_address=sample_wallet.wallet_address,
            to_address='0x4567890123456789012345678901234567890123',
            amount=1.0
        )
        
        # Attempt concurrent signing (should handle gracefully)
        tasks = []
        for i, owner in enumerate(['0x1234567890123456789012345678901234567890', 
                                   '0x2345678901234567890123456789012345678901']):
            task = wallet_manager.sign_transaction(
                wallet_address=sample_wallet.wallet_address,
                transaction_id=transaction.transaction_id,
                signer_address=owner,
                signature_data=f'concurrent_sig_{i}'
            )
            tasks.append(task)
        
        # Execute concurrently
        results = await asyncio.gather(*tasks)
        
        assert all(results)
        assert transaction.current_signatures == 2
        assert transaction.status == TransactionStatus.APPROVED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])