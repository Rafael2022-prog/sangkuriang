"""
SANGKURIANG IPFS Storage Integration
Integrasi dengan IPFS untuk storage terdesentralisasi
"""

import asyncio
import json
import hashlib
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import aiofiles
from pathlib import Path
import tempfile
import os


class StorageStatus(Enum):
    """Status penyimpanan IPFS"""
    PENDING = "pending"
    UPLOADING = "uploading"
    STORED = "stored"
    PINNED = "pinned"
    FAILED = "failed"
    EXPIRED = "expired"


class ContentType(Enum):
    """Tipe konten yang disimpan"""
    PROPOSAL_DOCUMENT = "proposal_document"
    TECHNICAL_SPEC = "technical_specification"
    CODE_REPOSITORY = "code_repository"
    AUDIT_REPORT = "audit_report"
    COMMUNITY_DISCUSSION = "community_discussion"
    GOVERNANCE_DOCUMENT = "governance_document"
    TREASURY_REPORT = "treasury_report"
    MEDIA_ASSET = "media_asset"
    BACKUP_DATA = "backup_data"


@dataclass
class IPFSFile:
    """Representasi file di IPFS"""
    hash: str  # IPFS Content Identifier (CID)
    name: str
    size: int
    content_type: ContentType
    metadata: Dict[str, Any]
    uploaded_by: str
    uploaded_at: float
    last_accessed: float
    access_count: int
    is_pinned: bool
    pin_services: List[str]
    replication_factor: int
    encryption_key: Optional[str]
    compression_type: Optional[str]
    original_hash: Optional[str]  # Hash dari file asli sebelum encryption/compression
    status: StorageStatus
    version: int
    parent_hash: Optional[str]  # Untuk version control
    tags: List[str]
    related_files: List[str]  # CID dari file terkait
    checksum: str  # SHA256 checksum untuk integritas
    mime_type: str
    language: str
    region: str
    retention_days: Optional[int]
    auto_pin: bool
    backup_locations: List[str]  # Lokasi backup selain IPFS


@dataclass
class IPFSPinService:
    """Konfigurasi IPFS Pin Service"""
    name: str
    api_endpoint: str
    api_key: str
    is_active: bool
    max_storage_gb: int
    current_usage_gb: float
    reliability_score: float  # 0-1
    cost_per_gb: float
    supported_regions: List[str]
    encryption_support: bool
    compression_support: bool
    backup_support: bool


@dataclass
class StorageMetrics:
    """Metrics untuk IPFS storage"""
    total_files: int
    total_size_bytes: int
    pinned_files: int
    replication_factor_average: float
    upload_success_rate: float
    average_upload_time: float
    storage_cost_per_month: float
    bandwidth_usage_gb: float
    active_pin_services: int
    failed_uploads: int
    expired_files: int
    encryption_usage_rate: float
    compression_usage_rate: float
    regional_distribution: Dict[str, int]
    content_type_distribution: Dict[str, int]
    version_control_efficiency: float


class IPFSStorage:
    """IPFS Storage Manager untuk SANGKURIANG"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ipfs_api_url = config.get('ipfs_api_url', 'http://localhost:5001/api/v0')
        self.gateway_url = config.get('ipfs_gateway_url', 'http://localhost:8080')
        self.pin_services: List[IPFSPinService] = []
        self.file_cache: Dict[str, IPFSFile] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Load pin services from config
        self._load_pin_services()
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300),
            connector=aiohttp.TCPConnector(limit=100)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _load_pin_services(self):
        """Load IPFS pin services dari config"""
        services_config = self.config.get('pin_services', [])
        for service_config in services_config:
            service = IPFSPinService(
                name=service_config['name'],
                api_endpoint=service_config['api_endpoint'],
                api_key=service_config['api_key'],
                is_active=service_config.get('is_active', True),
                max_storage_gb=service_config.get('max_storage_gb', 100),
                current_usage_gb=0.0,
                reliability_score=service_config.get('reliability_score', 0.9),
                cost_per_gb=service_config.get('cost_per_gb', 0.05),
                supported_regions=service_config.get('supported_regions', ['global']),
                encryption_support=service_config.get('encryption_support', True),
                compression_support=service_config.get('compression_support', True),
                backup_support=service_config.get('backup_support', False)
            )
            self.pin_services.append(service)
    
    async def upload_file(
        self,
        file_path: str,
        content_type: ContentType,
        uploader: str,
        metadata: Optional[Dict] = None,
        encrypt: bool = False,
        compress: bool = False,
        pin: bool = True,
        replication_factor: int = 3,
        tags: Optional[List[str]] = None,
        language: str = "id",
        region: str = "indonesia",
        retention_days: Optional[int] = None
    ) -> IPFSFile:
        """Upload file ke IPFS"""
        if not self.session:
            raise RuntimeError("IPFSStorage must be used as async context manager")
        
        # Validasi file
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError("Cannot upload empty file")
        
        # Generate file checksum
        checksum = await self._calculate_checksum(file_path)
        
        # Baca file
        async with aiofiles.open(file_path, 'rb') as f:
            file_content = await f.read()
        
        # Apply compression jika diminta
        if compress:
            file_content = await self._compress_content(file_content)
            compression_type = "gzip"
        else:
            compression_type = None
        
        # Apply encryption jika diminta
        encryption_key = None
        if encrypt:
            file_content, encryption_key = await self._encrypt_content(file_content)
        
        # Upload ke IPFS
        upload_start = time.time()
        
        try:
            # Upload via IPFS API
            form_data = aiohttp.FormData()
            form_data.add_field('file', file_content, filename=os.path.basename(file_path))
            form_data.add_field('pin', str(pin).lower())
            
            async with self.session.post(
                f"{self.ipfs_api_url}/add",
                data=form_data,
                timeout=aiohttp.ClientTimeout(total=600)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"IPFS upload failed: {response.status} - {error_text}")
                
                result = await response.json()
                ipfs_hash = result['Hash']
                uploaded_size = result['Size']
        
        except Exception as e:
            # Fallback ke pin service jika IPFS node lokal gagal
            ipfs_hash = await self._upload_to_pin_service(file_content, os.path.basename(file_path))
            uploaded_size = len(file_content)
        
        upload_time = time.time() - upload_start
        
        # Pin ke multiple services untuk redundancy
        if pin:
            await self._pin_to_multiple_services(ipfs_hash, replication_factor)
        
        # Buat IPFSFile object
        ipfs_file = IPFSFile(
            hash=ipfs_hash,
            name=os.path.basename(file_path),
            size=uploaded_size,
            content_type=content_type,
            metadata=metadata or {},
            uploaded_by=uploader,
            uploaded_at=upload_start,
            last_accessed=upload_start,
            access_count=1,
            is_pinned=pin,
            pin_services=[],
            replication_factor=replication_factor,
            encryption_key=encryption_key,
            compression_type=compression_type,
            original_hash=checksum,
            status=StorageStatus.STORED,
            version=1,
            parent_hash=None,
            tags=tags or [],
            related_files=[],
            checksum=checksum,
            mime_type=self._get_mime_type(file_path),
            language=language,
            region=region,
            retention_days=retention_days,
            auto_pin=pin,
            backup_locations=[]
        )
        
        # Update pin services
        if pin:
            ipfs_file.pin_services = [service.name for service in self.pin_services if service.is_active]
        
        # Cache file
        self.file_cache[ipfs_hash] = ipfs_file
        
        return ipfs_file
    
    async def upload_text_content(
        self,
        content: str,
        file_name: str,
        content_type: ContentType,
        uploader: str,
        metadata: Optional[Dict] = None,
        encrypt: bool = False,
        compress: bool = False,
        pin: bool = True,
        tags: Optional[List[str]] = None,
        language: str = "id",
        region: str = "indonesia"
    ) -> IPFSFile:
        """Upload text content ke IPFS"""
        # Simpan ke temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Upload via method upload_file
            ipfs_file = await self.upload_file(
                file_path=temp_file_path,
                content_type=content_type,
                uploader=uploader,
                metadata=metadata,
                encrypt=encrypt,
                compress=compress,
                pin=pin,
                tags=tags,
                language=language,
                region=region
            )
            
            # Update nama file
            ipfs_file.name = file_name
            
            return ipfs_file
        
        finally:
            # Cleanup temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    async def get_file(self, ipfs_hash: str, update_access: bool = True) -> Optional[IPFSFile]:
        """Dapatkan file dari IPFS"""
        # Check cache dulu
        if ipfs_hash in self.file_cache:
            ipfs_file = self.file_cache[ipfs_hash]
            if update_access:
                ipfs_file.last_accessed = time.time()
                ipfs_file.access_count += 1
            return ipfs_file
        
        # Fetch dari IPFS
        if not self.session:
            return None
        
        try:
            async with self.session.get(
                f"{self.gateway_url}/ipfs/{ipfs_hash}",
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                if response.status == 200:
                    # File ditemukan, tapi kita tidak punya metadata lengkap
                    # Return basic IPFSFile
                    content = await response.read()
                    
                    ipfs_file = IPFSFile(
                        hash=ipfs_hash,
                        name=f"ipfs_file_{ipfs_hash[:8]}",
                        size=len(content),
                        content_type=ContentType.BACKUP_DATA,
                        metadata={},
                        uploaded_by="unknown",
                        uploaded_at=time.time(),
                        last_accessed=time.time(),
                        access_count=1,
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
                        checksum="",
                        mime_type="application/octet-stream",
                        language="unknown",
                        region="unknown",
                        retention_days=None,
                        auto_pin=False,
                        backup_locations=[]
                    )
                    
                    self.file_cache[ipfs_hash] = ipfs_file
                    return ipfs_file
                
        except Exception:
            pass
        
        return None
    
    async def pin_file(self, ipfs_hash: str, service_name: Optional[str] = None) -> bool:
        """Pin file ke IPFS"""
        if service_name:
            # Pin ke service tertentu
            service = next((s for s in self.pin_services if s.name == service_name and s.is_active), None)
            if service:
                return await self._pin_to_service(ipfs_hash, service)
        else:
            # Pin ke semua active services
            success_count = 0
            for service in self.pin_services:
                if service.is_active:
                    if await self._pin_to_service(ipfs_hash, service):
                        success_count += 1
            
            return success_count > 0
        
        return False
    
    async def unpin_file(self, ipfs_hash: str, service_name: Optional[str] = None) -> bool:
        """Unpin file dari IPFS"""
        if service_name:
            # Unpin dari service tertentu
            service = next((s for s in self.pin_services if s.name == service_name and s.is_active), None)
            if service:
                return await self._unpin_from_service(ipfs_hash, service)
        else:
            # Unpin dari semua services
            success_count = 0
            for service in self.pin_services:
                if service.is_active:
                    if await self._unpin_from_service(ipfs_hash, service):
                        success_count += 1
            
            return success_count > 0
        
        return False
    
    async def get_file_stats(self, ipfs_hash: str) -> Optional[Dict]:
        """Dapatkan statistik file"""
        ipfs_file = await self.get_file(ipfs_hash, update_access=False)
        if not ipfs_file:
            return None
        
        return {
            "hash": ipfs_file.hash,
            "name": ipfs_file.name,
            "size": ipfs_file.size,
            "content_type": ipfs_file.content_type.value,
            "uploaded_at": ipfs_file.uploaded_at,
            "last_accessed": ipfs_file.last_accessed,
            "access_count": ipfs_file.access_count,
            "is_pinned": ipfs_file.is_pinned,
            "pin_services": ipfs_file.pin_services,
            "replication_factor": ipfs_file.replication_factor,
            "status": ipfs_file.status.value,
            "version": ipfs_file.version,
            "checksum": ipfs_file.checksum,
            "mime_type": ipfs_file.mime_type,
            "language": ipfs_file.language,
            "region": ipfs_file.region
        }
    
    async def search_files(
        self,
        query: str,
        content_type: Optional[ContentType] = None,
        tags: Optional[List[str]] = None,
        uploader: Optional[str] = None,
        language: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 50
    ) -> List[IPFSFile]:
        """Cari file berdasarkan query"""
        results = []
        
        # Search dalam cache dulu
        for ipfs_hash, ipfs_file in self.file_cache.items():
            if len(results) >= limit:
                break
            
            # Match query
            if query.lower() not in ipfs_file.name.lower():
                continue
            
            # Apply filters
            if content_type and ipfs_file.content_type != content_type:
                continue
            if tags and not any(tag in ipfs_file.tags for tag in tags):
                continue
            if uploader and ipfs_file.uploaded_by != uploader:
                continue
            if language and ipfs_file.language != language:
                continue
            if region and ipfs_file.region != region:
                continue
            
            results.append(ipfs_file)
        
        return results
    
    async def get_storage_metrics(self) -> StorageMetrics:
        """Dapatkan metrics untuk storage system"""
        total_files = len(self.file_cache)
        total_size = sum(file.size for file in self.file_cache.values())
        pinned_files = sum(1 for file in self.file_cache.values() if file.is_pinned)
        
        avg_replication = sum(file.replication_factor for file in self.file_cache.values()) / total_files if total_files > 0 else 0.0
        
        # Calculate content type distribution
        content_dist = {}
        for file in self.file_cache.values():
            content_type = file.content_type.value
            content_dist[content_type] = content_dist.get(content_type, 0) + 1
        
        # Calculate regional distribution
        regional_dist = {}
        for file in self.file_cache.values():
            region = file.region
            regional_dist[region] = regional_dist.get(region, 0) + 1
        
        # Calculate usage rates
        encrypted_files = sum(1 for file in self.file_cache.values() if file.encryption_key)
        compressed_files = sum(1 for file in self.file_cache.values() if file.compression_type)
        
        encryption_usage = (encrypted_files / total_files * 100) if total_files > 0 else 0.0
        compression_usage = (compressed_files / total_files * 100) if total_files > 0 else 0.0
        
        return StorageMetrics(
            total_files=total_files,
            total_size_bytes=total_size,
            pinned_files=pinned_files,
            replication_factor_average=avg_replication,
            upload_success_rate=95.0,  # Placeholder
            average_upload_time=30.0,  # Placeholder
            storage_cost_per_month=50.0,  # Placeholder
            bandwidth_usage_gb=100.0,  # Placeholder
            active_pin_services=len([s for s in self.pin_services if s.is_active]),
            failed_uploads=0,  # Placeholder
            expired_files=0,  # Placeholder
            encryption_usage_rate=encryption_usage,
            compression_usage_rate=compression_usage,
            regional_distribution=regional_dist,
            content_type_distribution=content_dist,
            version_control_efficiency=90.0  # Placeholder
        )
    
    async def cleanup_expired_files(self) -> int:
        """Bersihkan file yang sudah expired"""
        current_time = time.time()
        expired_count = 0
        
        expired_hashes = []
        for ipfs_hash, ipfs_file in self.file_cache.items():
            if ipfs_file.retention_days:
                expiration_time = ipfs_file.uploaded_at + (ipfs_file.retention_days * 24 * 3600)
                if current_time > expiration_time:
                    expired_hashes.append(ipfs_hash)
        
        # Remove expired files
        for ipfs_hash in expired_hashes:
            await self.unpin_file(ipfs_hash)
            del self.file_cache[ipfs_hash]
            expired_count += 1
        
        return expired_count
    
    # Private methods
    
    async def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum untuk file"""
        sha256_hash = hashlib.sha256()
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    async def _compress_content(self, content: bytes) -> bytes:
        """Compress content menggunakan gzip"""
        import gzip
        return gzip.compress(content)
    
    async def _encrypt_content(self, content: bytes) -> Tuple[bytes, str]:
        """Encrypt content (placeholder implementation)"""
        # In real implementation, use proper encryption like AES-256-GCM
        encryption_key = hashlib.sha256(f"key_{time.time()}".encode()).hexdigest()[:32]
        # Simple XOR encryption for demo (NOT SECURE!)
        encrypted = bytes(b ^ ord(encryption_key[0]) for b in content)
        return encrypted, encryption_key
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type untuk file"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"
    
    async def _upload_to_pin_service(self, content: bytes, file_name: str) -> str:
        """Upload ke IPFS pin service sebagai fallback"""
        # Placeholder implementation
        # In real implementation, upload to services like Pinata, Infura, etc.
        return hashlib.sha256(content).hexdigest()
    
    async def _pin_to_multiple_services(self, ipfs_hash: str, replication_factor: int):
        """Pin file ke multiple services untuk redundancy"""
        active_services = [s for s in self.pin_services if s.is_active]
        
        for i, service in enumerate(active_services[:replication_factor]):
            try:
                await self._pin_to_service(ipfs_hash, service)
            except Exception as e:
                print(f"Failed to pin to {service.name}: {e}")
    
    async def _pin_to_service(self, ipfs_hash: str, service: IPFSPinService) -> bool:
        """Pin file ke specific service"""
        # Placeholder implementation
        # In real implementation, use service-specific API
        return True
    
    async def _unpin_from_service(self, ipfs_hash: str, service: IPFSPinService) -> bool:
        """Unpin file dari specific service"""
        # Placeholder implementation
        # In real implementation, use service-specific API
        return True