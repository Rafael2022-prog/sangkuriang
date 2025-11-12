"""
Unit tests untuk IPFS Storage Integration
"""

import pytest
import pytest_asyncio
import asyncio
import tempfile
import os
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import aiohttp
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ipfs_storage import (
    IPFSStorage,
    IPFSFile,
    IPFSPinService,
    StorageMetrics,
    StorageStatus,
    ContentType
)


@pytest_asyncio.fixture
async def mock_aiohttp_session():
    """Mock aiohttp session"""
    session_mock = AsyncMock(spec=aiohttp.ClientSession)
    
    # Mock response untuk upload
    upload_response_mock = AsyncMock(spec=aiohttp.ClientResponse)
    upload_response_mock.status = 200
    upload_response_mock.json = AsyncMock(return_value={
        "Hash": "QmTestHash123456789",
        "Size": 1024,
        "Name": "test_file.txt"
    })
    
    # Mock response untuk get
    get_response_mock = AsyncMock(spec=aiohttp.ClientResponse)
    get_response_mock.status = 200
    get_response_mock.read = AsyncMock(return_value=b"test content")
    
    # Mock post method untuk upload
    session_mock.post = AsyncMock(return_value=AsyncMock(
        __aenter__=AsyncMock(return_value=upload_response_mock),
        __aexit__=AsyncMock(return_value=None)
    ))
    
    # Mock get method untuk download
    session_mock.get = AsyncMock(return_value=AsyncMock(
        __aenter__=AsyncMock(return_value=get_response_mock),
        __aexit__=AsyncMock(return_value=None)
    ))
    
    return session_mock


@pytest.fixture
def ipfs_config():
    """IPFS configuration"""
    return {
        "ipfs_api_url": "http://localhost:5001/api/v0",
        "ipfs_gateway_url": "http://localhost:8080",
        "pin_services": [
            {
                "name": "pinata",
                "api_endpoint": "https://api.pinata.cloud",
                "api_key": "test_api_key",
                "is_active": True,
                "max_storage_gb": 100,
                "reliability_score": 0.95,
                "cost_per_gb": 0.05,
                "supported_regions": ["global"],
                "encryption_support": True,
                "compression_support": True,
                "backup_support": False
            },
            {
                "name": "infura",
                "api_endpoint": "https://ipfs.infura.io",
                "api_key": "test_infura_key",
                "is_active": True,
                "max_storage_gb": 50,
                "reliability_score": 0.9,
                "cost_per_gb": 0.08,
                "supported_regions": ["global", "indonesia"],
                "encryption_support": True,
                "compression_support": False,
                "backup_support": True
            }
        ]
    }


@pytest_asyncio.fixture
async def ipfs_storage(ipfs_config, mock_aiohttp_session):
    """IPFS Storage instance"""
    storage = IPFSStorage(ipfs_config)
    storage.session = mock_aiohttp_session
    return storage


@pytest.fixture
def temp_text_file():
    """Create temporary text file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is test content for IPFS upload testing. Content ini akan diupload ke IPFS untuk testing sistem storage terdesentralisasi.")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_ipfs_storage_initialization(ipfs_config):
    """Test IPFS Storage initialization"""
    storage = IPFSStorage(ipfs_config)
    
    assert storage.ipfs_api_url == "http://localhost:5001/api/v0"
    assert storage.gateway_url == "http://localhost:8080"
    assert len(storage.pin_services) == 2
    assert storage.pin_services[0].name == "pinata"
    assert storage.pin_services[1].name == "infura"


@pytest.mark.asyncio
async def test_upload_file_success(ipfs_storage, temp_text_file):
    """Test upload file ke IPFS berhasil"""
    # Execute
    ipfs_file = await ipfs_storage.upload_file(
        file_path=temp_text_file,
        content_type=ContentType.PROPOSAL_DOCUMENT,
        uploader="test_user",
        metadata={"proposal_id": "123", "category": "technical"},
        encrypt=False,
        compress=False,
        pin=True,
        replication_factor=2,
        tags=["proposal", "technical", "indonesia"],
        language="id",
        region="indonesia"
    )
    
    # Verify
    assert isinstance(ipfs_file, IPFSFile)
    assert ipfs_file.hash is not None  # Hash should be generated from actual upload
    assert ipfs_file.name == os.path.basename(temp_text_file)
    assert ipfs_file.content_type == ContentType.PROPOSAL_DOCUMENT
    assert ipfs_file.uploaded_by == "test_user"
    assert ipfs_file.is_pinned is True
    assert ipfs_file.replication_factor == 2
    assert "proposal" in ipfs_file.tags
    assert ipfs_file.language == "id"
    assert ipfs_file.region == "indonesia"
    assert ipfs_file.status == StorageStatus.STORED


@pytest.mark.asyncio
async def test_upload_file_with_compression(ipfs_storage, temp_text_file):
    """Test upload file dengan compression"""
    # Execute
    ipfs_file = await ipfs_storage.upload_file(
        file_path=temp_text_file,
        content_type=ContentType.TECHNICAL_SPEC,
        uploader="test_user",
        compress=True,
        pin=False
    )
    
    # Verify
    assert isinstance(ipfs_file, IPFSFile)
    assert ipfs_file.compression_type == "gzip"
    assert ipfs_file.is_pinned is False


@pytest.mark.asyncio
async def test_upload_file_with_encryption(ipfs_storage, temp_text_file):
    """Test upload file dengan encryption"""
    # Execute
    ipfs_file = await ipfs_storage.upload_file(
        file_path=temp_text_file,
        content_type=ContentType.GOVERNANCE_DOCUMENT,
        uploader="test_user",
        encrypt=True,
        pin=True
    )
    
    # Verify
    assert isinstance(ipfs_file, IPFSFile)
    assert ipfs_file.encryption_key is not None
    assert len(ipfs_file.encryption_key) == 32


@pytest.mark.asyncio
async def test_upload_file_validation_errors(ipfs_storage):
    """Test upload file dengan validasi error"""
    # Test file tidak ada
    with pytest.raises(FileNotFoundError, match="File not found"):
        await ipfs_storage.upload_file(
            file_path="/non/existing/file.txt",
            content_type=ContentType.PROPOSAL_DOCUMENT,
            uploader="test_user"
        )
    
    # Test file kosong
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("")  # Empty file
        empty_file_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Cannot upload empty file"):
            await ipfs_storage.upload_file(
                file_path=empty_file_path,
                content_type=ContentType.PROPOSAL_DOCUMENT,
                uploader="test_user"
            )
    finally:
        if os.path.exists(empty_file_path):
            os.unlink(empty_file_path)


@pytest.mark.asyncio
async def test_upload_text_content_success(ipfs_storage):
    """Test upload text content berhasil"""
    content = """
    # Proposal Pengembangan Sistem Kriptografi Baru
    
    ## Latar Belakang
    Keamanan data menjadi semakin penting dalam era digital ini. 
    Indonesia membutuhkan solusi kriptografi lokal yang handal.
    
    ## Tujuan
    Mengembangkan sistem kriptografi berbasis matematika Nusantara.
    """
    
    # Execute
    ipfs_file = await ipfs_storage.upload_text_content(
        content=content,
        file_name="proposal_kriptografi.md",
        content_type=ContentType.PROPOSAL_DOCUMENT,
        uploader="crypto_researcher",
        metadata={"version": "1.0", "language": "id"},
        tags=["cryptography", "indonesia", "security"],
        language="id",
        region="indonesia"
    )
    
    # Verify
    assert isinstance(ipfs_file, IPFSFile)
    assert ipfs_file.name == "proposal_kriptografi.md"
    assert ipfs_file.content_type == ContentType.PROPOSAL_DOCUMENT
    assert ipfs_file.uploaded_by == "crypto_researcher"
    assert "cryptography" in ipfs_file.tags
    assert ipfs_file.language == "id"
    assert ipfs_file.region == "indonesia"


@pytest.mark.asyncio
async def test_get_file_success(ipfs_storage):
    """Test get file dari IPFS berhasil"""
    # Setup - add file to cache
    test_file = IPFSFile(
        hash="QmTestHash123456789",
        name="test_file.txt",
        size=1024,
        content_type=ContentType.PROPOSAL_DOCUMENT,
        metadata={"test": "data"},
        uploaded_by="test_user",
        uploaded_at=1234567890,
        last_accessed=1234567890,
        access_count=1,
        is_pinned=True,
        pin_services=["pinata"],
        replication_factor=2,
        encryption_key=None,
        compression_type=None,
        original_hash="original_checksum",
        status=StorageStatus.STORED,
        version=1,
        parent_hash=None,
        tags=["test"],
        related_files=[],
        checksum="file_checksum",
        mime_type="text/plain",
        language="id",
        region="indonesia",
        retention_days=None,
        auto_pin=True,
        backup_locations=[]
    )
    
    ipfs_storage.file_cache["QmTestHash123456789"] = test_file
    
    # Execute
    result = await ipfs_storage.get_file("QmTestHash123456789")
    
    # Verify
    assert result is not None
    assert result.hash == "QmTestHash123456789"
    assert result.name == "test_file.txt"
    assert result.access_count == 2  # Incremented
    assert result.last_accessed > 1234567890  # Updated


@pytest.mark.asyncio
async def test_get_file_not_found(ipfs_storage):
    """Test get file yang tidak ada"""
    # Execute
    result = await ipfs_storage.get_file("QmNonExistingHash")
    
    # Verify
    assert result is None


@pytest.mark.asyncio
async def test_pin_file_success(ipfs_storage):
    """Test pin file berhasil"""
    # Execute
    result = await ipfs_storage.pin_file("QmTestHash123456789", "pinata")
    
    # Verify
    assert result is True


@pytest.mark.asyncio
async def test_unpin_file_success(ipfs_storage):
    """Test unpin file berhasil"""
    # Execute
    result = await ipfs_storage.unpin_file("QmTestHash123456789", "pinata")
    
    # Verify
    assert result is True


@pytest.mark.asyncio
async def test_get_file_stats(ipfs_storage):
    """Test get file stats"""
    # Setup - add file to cache
    test_file = IPFSFile(
        hash="QmTestHash123456789",
        name="test_file.txt",
        size=1024,
        content_type=ContentType.PROPOSAL_DOCUMENT,
        metadata={"proposal_id": "123"},
        uploaded_by="test_user",
        uploaded_at=1234567890,
        last_accessed=1234567890,
        access_count=5,
        is_pinned=True,
        pin_services=["pinata", "infura"],
        replication_factor=2,
        encryption_key=None,
        compression_type=None,
        original_hash="original_checksum",
        status=StorageStatus.STORED,
        version=1,
        parent_hash=None,
        tags=["proposal", "technical"],
        related_files=[],
        checksum="file_checksum",
        mime_type="text/plain",
        language="id",
        region="indonesia",
        retention_days=None,
        auto_pin=True,
        backup_locations=[]
    )
    
    ipfs_storage.file_cache["QmTestHash123456789"] = test_file
    
    # Execute
    stats = await ipfs_storage.get_file_stats("QmTestHash123456789")
    
    # Verify
    assert stats is not None
    assert stats["hash"] == "QmTestHash123456789"
    assert stats["name"] == "test_file.txt"
    assert stats["size"] == 1024
    assert stats["content_type"] == "proposal_document"
    assert stats["access_count"] == 5
    assert stats["is_pinned"] is True
    assert "pinata" in stats["pin_services"]
    assert stats["language"] == "id"
    assert stats["region"] == "indonesia"


@pytest.mark.asyncio
async def test_search_files(ipfs_storage):
    """Test search files"""
    # Setup - add multiple files to cache
    files = [
        IPFSFile(
            hash="QmHash1",
            name="proposal_teknis.txt",
            size=1024,
            content_type=ContentType.PROPOSAL_DOCUMENT,
            metadata={},
            uploaded_by="user1",
            uploaded_at=1234567890,
            last_accessed=1234567890,
            access_count=1,
            is_pinned=True,
            pin_services=[],
            replication_factor=1,
            encryption_key=None,
            compression_type=None,
            original_hash=None,
            status=StorageStatus.STORED,
            version=1,
            parent_hash=None,
            tags=["proposal", "technical"],
            related_files=[],
            checksum="checksum1",
            mime_type="text/plain",
            language="id",
            region="indonesia",
            retention_days=None,
            auto_pin=True,
            backup_locations=[]
        ),
        IPFSFile(
            hash="QmHash2",
            name="audit_report.pdf",
            size=2048,
            content_type=ContentType.AUDIT_REPORT,
            metadata={},
            uploaded_by="user2",
            uploaded_at=1234567891,
            last_accessed=1234567891,
            access_count=2,
            is_pinned=False,
            pin_services=[],
            replication_factor=1,
            encryption_key=None,
            compression_type=None,
            original_hash=None,
            status=StorageStatus.STORED,
            version=1,
            parent_hash=None,
            tags=["audit", "security"],
            related_files=[],
            checksum="checksum2",
            mime_type="application/pdf",
            language="en",
            region="global",
            retention_days=None,
            auto_pin=False,
            backup_locations=[]
        ),
        IPFSFile(
            hash="QmHash3",
            name="proposal_komunitas.md",
            size=512,
            content_type=ContentType.COMMUNITY_DISCUSSION,
            metadata={},
            uploaded_by="user3",
            uploaded_at=1234567892,
            last_accessed=1234567892,
            access_count=3,
            is_pinned=True,
            pin_services=[],
            replication_factor=2,
            encryption_key=None,
            compression_type=None,
            original_hash=None,
            status=StorageStatus.STORED,
            version=1,
            parent_hash=None,
            tags=["proposal", "community"],
            related_files=[],
            checksum="checksum3",
            mime_type="text/markdown",
            language="id",
            region="indonesia",
            retention_days=None,
            auto_pin=True,
            backup_locations=[]
        )
    ]
    
    for file_obj in files:
        ipfs_storage.file_cache[file_obj.hash] = file_obj
    
    # Execute - search by name
    results = await ipfs_storage.search_files(
        query="proposal",
        limit=10
    )
    
    # Verify
    assert len(results) == 2  # Should find 2 files with "proposal" in name
    assert all("proposal" in file.name.lower() for file in results)
    
    # Execute - search with content type filter
    results = await ipfs_storage.search_files(
        query="report",
        content_type=ContentType.AUDIT_REPORT,
        limit=10
    )
    
    # Verify
    assert len(results) == 1
    assert results[0].name == "audit_report.pdf"
    assert results[0].content_type == ContentType.AUDIT_REPORT
    
    # Execute - search with language filter
    results = await ipfs_storage.search_files(
        query="proposal",
        language="id",
        limit=10
    )
    
    # Verify
    assert len(results) == 2  # Both Indonesian proposals
    assert all(file.language == "id" for file in results)


@pytest.mark.asyncio
async def test_get_storage_metrics(ipfs_storage):
    """Test get storage metrics"""
    # Setup - add files to cache
    files = [
        IPFSFile(
            hash="QmHash1",
            name="file1.txt",
            size=1024,
            content_type=ContentType.PROPOSAL_DOCUMENT,
            metadata={},
            uploaded_by="user1",
            uploaded_at=1234567890,
            last_accessed=1234567890,
            access_count=1,
            is_pinned=True,
            pin_services=[],
            replication_factor=1,
            encryption_key="encryption_key_1",  # Encrypted
            compression_type=None,
            original_hash=None,
            status=StorageStatus.STORED,
            version=1,
            parent_hash=None,
            tags=[],
            related_files=[],
            checksum="checksum1",
            mime_type="text/plain",
            language="id",
            region="indonesia",
            retention_days=None,
            auto_pin=True,
            backup_locations=[]
        ),
        IPFSFile(
            hash="QmHash2",
            name="file2.txt",
            size=2048,
            content_type=ContentType.AUDIT_REPORT,
            metadata={},
            uploaded_by="user2",
            uploaded_at=1234567891,
            last_accessed=1234567891,
            access_count=2,
            is_pinned=False,
            pin_services=[],
            replication_factor=2,
            encryption_key=None,
            compression_type="gzip",  # Compressed
            original_hash=None,
            status=StorageStatus.STORED,
            version=1,
            parent_hash=None,
            tags=[],
            related_files=[],
            checksum="checksum2",
            mime_type="text/plain",
            language="en",
            region="global",
            retention_days=None,
            auto_pin=False,
            backup_locations=[]
        )
    ]
    
    for file_obj in files:
        ipfs_storage.file_cache[file_obj.hash] = file_obj
    
    # Execute
    metrics = await ipfs_storage.get_storage_metrics()
    
    # Verify
    assert isinstance(metrics, StorageMetrics)
    assert metrics.total_files == 2
    assert metrics.total_size_bytes == 3072  # 1024 + 2048
    assert metrics.pinned_files == 1  # Only 1 file is pinned
    assert metrics.replication_factor_average == 1.5  # (1 + 2) / 2
    assert metrics.active_pin_services == 2  # Both pin services are active
    assert metrics.encryption_usage_rate == 50.0  # 1 out of 2 files encrypted
    assert metrics.compression_usage_rate == 50.0  # 1 out of 2 files compressed
    assert metrics.content_type_distribution["proposal_document"] == 1
    assert metrics.content_type_distribution["audit_report"] == 1
    assert metrics.regional_distribution["indonesia"] == 1
    assert metrics.regional_distribution["global"] == 1


@pytest.mark.asyncio
async def test_cleanup_expired_files(ipfs_storage):
    """Test cleanup expired files"""
    # Setup - add files with different retention periods
    current_time = 1234567890
    
    # File 1: Not expired (retention 30 days, uploaded 15 days ago)
    file1 = IPFSFile(
        hash="QmHash1",
        name="file1.txt",
        size=1024,
        content_type=ContentType.PROPOSAL_DOCUMENT,
        metadata={},
        uploaded_by="user1",
        uploaded_at=current_time - (15 * 24 * 3600),  # 15 days ago
        last_accessed=current_time,
        access_count=1,
        is_pinned=True,
        pin_services=[],
        replication_factor=1,
        encryption_key=None,
        compression_type=None,
        original_hash=None,
        status=StorageStatus.STORED,
        version=1,
        parent_hash=None,
        tags=[],
        related_files=[],
        checksum="checksum1",
        mime_type="text/plain",
        language="id",
        region="indonesia",
        retention_days=30,  # 30 days retention
        auto_pin=True,
        backup_locations=[]
    )
    
    # File 2: Expired (retention 10 days, uploaded 15 days ago)
    file2 = IPFSFile(
        hash="QmHash2",
        name="file2.txt",
        size=2048,
        content_type=ContentType.AUDIT_REPORT,
        metadata={},
        uploaded_by="user2",
        uploaded_at=current_time - (15 * 24 * 3600),  # 15 days ago
        last_accessed=current_time,
        access_count=2,
        is_pinned=False,
        pin_services=[],
        replication_factor=1,
        encryption_key=None,
        compression_type=None,
        original_hash=None,
        status=StorageStatus.STORED,
        version=1,
        parent_hash=None,
        tags=[],
        related_files=[],
        checksum="checksum2",
        mime_type="text/plain",
        language="en",
        region="global",
        retention_days=10,  # 10 days retention - EXPIRED
        auto_pin=False,
        backup_locations=[]
    )
    
    # File 3: No retention (permanent)
    file3 = IPFSFile(
        hash="QmHash3",
        name="file3.txt",
        size=512,
        content_type=ContentType.COMMUNITY_DISCUSSION,
        metadata={},
        uploaded_by="user3",
        uploaded_at=current_time - (100 * 24 * 3600),  # 100 days ago
        last_accessed=current_time,
        access_count=3,
        is_pinned=True,
        pin_services=[],
        replication_factor=2,
        encryption_key=None,
        compression_type=None,
        original_hash=None,
        status=StorageStatus.STORED,
        version=1,
        parent_hash=None,
        tags=[],
        related_files=[],
        checksum="checksum3",
        mime_type="text/plain",
        language="id",
        region="indonesia",
        retention_days=None,  # No retention - permanent
        auto_pin=True,
        backup_locations=[]
    )
    
    # Add files to cache
    ipfs_storage.file_cache["QmHash1"] = file1
    ipfs_storage.file_cache["QmHash2"] = file2
    ipfs_storage.file_cache["QmHash3"] = file3
    
    # Mock time.time to return current_time
    with patch('time.time', return_value=current_time):
        # Execute
        expired_count = await ipfs_storage.cleanup_expired_files()
    
    # Verify
    assert expired_count == 1  # Only file2 should be expired
    assert "QmHash1" in ipfs_storage.file_cache  # Not expired
    assert "QmHash2" not in ipfs_storage.file_cache  # Expired and removed
    assert "QmHash3" in ipfs_storage.file_cache  # Permanent file


@pytest.mark.asyncio
async def test_ipfs_storage_context_manager(ipfs_config):
    """Test IPFS Storage sebagai async context manager"""
    # Execute
    async with IPFSStorage(ipfs_config) as storage:
        assert storage.session is not None
        assert isinstance(storage.session, aiohttp.ClientSession)
    
    # Verify session is closed after exiting context
    # Note: In real implementation, we'd check if session is closed
    # For now, we just verify the context manager works


@pytest.mark.asyncio
async def test_upload_file_fallback_to_pin_service(ipfs_storage, temp_text_file, mock_aiohttp_session):
    """Test upload file fallback ke pin service saat IPFS node gagal"""
    # Mock IPFS API failure
    response_mock = AsyncMock(spec=aiohttp.ClientResponse)
    response_mock.status = 500
    response_mock.text = AsyncMock(return_value="Internal Server Error")
    
    mock_aiohttp_session.post = AsyncMock(return_value=AsyncMock(
        __aenter__=AsyncMock(return_value=response_mock),
        __aexit__=AsyncMock(return_value=None)
    ))
    
    # Mock successful fallback to pin service
    with patch.object(ipfs_storage, '_upload_to_pin_service', return_value="QmFallbackHash123"):
        # Execute
        ipfs_file = await ipfs_storage.upload_file(
            file_path=temp_text_file,
            content_type=ContentType.PROPOSAL_DOCUMENT,
            uploader="test_user"
        )
    
    # Verify
    assert isinstance(ipfs_file, IPFSFile)
    assert ipfs_file.hash == "QmFallbackHash123"  # Should use fallback hash
    assert ipfs_file.status == StorageStatus.STORED


@pytest.mark.asyncio
async def test_pin_to_multiple_services(ipfs_storage):
    """Test pin file ke multiple services"""
    # Mock pin services
    ipfs_storage.pin_services = [
        IPFSPinService(
            name="pinata",
            api_endpoint="https://api.pinata.cloud",
            api_key="test_key",
            is_active=True,
            max_storage_gb=100,
            current_usage_gb=0,
            reliability_score=0.95,
            cost_per_gb=0.05,
            supported_regions=["global"],
            encryption_support=True,
            compression_support=True,
            backup_support=False
        ),
        IPFSPinService(
            name="infura",
            api_endpoint="https://ipfs.infura.io",
            api_key="test_key",
            is_active=True,
            max_storage_gb=50,
            current_usage_gb=0,
            reliability_score=0.9,
            cost_per_gb=0.08,
            supported_regions=["global"],
            encryption_support=True,
            compression_support=False,
            backup_support=True
        ),
        IPFSPinService(
            name="inactive_service",
            api_endpoint="https://inactive.io",
            api_key="test_key",
            is_active=False,  # Inactive
            max_storage_gb=50,
            current_usage_gb=0,
            reliability_score=0.8,
            cost_per_gb=0.1,
            supported_regions=["global"],
            encryption_support=False,
            compression_support=False,
            backup_support=False
        )
    ]
    
    # Mock _pin_to_service method
    with patch.object(ipfs_storage, '_pin_to_service', return_value=True) as mock_pin:
        # Execute
        await ipfs_storage._pin_to_multiple_services("QmTestHash123", 3)
    
    # Verify - should only pin to active services
    assert mock_pin.call_count == 2  # Only 2 services are active
    mock_pin.assert_any_call("QmTestHash123", ipfs_storage.pin_services[0])
    mock_pin.assert_any_call("QmTestHash123", ipfs_storage.pin_services[1])