"""
SANGKURIANG Decentralized Storage System
Sistem penyimpanan terdesentralisasi menggunakan IPFS untuk DAO dan komunitas
"""

import asyncio
import json
import hashlib
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import ipfshttpclient
import redis.asyncio as redis
from web3 import Web3
from eth_account import Account
import aiofiles
import os
import shutil
from pathlib import Path
import base64
import zlib
import pickle


class StorageType(Enum):
    """Jenis penyimpanan"""
    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    CODE = "code"
    DATA = "data"
    METADATA = "metadata"
    BACKUP = "backup"
    ARCHIVE = "archive"
    TEMPORARY = "temporary"


class EncryptionType(Enum):
    """Jenis enkripsi"""
    NONE = "none"
    AES256 = "aes256"
    RSA2048 = "rsa2048"
    ECC = "ecc"
    HYBRID = "hybrid"


class AccessLevel(Enum):
    """Level akses untuk file"""
    PUBLIC = "public"
    COMMUNITY = "community"
    PRIVATE = "private"
    ENCRYPTED = "encrypted"
    RESTRICTED = "restricted"


class FileStatus(Enum):
    """Status file"""
    PENDING = "pending"
    UPLOADING = "uploading"
    STORED = "stored"
    PINNED = "pinned"
    REPLICATED = "replicated"
    ARCHIVED = "archived"
    DELETED = "deleted"
    FAILED = "failed"


@dataclass
class FileMetadata:
    """Metadata untuk file"""
    filename: str
    file_hash: str
    file_size: int
    content_type: str
    storage_type: StorageType
    encryption_type: EncryptionType
    access_level: AccessLevel
    uploader_address: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    ipfs_hash: Optional[str] = None
    ipfs_path: Optional[str] = None
    ipfs_size: Optional[int] = None
    original_path: Optional[str] = None
    backup_hashes: List[str] = field(default_factory=list)
    replication_nodes: List[str] = field(default_factory=list)
    access_control: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None
    version: str = "1.0"
    checksum: Optional[str] = None
    compression_ratio: float = 0.0
    encryption_key_hash: Optional[str] = None
    thumbnail_hash: Optional[str] = None
    preview_hash: Optional[str] = None
    parent_directory: Optional[str] = None
    child_files: List[str] = field(default_factory=list)
    related_files: List[str] = field(default_factory=list)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StorageQuota:
    """Kuota penyimpanan untuk user"""
    user_address: str
    total_quota: int  # in bytes
    used_quota: int = 0
    available_quota: int = 0
    quota_type: str = "community"  # community, premium, enterprise
    quota_expiry: Optional[datetime] = None
    quota_renewal_date: Optional[datetime] = None
    quota_history: List[Dict[str, Any]] = field(default_factory=list)
    quota_overdraft_allowed: bool = False
    quota_overdraft_limit: int = 0
    quota_warnings_sent: int = 0
    
    def __post_init__(self):
        self.available_quota = self.total_quota - self.used_quota


@dataclass
class StorageNode:
    """Node penyimpanan dalam jaringan"""
    node_id: str
    node_address: str
    node_type: str  # ipfs, filecoin, arweave, custom
    node_status: str  # active, inactive, maintenance
    node_location: str
    node_capacity: int
    node_used: int = 0
    node_available: int = 0
    node_reliability: float = 0.0
    node_latency: float = 0.0
    node_bandwidth: int = 0
    node_cost_per_gb: float = 0.0
    node_encryption_supported: bool = True
    node_backup_enabled: bool = True
    node_replication_factor: int = 3
    node_last_seen: datetime = field(default_factory=datetime.now)
    node_version: str = "1.0"
    node_capabilities: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.node_available = self.node_capacity - self.node_used


@dataclass
class StorageTransaction:
    """Transaksi penyimpanan"""
    transaction_id: str
    user_address: str
    operation: str  # upload, download, delete, replicate, backup
    file_hash: str
    file_size: int
    storage_nodes: List[str]
    transaction_cost: float
    transaction_status: str
    transaction_fee: float = 0.0
    transaction_gas: int = 0
    transaction_timestamp: datetime = field(default_factory=datetime.now)
    transaction_duration: float = 0.0
    transaction_retry_count: int = 0
    transaction_error: Optional[str] = None
    transaction_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StorageMetrics:
    """Metrik sistem penyimpanan"""
    total_files: int = 0
    total_storage_used: int = 0
    total_storage_available: int = 0
    total_uploads: int = 0
    total_downloads: int = 0
    total_replications: int = 0
    total_backups: int = 0
    average_upload_time: float = 0.0
    average_download_time: float = 0.0
    average_file_size: float = 0.0
    storage_efficiency: float = 0.0
    replication_efficiency: float = 0.0
    node_health_score: float = 0.0
    data_integrity_score: float = 0.0
    cost_efficiency: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


class DecentralizedStorageSystem:
    """Sistem Penyimpanan Terdesentralisasi SANGKURIANG"""
    
    def __init__(
        self,
        ipfs_nodes: List[str],
        redis_url: str = "redis://localhost:6379",
        web3_provider: str = "https://mainnet.infura.io/v3/YOUR_PROJECT_ID",
        encryption_key: Optional[str] = None,
        backup_enabled: bool = True,
        replication_factor: int = 3,
        compression_enabled: bool = True
    ):
        # IPFS clients
        self.ipfs_clients = []
        for node in ipfs_nodes:
            try:
                client = ipfshttpclient.connect(node)
                self.ipfs_clients.append(client)
            except Exception as e:
                print(f"Failed to connect to IPFS node {node}: {e}")
        
        if not self.ipfs_clients:
            raise Exception("No IPFS nodes available")
        
        # Redis client
        self.redis_client = redis.from_url(redis_url)
        
        # Web3 integration
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))
        
        # Encryption
        self.encryption_key = encryption_key
        self.backup_enabled = backup_enabled
        self.replication_factor = replication_factor
        self.compression_enabled = compression_enabled
        
        # Storage state
        self.file_registry: Dict[str, FileMetadata] = {}
        self.user_quotas: Dict[str, StorageQuota] = {}
        self.storage_nodes: Dict[str, StorageNode] = {}
        self.transactions: Dict[str, StorageTransaction] = {}
        self.pending_operations: List[str] = []
        
        # Configuration
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.allowed_content_types = {
            'text/plain', 'text/html', 'text/css', 'text/javascript',
            'application/json', 'application/pdf', 'application/zip',
            'image/jpeg', 'image/png', 'image/gif', 'image/svg+xml',
            'video/mp4', 'video/webm', 'audio/mpeg', 'audio/wav',
            'application/octet-stream'
        }
        
        # Metrics
        self.metrics = StorageMetrics()
        
        # Monitoring
        self.monitoring_active = True
        
        # Initialize system
        asyncio.create_task(self._initialize_storage_system())
    
    async def _initialize_storage_system(self) -> None:
        """Inisialisasi sistem penyimpanan"""
        try:
            # Load existing data from Redis
            await self._load_existing_data()
            
            # Initialize storage nodes
            await self._initialize_storage_nodes()
            
            # Start monitoring
            asyncio.create_task(self._storage_monitoring_loop())
            asyncio.create_task(self._replication_monitoring_loop())
            
            print("✅ Decentralized storage system initialized")
            
        except Exception as e:
            print(f"❌ Failed to initialize storage system: {e}")
    
    async def upload_file(
        self,
        file_path: str,
        uploader_address: str,
        storage_type: StorageType,
        access_level: AccessLevel,
        encryption_type: EncryptionType = EncryptionType.NONE,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        custom_metadata: Optional[Dict[str, Any]] = None,
        private_key: str = ""
    ) -> Dict[str, Any]:
        """Unggah file ke sistem penyimpanan terdesentralisasi"""
        try:
            # Validate file
            if not os.path.exists(file_path):
                return {"success": False, "error": "File not found"}
            
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                return {"success": False, "error": "File too large"}
            
            # Check user quota
            quota_result = await self._check_user_quota(uploader_address, file_size)
            if not quota_result["allowed"]:
                return {"success": False, "error": quota_result["reason"]}
            
            # Generate file hash
            file_hash = await self._calculate_file_hash(file_path)
            
            # Check if file already exists
            if file_hash in self.file_registry:
                return {
                    "success": True,
                    "file_hash": file_hash,
                    "ipfs_hash": self.file_registry[file_hash].ipfs_hash,
                    "message": "File already exists"
                }
            
            # Process file (compress, encrypt if needed)
            processed_file_path = await self._process_file(file_path, encryption_type)
            
            # Upload to IPFS
            ipfs_result = await self._upload_to_ipfs(processed_file_path)
            if not ipfs_result["success"]:
                return {"success": False, "error": ipfs_result["error"]}
            
            # Create metadata
            metadata = FileMetadata(
                filename=os.path.basename(file_path),
                file_hash=file_hash,
                file_size=file_size,
                content_type=self._get_content_type(file_path),
                storage_type=storage_type,
                encryption_type=encryption_type,
                access_level=access_level,
                uploader_address=uploader_address,
                ipfs_hash=ipfs_result["ipfs_hash"],
                ipfs_path=ipfs_result["ipfs_path"],
                ipfs_size=ipfs_result["ipfs_size"],
                original_path=file_path,
                tags=tags or [],
                description=description,
                custom_metadata=custom_metadata or {},
                checksum=ipfs_result.get("checksum")
            )
            
            # Replicate file
            if self.backup_enabled:
                replication_result = await self._replicate_file(ipfs_result["ipfs_hash"], file_size)
                metadata.replication_nodes = replication_result["nodes"]
                metadata.backup_hashes = replication_result["backup_hashes"]
            
            # Update registry
            self.file_registry[file_hash] = metadata
            
            # Update user quota
            await self._update_user_quota(uploader_address, file_size, "upload")
            
            # Record transaction
            await self._record_transaction(
                user_address=uploader_address,
                operation="upload",
                file_hash=file_hash,
                file_size=file_size,
                storage_nodes=metadata.replication_nodes,
                transaction_cost=ipfs_result.get("cost", 0.0)
            )
            
            # Clean up processed file
            if processed_file_path != file_path:
                os.remove(processed_file_path)
            
            print(f"✅ File uploaded: {file_hash}")
            return {
                "success": True,
                "file_hash": file_hash,
                "ipfs_hash": ipfs_result["ipfs_hash"],
                "file_size": file_size,
                "replication_nodes": len(metadata.replication_nodes),
                "access_level": access_level.value
            }
            
        except Exception as e:
            print(f"❌ Failed to upload file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def download_file(
        self,
        file_hash: str,
        downloader_address: str,
        private_key: str = ""
    ) -> Dict[str, Any]:
        """Unduh file dari sistem penyimpanan"""
        try:
            # Validate file exists
            if file_hash not in self.file_registry:
                return {"success": False, "error": "File not found"}
            
            metadata = self.file_registry[file_hash]
            
            # Check access permissions
            access_result = await self._check_access_permissions(downloader_address, metadata)
            if not access_result["allowed"]:
                return {"success": False, "error": access_result["reason"]}
            
            # Download from IPFS
            download_result = await self._download_from_ipfs(metadata.ipfs_hash)
            if not download_result["success"]:
                return {"success": False, "error": download_result["error"]}
            
            # Decrypt file if encrypted
            if metadata.encryption_type != EncryptionType.NONE:
                decrypted_data = await self._decrypt_file(
                    download_result["data"],
                    metadata.encryption_type,
                    private_key
                )
                file_data = decrypted_data
            else:
                file_data = download_result["data"]
            
            # Decompress if compressed
            if metadata.compression_ratio > 0:
                file_data = zlib.decompress(file_data)
            
            # Verify integrity
            if not await self._verify_file_integrity(file_data, metadata.checksum):
                return {"success": False, "error": "File integrity verification failed"}
            
            # Record transaction
            await self._record_transaction(
                user_address=downloader_address,
                operation="download",
                file_hash=file_hash,
                file_size=len(file_data),
                storage_nodes=metadata.replication_nodes,
                transaction_cost=download_result.get("cost", 0.0)
            )
            
            print(f"✅ File downloaded: {file_hash}")
            return {
                "success": True,
                "file_data": file_data,
                "file_metadata": metadata,
                "download_time": download_result["download_time"]
            }
            
        except Exception as e:
            print(f"❌ Failed to download file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_file(
        self,
        file_hash: str,
        deleter_address: str,
        private_key: str = ""
    ) -> Dict[str, Any]:
        """Hapus file dari sistem penyimpanan"""
        try:
            # Validate file exists
            if file_hash not in self.file_registry:
                return {"success": False, "error": "File not found"}
            
            metadata = self.file_registry[file_hash]
            
            # Check deletion permissions
            if metadata.uploader_address.lower() != deleter_address.lower():
                return {"success": False, "error": "Only uploader can delete file"}
            
            # Unpin from IPFS nodes
            unpin_result = await self._unpin_from_ipfs(metadata.ipfs_hash)
            if not unpin_result["success"]:
                return {"success": False, "error": unpin_result["error"]}
            
            # Remove from backup nodes
            if metadata.backup_hashes:
                await self._remove_from_backup_nodes(metadata.backup_hashes)
            
            # Update user quota
            await self._update_user_quota(deleter_address, -metadata.file_size, "delete")
            
            # Update file status
            metadata.status = FileStatus.DELETED
            metadata.updated_at = datetime.now()
            
            # Record transaction
            await self._record_transaction(
                user_address=deleter_address,
                operation="delete",
                file_hash=file_hash,
                file_size=metadata.file_size,
                storage_nodes=metadata.replication_nodes,
                transaction_cost=unpin_result.get("cost", 0.0)
            )
            
            print(f"✅ File deleted: {file_hash}")
            return {
                "success": True,
                "file_hash": file_hash,
                "unpinned_nodes": unpin_result["unpinned_nodes"]
            }
            
        except Exception as e:
            print(f"❌ Failed to delete file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def replicate_file(
        self,
        file_hash: str,
        replicator_address: str,
        target_nodes: Optional[List[str]] = None,
        replication_factor: Optional[int] = None
    ) -> Dict[str, Any]:
        """Replikasi file ke node tambahan"""
        try:
            # Validate file exists
            if file_hash not in self.file_registry:
                return {"success": False, "error": "File not found"}
            
            metadata = self.file_registry[file_hash]
            
            # Check replication permissions
            access_result = await self._check_access_permissions(replicator_address, metadata)
            if not access_result["allowed"]:
                return {"success": False, "error": access_result["reason"]}
            
            # Perform replication
            replication_factor = replication_factor or self.replication_factor
            replication_result = await self._replicate_file(
                metadata.ipfs_hash,
                metadata.file_size,
                target_nodes,
                replication_factor
            )
            
            if not replication_result["success"]:
                return {"success": False, "error": replication_result["error"]}
            
            # Update metadata
            metadata.replication_nodes.extend(replication_result["new_nodes"])
            metadata.backup_hashes.extend(replication_result["backup_hashes"])
            metadata.updated_at = datetime.now()
            
            # Record transaction
            await self._record_transaction(
                user_address=replicator_address,
                operation="replicate",
                file_hash=file_hash,
                file_size=metadata.file_size,
                storage_nodes=replication_result["new_nodes"],
                transaction_cost=replication_result.get("cost", 0.0)
            )
            
            print(f"✅ File replicated: {file_hash}")
            return {
                "success": True,
                "file_hash": file_hash,
                "new_nodes": replication_result["new_nodes"],
                "backup_hashes": replication_result["backup_hashes"]
            }
            
        except Exception as e:
            print(f"❌ Failed to replicate file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_file_metadata(self, file_hash: str) -> Dict[str, Any]:
        """Dapatkan metadata file"""
        try:
            if file_hash not in self.file_registry:
                return {"success": False, "error": "File not found"}
            
            metadata = self.file_registry[file_hash]
            
            return {
                "success": True,
                "metadata": {
                    "filename": metadata.filename,
                    "file_hash": metadata.file_hash,
                    "file_size": metadata.file_size,
                    "content_type": metadata.content_type,
                    "storage_type": metadata.storage_type.value,
                    "encryption_type": metadata.encryption_type.value,
                    "access_level": metadata.access_level.value,
                    "uploader_address": metadata.uploader_address,
                    "created_at": metadata.created_at.isoformat(),
                    "updated_at": metadata.updated_at.isoformat(),
                    "ipfs_hash": metadata.ipfs_hash,
                    "ipfs_path": metadata.ipfs_path,
                    "ipfs_size": metadata.ipfs_size,
                    "replication_nodes": len(metadata.replication_nodes),
                    "backup_hashes": len(metadata.backup_hashes),
                    "tags": metadata.tags,
                    "description": metadata.description,
                    "version": metadata.version,
                    "checksum": metadata.checksum,
                    "compression_ratio": metadata.compression_ratio,
                    "status": getattr(metadata, 'status', FileStatus.STORED).value if hasattr(metadata, 'status') else FileStatus.STORED.value
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to get file metadata: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_user_files(
        self,
        user_address: str,
        storage_type: Optional[StorageType] = None,
        access_level: Optional[AccessLevel] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Daftar file milik user"""
        try:
            user_files = []
            
            for file_hash, metadata in self.file_registry.items():
                if metadata.uploader_address.lower() == user_address.lower():
                    # Filter by storage type
                    if storage_type and metadata.storage_type != storage_type:
                        continue
                    
                    # Filter by access level
                    if access_level and metadata.access_level != access_level:
                        continue
                    
                    user_files.append({
                        "file_hash": file_hash,
                        "filename": metadata.filename,
                        "file_size": metadata.file_size,
                        "content_type": metadata.content_type,
                        "storage_type": metadata.storage_type.value,
                        "access_level": metadata.access_level.value,
                        "created_at": metadata.created_at.isoformat(),
                        "ipfs_hash": metadata.ipfs_hash,
                        "tags": metadata.tags,
                        "description": metadata.description
                    })
            
            # Apply pagination
            total_files = len(user_files)
            paginated_files = user_files[offset:offset + limit]
            
            return {
                "success": True,
                "files": paginated_files,
                "total_files": total_files,
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            print(f"❌ Failed to list user files: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_storage_metrics(self) -> Dict[str, Any]:
        """Dapatkan metrik sistem penyimpanan"""
        try:
            await self._update_storage_metrics()
            
            return {
                "success": True,
                "metrics": {
                    "total_files": self.metrics.total_files,
                    "total_storage_used": self.metrics.total_storage_used,
                    "total_storage_available": self.metrics.total_storage_available,
                    "total_uploads": self.metrics.total_uploads,
                    "total_downloads": self.metrics.total_downloads,
                    "total_replications": self.metrics.total_replications,
                    "total_backups": self.metrics.total_backups,
                    "average_upload_time": self.metrics.average_upload_time,
                    "average_download_time": self.metrics.average_download_time,
                    "average_file_size": self.metrics.average_file_size,
                    "storage_efficiency": self.metrics.storage_efficiency,
                    "replication_efficiency": self.metrics.replication_efficiency,
                    "node_health_score": self.metrics.node_health_score,
                    "data_integrity_score": self.metrics.data_integrity_score,
                    "cost_efficiency": self.metrics.cost_efficiency,
                    "last_updated": self.metrics.last_updated.isoformat()
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to get storage metrics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Helper methods
    async def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate file hash"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256()
                while chunk := f.read(8192):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except Exception as e:
            print(f"Error calculating file hash: {e}")
            return ""
    
    async def _process_file(self, file_path: str, encryption_type: EncryptionType) -> str:
        """Process file (compress, encrypt)"""
        try:
            # Read file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Compress if enabled
            if self.compression_enabled and len(file_data) > 1024:  # Only compress files > 1KB
                compressed_data = zlib.compress(file_data)
                if len(compressed_data) < len(file_data):
                    file_data = compressed_data
            
            # Encrypt if needed
            if encryption_type != EncryptionType.NONE:
                # In a real implementation, you would encrypt the file data
                # For now, we'll just return the processed path
                pass
            
            # Write processed file
            processed_path = f"{file_path}.processed"
            with open(processed_path, 'wb') as f:
                f.write(file_data)
            
            return processed_path
            
        except Exception as e:
            print(f"Error processing file: {e}")
            return file_path
    
    async def _upload_to_ipfs(self, file_path: str) -> Dict[str, Any]:
        """Upload file to IPFS"""
        try:
            if not self.ipfs_clients:
                return {"success": False, "error": "No IPFS nodes available"}
            
            # Use first available client
            client = self.ipfs_clients[0]
            
            # Upload file
            result = client.add(file_path)
            
            return {
                "success": True,
                "ipfs_hash": result["Hash"],
                "ipfs_path": result["Name"],
                "ipfs_size": result["Size"],
                "cost": 0.0  # IPFS is free for now
            }
            
        except Exception as e:
            print(f"Error uploading to IPFS: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _download_from_ipfs(self, ipfs_hash: str) -> Dict[str, Any]:
        """Download file from IPFS"""
        try:
            if not self.ipfs_clients:
                return {"success": False, "error": "No IPFS nodes available"}
            
            # Use first available client
            client = self.ipfs_clients[0]
            
            # Download file
            start_time = time.time()
            data = client.cat(ipfs_hash)
            download_time = time.time() - start_time
            
            return {
                "success": True,
                "data": data,
                "download_time": download_time,
                "cost": 0.0
            }
            
        except Exception as e:
            print(f"Error downloading from IPFS: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _unpin_from_ipfs(self, ipfs_hash: str) -> Dict[str, Any]:
        """Unpin file from IPFS"""
        try:
            unpinned_nodes = []
            
            for client in self.ipfs_clients:
                try:
                    client.pin.rm(ipfs_hash)
                    unpinned_nodes.append("node_address")
                except Exception as e:
                    print(f"Error unpinning from IPFS node: {e}")
            
            return {
                "success": True,
                "unpinned_nodes": unpinned_nodes,
                "cost": 0.0
            }
            
        except Exception as e:
            print(f"Error unpinning from IPFS: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _replicate_file(
        self,
        ipfs_hash: str,
        file_size: int,
        target_nodes: Optional[List[str]] = None,
        replication_factor: int = 3
    ) -> Dict[str, Any]:
        """Replicate file to additional nodes"""
        try:
            # In a real implementation, this would replicate to multiple IPFS nodes
            # For now, we'll simulate replication
            new_nodes = ["node1", "node2", "node3"]
            backup_hashes = [f"backup_{ipfs_hash}_{i}" for i in range(replication_factor)]
            
            return {
                "success": True,
                "new_nodes": new_nodes[:replication_factor],
                "backup_hashes": backup_hashes[:replication_factor],
                "cost": 0.0
            }
            
        except Exception as e:
            print(f"Error replicating file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _check_user_quota(self, user_address: str, file_size: int) -> Dict[str, Any]:
        """Check user storage quota"""
        try:
            if user_address not in self.user_quotas:
                # Create default quota (1GB)
                self.user_quotas[user_address] = StorageQuota(
                    user_address=user_address,
                    total_quota=1024 * 1024 * 1024  # 1GB
                )
            
            quota = self.user_quotas[user_address]
            
            if quota.used_quota + file_size > quota.total_quota:
                return {
                    "allowed": False,
                    "reason": "Storage quota exceeded"
                }
            
            return {
                "allowed": True,
                "reason": ""
            }
            
        except Exception as e:
            print(f"Error checking user quota: {e}")
            return {
                "allowed": False,
                "reason": "Quota check failed"
            }
    
    async def _update_user_quota(self, user_address: str, size_change: int, operation: str) -> None:
        """Update user storage quota"""
        try:
            if user_address not in self.user_quotas:
                self.user_quotas[user_address] = StorageQuota(
                    user_address=user_address,
                    total_quota=1024 * 1024 * 1024  # 1GB
                )
            
            quota = self.user_quotas[user_address]
            quota.used_quota += size_change
            quota.available_quota = quota.total_quota - quota.used_quota
            
            # Record quota history
            quota.quota_history.append({
                "operation": operation,
                "size_change": size_change,
                "timestamp": datetime.now().isoformat(),
                "used_quota": quota.used_quota
            })
            
        except Exception as e:
            print(f"Error updating user quota: {e}")
    
    async def _check_access_permissions(self, user_address: str, metadata: FileMetadata) -> Dict[str, Any]:
        """Check file access permissions"""
        try:
            if metadata.access_level == AccessLevel.PUBLIC:
                return {"allowed": True, "reason": ""}
            
            if metadata.access_level == AccessLevel.COMMUNITY:
                # Check if user is in community
                # For now, we'll allow all authenticated users
                return {"allowed": True, "reason": ""}
            
            if metadata.access_level == AccessLevel.PRIVATE:
                if user_address.lower() == metadata.uploader_address.lower():
                    return {"allowed": True, "reason": ""}
                else:
                    return {"allowed": False, "reason": "Access denied"}
            
            if metadata.access_level == AccessLevel.ENCRYPTED:
                # Additional encryption checks would go here
                return {"allowed": True, "reason": ""}
            
            return {"allowed": False, "reason": "Unknown access level"}
            
        except Exception as e:
            print(f"Error checking access permissions: {e}")
            return {
                "allowed": False,
                "reason": "Permission check failed"
            }
    
    async def _record_transaction(
        self,
        user_address: str,
        operation: str,
        file_hash: str,
        file_size: int,
        storage_nodes: List[str],
        transaction_cost: float
    ) -> None:
        """Record storage transaction"""
        try:
            transaction_id = hashlib.sha256(
                f"{user_address}:{operation}:{file_hash}:{time.time()}".encode()
            ).hexdigest()
            
            transaction = StorageTransaction(
                transaction_id=transaction_id,
                user_address=user_address,
                operation=operation,
                file_hash=file_hash,
                file_size=file_size,
                storage_nodes=storage_nodes,
                transaction_cost=transaction_cost,
                transaction_status="completed"
            )
            
            self.transactions[transaction_id] = transaction
            
            # Update metrics
            if operation == "upload":
                self.metrics.total_uploads += 1
            elif operation == "download":
                self.metrics.total_downloads += 1
            elif operation == "replicate":
                self.metrics.total_replications += 1
            
        except Exception as e:
            print(f"Error recording transaction: {e}")
    
    async def _verify_file_integrity(self, file_data: bytes, expected_checksum: str) -> bool:
        """Verify file integrity"""
        try:
            if not expected_checksum:
                return True  # No checksum to verify against
            
            actual_checksum = hashlib.sha256(file_data).hexdigest()
            return actual_checksum == expected_checksum
            
        except Exception as e:
            print(f"Error verifying file integrity: {e}")
            return False
    
    def _get_content_type(self, file_path: str) -> str:
        """Get file content type"""
        try:
            import mimetypes
            content_type, _ = mimetypes.guess_type(file_path)
            return content_type or "application/octet-stream"
        except:
            return "application/octet-stream"
    
    async def _update_storage_metrics(self) -> None:
        """Update storage metrics"""
        try:
            self.metrics.total_files = len(self.file_registry)
            self.metrics.total_storage_used = sum(
                metadata.file_size for metadata in self.file_registry.values()
            )
            
            # Calculate average file size
            if self.metrics.total_files > 0:
                self.metrics.average_file_size = self.metrics.total_storage_used / self.metrics.total_files
            
            # Calculate storage efficiency
            if self.metrics.total_storage_used > 0:
                self.metrics.storage_efficiency = len([f for f in self.file_registry.values() if f.replication_nodes]) / self.metrics.total_files
            
            self.metrics.last_updated = datetime.now()
            
        except Exception as e:
            print(f"Error updating storage metrics: {e}")
    
    async def _initialize_storage_nodes(self) -> None:
        """Initialize storage nodes"""
        try:
            # Add IPFS nodes as storage nodes
            for i, client in enumerate(self.ipfs_clients):
                node = StorageNode(
                    node_id=f"ipfs_node_{i}",
                    node_address=f"ipfs://localhost:500{i+1}",
                    node_type="ipfs",
                    node_status="active",
                    node_location="local",
                    node_capacity=1000 * 1024 * 1024 * 1024,  # 1TB
                    node_reliability=0.95,
                    node_latency=50.0,
                    node_bandwidth=1000,  # Mbps
                    node_cost_per_gb=0.0,  # Free for now
                    node_capabilities=["ipfs", "pinning", "replication"]
                )
                
                self.storage_nodes[node.node_id] = node
            
        except Exception as e:
            print(f"Error initializing storage nodes: {e}")
    
    async def _load_existing_data(self) -> None:
        """Load existing data from Redis"""
        try:
            # Load file registry
            registry_data = await self.redis_client.get("file_registry")
            if registry_data:
                self.file_registry = pickle.loads(registry_data)
            
            # Load user quotas
            quotas_data = await self.redis_client.get("user_quotas")
            if quotas_data:
                self.user_quotas = pickle.loads(quotas_data)
            
        except Exception as e:
            print(f"Error loading existing data: {e}")
    
    async def _storage_monitoring_loop(self) -> None:
        """Storage monitoring loop"""
        while self.monitoring_active:
            try:
                await self._update_storage_metrics()
                await self._check_node_health()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                print(f"Storage monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _replication_monitoring_loop(self) -> None:
        """Replication monitoring loop"""
        while self.monitoring_active:
            try:
                await self._check_replication_health()
                await asyncio.sleep(1800)  # Check every 30 minutes
            except Exception as e:
                print(f"Replication monitoring error: {e}")
                await asyncio.sleep(300)
    
    async def _check_node_health(self) -> None:
        """Check storage node health"""
        try:
            for node in self.storage_nodes.values():
                # Simple health check - in real implementation, you'd ping the node
                node.node_last_seen = datetime.now()
                node.node_reliability = 0.95  # Mock reliability
            
        except Exception as e:
            print(f"Error checking node health: {e}")
    
    async def _check_replication_health(self) -> None:
        """Check replication health"""
        try:
            for file_hash, metadata in self.file_registry.items():
                if len(metadata.replication_nodes) < self.replication_factor:
                    # Trigger additional replication
                    await self.replicate_file(
                        file_hash=file_hash,
                        replicator_address="system",
                        replication_factor=self.replication_factor - len(metadata.replication_nodes)
                    )
            
        except Exception as e:
            print(f"Error checking replication health: {e}")


# Example usage and testing
async def test_decentralized_storage_system():
    """Test SANGKURIANG Decentralized Storage System"""
    print("🚀 Testing SANGKURIANG Decentralized Storage System")
    
    # Initialize system
    storage_system = DecentralizedStorageSystem(
        ipfs_nodes=["/ip4/127.0.0.1/tcp/5001/http"],
        backup_enabled=True,
        replication_factor=3,
        compression_enabled=True
    )
    
    # Create test files
    test_files = [
        {
            "filename": "proposal_document.pdf",
            "content": b"This is a test proposal document for SANGKURIANG DAO.",
            "storage_type": StorageType.DOCUMENT,
            "access_level": AccessLevel.COMMUNITY,
            "encryption_type": EncryptionType.NONE
        },
        {
            "filename": "smart_contract.sol",
            "content": b"pragma solidity ^0.8.0; contract TestContract { }",
            "storage_type": StorageType.CODE,
            "access_level": AccessLevel.PUBLIC,
            "encryption_type": EncryptionType.NONE
        },
        {
            "filename": "community_image.png",
            "content": b"fake_image_data_for_testing_purposes_only",
            "storage_type": StorageType.IMAGE,
            "access_level": AccessLevel.PUBLIC,
            "encryption_type": EncryptionType.NONE
        }
    ]
    
    uploaded_files = []
    user_address = "0x1111111111111111111111111111111111111111"
    
    # Upload files
    for test_file in test_files:
        # Create temporary file
        temp_path = f"/tmp/{test_file['filename']}"
        with open(temp_path, 'wb') as f:
            f.write(test_file['content'])
        
        # Upload to storage
        result = await storage_system.upload_file(
            file_path=temp_path,
            uploader_address=user_address,
            storage_type=test_file['storage_type'],
            access_level=test_file['access_level'],
            encryption_type=test_file['encryption_type'],
            tags=["test", "sangkuriang", "dao"],
            description=f"Test file: {test_file['filename']}"
        )
        
        if result["success"]:
            uploaded_files.append(result["file_hash"])
            print(f"✅ Uploaded: {test_file['filename']} -> {result['file_hash']}")
        
        # Clean up temp file
        os.remove(temp_path)
    
    # Get file metadata
    for file_hash in uploaded_files:
        metadata_result = await storage_system.get_file_metadata(file_hash)
        if metadata_result["success"]:
            print(f"📄 Metadata for {file_hash}:")
            print(json.dumps(metadata_result["metadata"], indent=2, default=str))
    
    # List user files
    user_files_result = await storage_system.list_user_files(user_address)
    if user_files_result["success"]:
        print(f"📁 User files: {len(user_files_result['files'])} files")
        for file_info in user_files_result["files"]:
            print(f"  - {file_info['filename']} ({file_info['file_size']} bytes)")
    
    # Download files
    for file_hash in uploaded_files:
        download_result = await storage_system.download_file(
            file_hash=file_hash,
            downloader_address=user_address
        )
        
        if download_result["success"]:
            print(f"✅ Downloaded: {file_hash} ({len(download_result['file_data'])} bytes)")
    
    # Replicate files
    for file_hash in uploaded_files:
        replicate_result = await storage_system.replicate_file(
            file_hash=file_hash,
            replicator_address=user_address,
            replication_factor=2
        )
        
        if replicate_result["success"]:
            print(f"✅ Replicated: {file_hash} to {len(replicate_result['new_nodes'])} nodes")
    
    # Get storage metrics
    metrics_result = await storage_system.get_storage_metrics()
    if metrics_result["success"]:
        print(f"📊 Storage Metrics:")
        print(json.dumps(metrics_result["metrics"], indent=2, default=str))
    
    print("\n🎉 Decentralized storage system test completed!")


if __name__ == "__main__":
    asyncio.run(test_decentralized_storage_system())