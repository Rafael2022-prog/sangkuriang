import pytest
import asyncio
import json
from datetime import datetime, timedelta
from multi_sig_wallet import MultiSigWalletManager, SignatureType


class TestMultiSigWalletManager:
    """Test suite for MultiSigWalletManager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.wallet_manager = MultiSigWalletManager()
        self.sample_owners = [
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
    
    @pytest.mark.asyncio
    async def test_create_wallet_success(self):
        """Test successful wallet creation"""
        wallet = await self.wallet_manager.create_wallet(
            initial_owners=self.sample_owners,
            threshold=2,
            wallet_metadata={'name': 'Test Wallet'}
        )
        
        assert wallet.wallet_address is not None
        assert wallet.threshold == 2
        assert len(wallet.owners) == 3
        assert wallet.metadata['name'] == 'Test Wallet'
    
    @pytest.mark.asyncio
    async def test_create_wallet_invalid_threshold(self):
        """Test wallet creation with invalid threshold"""
        with pytest.raises(ValueError, match="Threshold cannot exceed number of owners"):
            await self.wallet_manager.create_wallet(
                initial_owners=self.sample_owners,
                threshold=5,  # More than number of owners
                wallet_metadata={'name': 'Invalid Wallet'}
            )
    
    @pytest.mark.asyncio
    async def test_create_transaction_success(self):
        """Test successful transaction creation"""
        wallet = await self.wallet_manager.create_wallet(
            initial_owners=self.sample_owners,
            threshold=2,
            wallet_metadata={'name': 'Test Wallet'}
        )
        
        transaction = await self.wallet_manager.create_transaction(
            wallet_address=wallet.wallet_address,
            to_address='0x9876543210987654321098765432109876543210',
            amount=1000,
            metadata={'purpose': 'Test transfer'}
        )
        
        assert transaction.transaction_id is not None
        assert transaction.destination == '0x9876543210987654321098765432109876543210'
        assert transaction.amount == 1000
        assert transaction.status.value == 'pending'
        assert len(transaction.signatures) == 0
    
    @pytest.mark.asyncio
    async def test_sign_transaction_success(self):
        """Test successful transaction signing"""
        wallet = await self.wallet_manager.create_wallet(
            initial_owners=self.sample_owners,
            threshold=2,
            wallet_metadata={'name': 'Test Wallet'}
        )
        
        transaction = await self.wallet_manager.create_transaction(
            wallet_id=wallet.wallet_id,
            destination='0x9876543210987654321098765432109876543210',
            amount=1000,
            transaction_metadata={'purpose': 'Test transfer'}
        )
        
        # Sign with first owner
        result1 = await self.wallet_manager.sign_transaction(
            wallet_address=wallet.wallet_address,
            transaction_id=transaction.transaction_id,
            signer_address=self.sample_owners[0]['address'],
            signature_data='signature_1_test'
        )
        
        assert result1 is True
        
        # Check transaction status after first signature
        wallet_status = await self.wallet_manager.get_wallet_status(wallet.wallet_address)
        transaction_status = next(t for t in wallet_status['pending_transactions'] if t['transaction_id'] == transaction.transaction_id)
        assert len(transaction_status['signatures']) == 1
        assert transaction_status['approval_percentage'] == 50.0
        
        # Sign with second owner (should reach threshold)
        result2 = await self.wallet_manager.sign_transaction(
            wallet_address=wallet.wallet_address,
            transaction_id=transaction.transaction_id,
            signer_address=self.sample_owners[1]['address'],
            signature_data='signature_2_test'
        )
        
        assert result2 is True
        
        # Check transaction status after second signature
        wallet_status = await self.wallet_manager.get_wallet_status(wallet.wallet_address)
        transaction_status = next(t for t in wallet_status['approved_transactions'] if t['transaction_id'] == transaction.transaction_id)
        assert len(transaction_status['signatures']) == 2
        assert transaction_status['approval_percentage'] == 100.0
    
    @pytest.mark.asyncio
    async def test_execute_transaction_success(self):
        """Test successful transaction execution"""
        wallet = await self.wallet_manager.create_wallet(
            initial_owners=self.sample_owners,
            threshold=2,
            wallet_metadata={'name': 'Test Wallet'}
        )
        
        transaction = await self.wallet_manager.create_transaction(
            wallet_id=wallet.wallet_id,
            destination='0x9876543210987654321098765432109876543210',
            amount=1000,
            transaction_metadata={'purpose': 'Test transfer'}
        )
        
        # Sign with two owners to reach threshold
        await self.wallet_manager.sign_transaction(
            wallet_address=wallet.wallet_address,
            transaction_id=transaction.transaction_id,
            signer_address=self.sample_owners[0]['address'],
            signature_data='signature_1_test'
        )
        
        await self.wallet_manager.sign_transaction(
            wallet_address=wallet.wallet_address,
            transaction_id=transaction.transaction_id,
            signer_address=self.sample_owners[1]['address'],
            signature_data='signature_2_test'
        )
        
        # Execute the transaction
        result = await self.wallet_manager.execute_transaction(
            wallet_address=wallet.wallet_address,
            transaction_id=transaction.transaction_id,
            executor_address=self.sample_owners[0]['address']
        )
        
        assert result is True
        
        # Check transaction status
        wallet_status = await self.wallet_manager.get_wallet_status(wallet.wallet_id)
        assert len(wallet_status['executed_transactions']) == 1
        assert wallet_status['executed_transactions'][0]['status'] == 'executed'
    
    @pytest.mark.asyncio
    async def test_transaction_serialization(self):
        """Test transaction serialization and deserialization"""
        wallet = await self.wallet_manager.create_wallet(
            initial_owners=self.sample_owners,
            threshold=2,
            wallet_metadata={'name': 'Test Wallet'}
        )
        
        transaction = await self.wallet_manager.create_transaction(
            wallet_id=wallet.wallet_id,
            destination='0x9876543210987654321098765432109876543210',
            amount=1000,
            transaction_metadata={'purpose': 'Test transfer'}
        )
        
        # Serialize transaction
        transaction_dict = transaction.to_dict()
        transaction_json = json.dumps(transaction_dict)
        
        assert isinstance(transaction_json, str)
        assert 'transaction_id' in transaction_dict
        assert 'destination' in transaction_dict
        assert 'amount' in transaction_dict
        assert 'status' in transaction_dict
        assert 'signatures' in transaction_dict
    
    @pytest.mark.asyncio
    async def test_wallet_status_report(self):
        """Test wallet status reporting"""
        wallet = await self.wallet_manager.create_wallet(
            initial_owners=self.sample_owners,
            threshold=2,
            wallet_metadata={'name': 'Test Wallet'}
        )
        
        # Create a transaction
        transaction = await self.wallet_manager.create_transaction(
            wallet_id=wallet.wallet_id,
            destination='0x9876543210987654321098765432109876543210',
            amount=1000,
            transaction_metadata={'purpose': 'Test transfer'}
        )
        
        # Get wallet status
        status = await self.wallet_manager.get_wallet_status(wallet.wallet_address)
        
        assert status['wallet_address'] == wallet.wallet_address
        assert status['threshold'] == 2
        assert status['total_weight'] == 3
        assert len(status['owners']) == 3
        assert len(status['pending_transactions']) == 1
        assert len(status['approved_transactions']) == 0
        assert len(status['executed_transactions']) == 0
        assert len(status['rejected_transactions']) == 0
    
    @pytest.mark.asyncio
    async def test_audit_logs_creation(self):
        """Test audit log creation"""
        wallet = await self.wallet_manager.create_wallet(
            initial_owners=self.sample_owners,
            threshold=2,
            wallet_metadata={'name': 'Test Wallet'}
        )
        
        transaction = await self.wallet_manager.create_transaction(
            wallet_id=wallet.wallet_id,
            destination='0x9876543210987654321098765432109876543210',
            amount=1000,
            transaction_metadata={'purpose': 'Test transfer'}
        )
        
        # Sign transaction
        await self.wallet_manager.sign_transaction(
            wallet_address=wallet.wallet_address,
            transaction_id=transaction.transaction_id,
            signer_address=self.sample_owners[0]['address'],
            signature_data='signature_1_test'
        )
        
        # Get audit logs
        audit_logs = await self.wallet_manager.get_audit_logs(wallet.wallet_address)
        
        assert len(audit_logs) >= 3  # Wallet creation, transaction creation, signature
        
        # Check log types
        log_types = [log['action'] for log in audit_logs]
        assert 'wallet_created' in log_types
        assert 'transaction_created' in log_types
        assert 'transaction_signed' in log_types
    
    @pytest.mark.asyncio
    async def test_concurrent_transaction_signing(self):
        """Test concurrent transaction signing"""
        wallet = await self.wallet_manager.create_wallet(
            initial_owners=self.sample_owners,
            threshold=2,
            wallet_metadata={'name': 'Test Wallet'}
        )
        
        transaction = await self.wallet_manager.create_transaction(
            wallet_id=wallet.wallet_id,
            destination='0x9876543210987654321098765432109876543210',
            amount=1000,
            transaction_metadata={'purpose': 'Test transfer'}
        )
        
        # Try to sign concurrently with two different owners
        tasks = [
            self.wallet_manager.sign_transaction(
                wallet_id=wallet.wallet_id,
                transaction_id=transaction.transaction_id,
                owner_address=self.sample_owners[0]['address'],
                signature='signature_1_test'
            ),
            self.wallet_manager.sign_transaction(
                wallet_id=wallet.wallet_id,
                transaction_id=transaction.transaction_id,
                owner_address=self.sample_owners[1]['address'],
                signature='signature_2_test'
            )
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Both signatures should succeed
        assert all(results)
        
        # Check final status
        wallet_status = await self.wallet_manager.get_wallet_status(wallet.wallet_id)
        transaction_status = next(t for t in wallet_status['approved_transactions'] if t['transaction_id'] == transaction.transaction_id)
        assert len(transaction_status['signatures']) == 2
        assert transaction_status['approval_percentage'] == 100.0