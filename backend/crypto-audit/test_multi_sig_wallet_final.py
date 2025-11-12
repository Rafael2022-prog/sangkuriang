import pytest
import asyncio
import json
from datetime import datetime, timedelta
import hmac
import hashlib
from multi_sig_wallet import MultiSigWalletManager, SignatureType


@pytest.mark.asyncio
async def test_create_wallet_success():
    """Test successful wallet creation"""
    wallet_manager = MultiSigWalletManager()
    sample_owners = [
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
        }
    ]
    
    wallet = await wallet_manager.create_wallet(
        initial_owners=sample_owners,
        threshold=2,
        wallet_metadata={'name': 'Test Wallet'}
    )
    
    assert wallet.wallet_address is not None
    assert wallet.threshold == 2
    assert len(wallet.owners) == 2
    assert wallet.metadata['name'] == 'Test Wallet'


@pytest.mark.asyncio
async def test_create_transaction_success():
    """Test successful transaction creation"""
    wallet_manager = MultiSigWalletManager()
    sample_owners = [
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
        }
    ]
    
    wallet = await wallet_manager.create_wallet(
        initial_owners=sample_owners,
        threshold=2,
        wallet_metadata={'name': 'Test Wallet'}
    )
    
    transaction = await wallet_manager.create_transaction(
        wallet_address=wallet.wallet_address,
        to_address='0x9876543210987654321098765432109876543210',
        amount=1000,
        metadata={'purpose': 'Test transfer'}
    )
    
    assert transaction.transaction_id is not None
    assert transaction.to_address == '0x9876543210987654321098765432109876543210'
    assert transaction.amount == 1000
    assert transaction.status.value == 'pending'
    assert len(transaction.signatures) == 0


@pytest.mark.asyncio
async def test_sign_transaction_success():
    """Test successful transaction signing"""
    wallet_manager = MultiSigWalletManager()
    sample_owners = [
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
        }
    ]
    
    wallet = await wallet_manager.create_wallet(
        initial_owners=sample_owners,
        threshold=2,
        wallet_metadata={'name': 'Test Wallet'}
    )
    
    transaction = await wallet_manager.create_transaction(
        wallet_address=wallet.wallet_address,
        to_address='0x9876543210987654321098765432109876543210',
        amount=1000,
        metadata={'purpose': 'Test transfer'}
    )
    
    # Sign with first owner - use signature yang sesuai dengan format HMAC
    import hmac
    import hashlib
    
    # Generate signature yang valid untuk testing
    expected_signature = hmac.new(
        sample_owners[0]['public_key'].encode(),
        transaction.transaction_id.encode(),
        hashlib.sha256
    ).hexdigest()
    
    result1 = await wallet_manager.sign_transaction(
        wallet_address=wallet.wallet_address,
        transaction_id=transaction.transaction_id,
        signer_address=sample_owners[0]['address'],
        signature_data=expected_signature[:16]  # Ambil 16 karakter pertama
    )
    
    assert result1 is True
    
    # Check transaction status after first signature
    wallet_status = await wallet_manager.get_wallet_status(wallet.wallet_address)
    assert wallet_status['transaction_stats']['pending'] == 1


@pytest.mark.asyncio
async def test_execute_transaction_success():
    """Test successful transaction execution"""
    wallet_manager = MultiSigWalletManager()
    sample_owners = [
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
        }
    ]
    
    wallet = await wallet_manager.create_wallet(
        initial_owners=sample_owners,
        threshold=2,
        wallet_metadata={'name': 'Test Wallet'}
    )
    
    transaction = await wallet_manager.create_transaction(
        wallet_address=wallet.wallet_address,
        to_address='0x9876543210987654321098765432109876543210',
        amount=1000,
        metadata={'purpose': 'Test transfer'}
    )
    
    # Sign with two owners to reach threshold
    # Sign with first owner - generate valid signature
    expected_signature1 = hmac.new(
        sample_owners[0]['public_key'].encode(),
        transaction.transaction_id.encode(),
        hashlib.sha256
    ).hexdigest()
    
    await wallet_manager.sign_transaction(
        wallet_address=wallet.wallet_address,
        transaction_id=transaction.transaction_id,
        signer_address=sample_owners[0]['address'],
        signature_data=expected_signature1[:16]
    )
    
    # Sign with second owner to reach threshold - generate valid signature
    expected_signature2 = hmac.new(
        sample_owners[1]['public_key'].encode(),
        transaction.transaction_id.encode(),
        hashlib.sha256
    ).hexdigest()
    
    await wallet_manager.sign_transaction(
        wallet_address=wallet.wallet_address,
        transaction_id=transaction.transaction_id,
        signer_address=sample_owners[1]['address'],
        signature_data=expected_signature2[:16]
    )
    
    # Execute the transaction
    result = await wallet_manager.execute_transaction(
        wallet_address=wallet.wallet_address,
        transaction_id=transaction.transaction_id
    )
    
    assert result is True
    
    # Check transaction status
    wallet_status = await wallet_manager.get_wallet_status(wallet.wallet_address)
    assert wallet_status['transaction_stats']['executed'] == 1


@pytest.mark.asyncio
async def test_wallet_status_report():
    """Test wallet status reporting"""
    wallet_manager = MultiSigWalletManager()
    sample_owners = [
        {
            'address': '0x1234567890123456789012345678901234567890',
            'public_key': 'public_key_1_test',
            'signature_type': 'ecdsa',
            'weight': 1
        }
    ]
    
    wallet = await wallet_manager.create_wallet(
        initial_owners=sample_owners,
        threshold=1,
        wallet_metadata={'name': 'Test Wallet'}
    )
    
    # Create a transaction
    transaction = await wallet_manager.create_transaction(
        wallet_address=wallet.wallet_address,
        to_address='0x9876543210987654321098765432109876543210',
        amount=1000,
        metadata={'purpose': 'Test transfer'}
    )
    
    # Get wallet status
    status = await wallet_manager.get_wallet_status(wallet.wallet_address)
    
    assert status['wallet_address'] == wallet.wallet_address
    assert status['threshold'] == 1
    assert status['total_weight'] == 1
    assert len(status['owner_activity']) == 1
    assert status['transaction_stats']['pending'] == 1


@pytest.mark.asyncio
async def test_transaction_serialization():
    """Test transaction serialization and deserialization"""
    wallet_manager = MultiSigWalletManager()
    sample_owners = [
        {
            'address': '0x1234567890123456789012345678901234567890',
            'public_key': 'public_key_1_test',
            'signature_type': 'ecdsa',
            'weight': 1
        }
    ]
    
    wallet = await wallet_manager.create_wallet(
        initial_owners=sample_owners,
        threshold=1,
        wallet_metadata={'name': 'Test Wallet'}
    )
    
    transaction = await wallet_manager.create_transaction(
        wallet_address=wallet.wallet_address,
        to_address='0x9876543210987654321098765432109876543210',
        amount=1000,
        metadata={'purpose': 'Test transfer'}
    )
    
    # Serialize transaction
    transaction_dict = transaction.to_dict()
    transaction_json = json.dumps(transaction_dict)
    
    assert isinstance(transaction_json, str)
    assert 'transaction_id' in transaction_dict
    assert 'to_address' in transaction_dict
    assert 'amount' in transaction_dict
    assert 'status' in transaction_dict
    assert 'signatures' in transaction_dict


@pytest.mark.asyncio
async def test_audit_logs_creation():
    """Test audit log creation"""
    wallet_manager = MultiSigWalletManager()
    sample_owners = [
        {
            'address': '0x1234567890123456789012345678901234567890',
            'public_key': 'public_key_1_test',
            'signature_type': 'ecdsa',
            'weight': 1
        }
    ]
    
    wallet = await wallet_manager.create_wallet(
        initial_owners=sample_owners,
        threshold=1,
        wallet_metadata={'name': 'Test Wallet'}
    )
    
    transaction = await wallet_manager.create_transaction(
        wallet_address=wallet.wallet_address,
        to_address='0x9876543210987654321098765432109876543210',
        amount=1000,
        metadata={'purpose': 'Test transfer'}
    )
    
    # Sign transaction - generate valid signature
    expected_signature = hmac.new(
        sample_owners[0]['public_key'].encode(),
        transaction.transaction_id.encode(),
        hashlib.sha256
    ).hexdigest()
    
    await wallet_manager.sign_transaction(
        wallet_address=wallet.wallet_address,
        transaction_id=transaction.transaction_id,
        signer_address=sample_owners[0]['address'],
        signature_data=expected_signature[:16]
    )
    
    # Get audit logs
    audit_logs = await wallet_manager.get_audit_logs(wallet.wallet_address)
    
    assert len(audit_logs) >= 3  # Wallet creation, transaction creation, signature
    
    # Check log types
    log_types = [log.action for log in audit_logs]
    assert 'WALLET_CREATED' in log_types
    assert 'TRANSACTION_CREATED' in log_types
    assert 'TRANSACTION_SIGNED' in log_types