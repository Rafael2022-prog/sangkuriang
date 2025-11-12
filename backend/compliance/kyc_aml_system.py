"""
KYC/AML System untuk SANGKURIANG
Sistem verifikasi identitas dan anti pencucian uang untuk kepatuhan regulasi
"""

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import aiohttp
import asyncio
from pathlib import Path


class VerificationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class DocumentType(Enum):
    KTP = "ktp"
    SIM = "sim"
    PASSPORT = "passport"
    NPWP = "npwp"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PROHIBITED = "prohibited"


@dataclass
class UserIdentity:
    user_id: str
    full_name: str
    date_of_birth: str
    nationality: str
    address: str
    phone_number: str
    email: str
    document_type: DocumentType
    document_number: str
    document_expiry: str
    selfie_photo: str  # Base64 encoded
    document_photo: str  # Base64 encoded
    created_at: datetime
    updated_at: datetime


@dataclass
class AMLCheck:
    check_id: str
    user_id: str
    risk_level: RiskLevel
    sanctions_check: bool
    pep_check: bool  # Politically Exposed Person
    adverse_media_check: bool
    transaction_monitoring: bool
    risk_score: float
    created_at: datetime


@dataclass
class VerificationResult:
    verification_id: str
    user_id: str
    status: VerificationStatus
    identity_verified: bool
    aml_check_passed: bool
    risk_level: RiskLevel
    rejection_reason: Optional[str]
    verified_at: Optional[datetime]
    expires_at: datetime


class DocumentVerification:
    """Verifikasi dokumen identitas menggunakan OCR dan validasi"""
    
    def __init__(self):
        self.supported_documents = [DocumentType.KTP, DocumentType.SIM, DocumentType.PASSPORT]
    
    async def verify_document(self, document_photo: str, document_type: DocumentType) -> Dict[str, Any]:
        """
        Verifikasi dokumen menggunakan OCR dan validasi format
        """
        try:
            # Simulasi OCR dan validasi dokumen
            # Dalam implementasi nyata, ini akan menggunakan layanan OCR seperti Google Vision API
            
            validation_result = {
                "valid": True,
                "confidence": 0.95,
                "extracted_data": {
                    "name": "JOHN DOE",
                    "document_number": "1234567890123456",
                    "date_of_birth": "1990-01-01",
                    "expiry_date": "2030-01-01",
                    "nationality": "ID"
                },
                "security_features": {
                    "hologram_detected": True,
                    "watermark_valid": True,
                    "microprint_valid": True
                }
            }
            
            return validation_result
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "confidence": 0.0
            }
    
    async def verify_selfie(self, selfie_photo: str, document_photo: str) -> Dict[str, Any]:
        """
        Verifikasi selfie dengan foto dokumen menggunakan face recognition
        """
        try:
            # Simulasi face recognition
            # Dalam implementasi nyata, ini akan menggunakan layanan seperti AWS Rekognition
            
            similarity_score = 0.92  # Simulasi tingkat kemiripan wajah
            
            return {
                "match": similarity_score > 0.85,
                "similarity_score": similarity_score,
                "liveness_detected": True,
                "confidence": 0.88
            }
            
        except Exception as e:
            return {
                "match": False,
                "error": str(e),
                "confidence": 0.0
            }


class AMLScreening:
    """Pemeriksaan Anti Pencucian Uang (AML)"""
    
    def __init__(self):
        self.sanctions_list = self._load_sanctions_list()
        self.pep_list = self._load_pep_list()
        self.adverse_media_keywords = self._load_adverse_media_keywords()
    
    def _load_sanctions_list(self) -> List[str]:
        """Load daftar sanksi dari berbagai sumber"""
        # Simulasi daftar sanksi (dalam implementasi nyata akan diambil dari API resmi)
        return [
            "SUDIRMAN",
            "SUKARNO",
            "SUSILO",
            # ... daftar nama yang disanksi
        ]
    
    def _load_pep_list(self) -> List[str]:
        """Load daftar Politically Exposed Person"""
        # Simulasi daftar PEP
        return [
            "PRESIDEN",
            "MENTERI",
            "GUBERNUR",
            "BUPATI",
            "WALIKOTA",
            # ... daftar PEP
        ]
    
    def _load_adverse_media_keywords(self) -> List[str]:
        """Load kata kunci untuk adverse media screening"""
        return [
            "KORUPSI",
            "PENIPUAN",
            "PENCUCIAN UANG",
            "TERORISME",
            "NARKOBA",
            "PENYELUNDUPAN"
        ]
    
    async def check_sanctions(self, name: str, date_of_birth: str) -> Dict[str, Any]:
        """Pemeriksaan terhadap daftar sanksi"""
        name_upper = name.upper()
        
        sanctions_match = any(sanction in name_upper for sanction in self.sanctions_list)
        
        return {
            "match_found": sanctions_match,
            "risk_score": 100 if sanctions_match else 0,
            "details": "Sanctions match found" if sanctions_match else "No sanctions match"
        }
    
    async def check_pep(self, name: str, nationality: str) -> Dict[str, Any]:
        """Pemeriksaan terhadap daftar PEP"""
        name_upper = name.upper()
        
        pep_match = any(pep in name_upper for pep in self.pep_list)
        
        return {
            "match_found": pep_match,
            "risk_score": 50 if pep_match else 0,
            "details": "PEP match found" if pep_match else "No PEP match",
            "enhanced_due_diligence_required": pep_match
        }
    
    async def check_adverse_media(self, name: str) -> Dict[str, Any]:
        """Pemeriksaan terhadap media negatif"""
        name_upper = name.upper()
        
        adverse_matches = [keyword for keyword in self.adverse_media_keywords if keyword in name_upper]
        
        risk_score = len(adverse_matches) * 25  # Setiap match memberikan 25 poin risiko
        risk_score = min(risk_score, 100)  # Maksimal 100
        
        return {
            "match_found": len(adverse_matches) > 0,
            "risk_score": risk_score,
            "keywords_matched": adverse_matches,
            "details": f"Found {len(adverse_matches)} adverse keywords"
        }
    
    async def calculate_overall_risk_score(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Menghitung skor risiko keseluruhan"""
        sanctions_result = await self.check_sanctions(user_data["name"], user_data["date_of_birth"])
        pep_result = await self.check_pep(user_data["name"], user_data["nationality"])
        adverse_result = await self.check_adverse_media(user_data["name"])
        
        # Hitung rata-rata tertimbang dari berbagai pemeriksaan
        total_risk_score = (
            sanctions_result["risk_score"] * 0.4 +  # Sanksi memiliki bobot tertinggi
            pep_result["risk_score"] * 0.3 +       # PEP memiliki bobot menengah
            adverse_result["risk_score"] * 0.3     # Adverse media memiliki bobot menengah
        )
        
        # Tentukan level risiko berdasarkan skor
        if total_risk_score >= 80:
            risk_level = RiskLevel.PROHIBITED
        elif total_risk_score >= 60:
            risk_level = RiskLevel.HIGH
        elif total_risk_score >= 30:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        return {
            "overall_risk_score": total_risk_score,
            "risk_level": risk_level,
            "sanctions_check": sanctions_result,
            "pep_check": pep_result,
            "adverse_media_check": adverse_result
        }


class TransactionMonitoring:
    """Pemantauan transaksi untuk deteksi aktivitas mencurigakan"""
    
    def __init__(self):
        self.suspicious_patterns = self._load_suspicious_patterns()
        self.thresholds = {
            "large_transaction": 100000000,  # Rp 100 juta
            "rapid_transactions": 5,  # 5 transaksi dalam 1 jam
            "unusual_frequency": 10  # 10 transaksi dalam 1 hari
        }
    
    def _load_suspicious_patterns(self) -> List[Dict[str, Any]]:
        """Load pola transaksi mencurigakan"""
        return [
            {
                "name": "structuring",
                "description": "Pecah transaksi besar menjadi transaksi kecil",
                "condition": lambda transactions: self._check_structuring(transactions)
            },
            {
                "name": "rapid_movement",
                "description": "Dana masuk dan keluar dengan cepat",
                "condition": lambda transactions: self._check_rapid_movement(transactions)
            },
            {
                "name": "unusual_frequency",
                "description": "Frekuensi transaksi tidak biasa",
                "condition": lambda transactions: self._check_unusual_frequency(transactions)
            }
        ]
    
    def _check_structuring(self, transactions: List[Dict[str, Any]]) -> bool:
        """Cek pola structuring (pecah transaksi)"""
        if len(transactions) < 3:
            return False
        
        # Cek apakah ada beberapa transaksi kecil dalam waktu singkat
        recent_transactions = [t for t in transactions if 
                             (datetime.now() - datetime.fromisoformat(t["timestamp"])).total_seconds() < 3600]
        
        if len(recent_transactions) < 3:
            return False
        
        amounts = [t["amount"] for t in recent_transactions]
        avg_amount = sum(amounts) / len(amounts)
        
        # Jika rata-rata transaksi kecil dan jumlahnya banyak, bisa jadi structuring
        return avg_amount < (self.thresholds["large_transaction"] / 10) and len(recent_transactions) >= 5
    
    def _check_rapid_movement(self, transactions: List[Dict[str, Any]]) -> bool:
        """Cek pergerakan dana yang cepat"""
        if len(transactions) < 2:
            return False
        
        # Sortir berdasarkan waktu
        sorted_transactions = sorted(transactions, key=lambda x: x["timestamp"])
        
        for i in range(len(sorted_transactions) - 1):
            current = sorted_transactions[i]
            next_trans = sorted_transactions[i + 1]
            
            # Jika ada transaksi masuk lalu keluar dalam waktu singkat
            if (current["type"] == "credit" and next_trans["type"] == "debit" and
                (datetime.fromisoformat(next_trans["timestamp"]) - 
                 datetime.fromisoformat(current["timestamp"])).total_seconds() < 300):  # 5 menit
                return True
        
        return False
    
    def _check_unusual_frequency(self, transactions: List[Dict[str, Any]]) -> bool:
        """Cek frekuensi transaksi yang tidak biasa"""
        # Hitung transaksi dalam 24 jam terakhir
        recent_transactions = [t for t in transactions if 
                           (datetime.now() - datetime.fromisoformat(t["timestamp"])).total_seconds() < 86400]
        
        return len(recent_transactions) > self.thresholds["unusual_frequency"]
    
    async def analyze_transactions(self, user_id: str, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analisis transaksi untuk mendeteksi aktivitas mencurigakan"""
        suspicious_activities = []
        
        for pattern in self.suspicious_patterns:
            if pattern["condition"](transactions):
                suspicious_activities.append({
                    "pattern": pattern["name"],
                    "description": pattern["description"],
                    "severity": "high"
                })
        
        # Hitung statistik transaksi
        total_transactions = len(transactions)
        total_amount = sum(t["amount"] for t in transactions)
        avg_transaction = total_amount / total_transactions if total_transactions > 0 else 0
        
        return {
            "suspicious_activities": suspicious_activities,
            "total_transactions": total_transactions,
            "total_amount": total_amount,
            "average_transaction": avg_transaction,
            "risk_indicators": len(suspicious_activities),
            "monitoring_required": len(suspicious_activities) > 0
        }


class KYCAMLSystem:
    """Sistem utama KYC/AML untuk SANGKURIANG"""
    
    def __init__(self, storage_path: str = "kyc_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        self.document_verification = DocumentVerification()
        self.aml_screening = AMLScreening()
        self.transaction_monitoring = TransactionMonitoring()
        
        # Database sederhana untuk menyimpan data
        self.users_db = {}
        self.verifications_db = {}
        self.aml_checks_db = {}
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        return str(uuid.uuid4())
    
    def _save_to_storage(self, data: Dict[str, Any], filename: str):
        """Simpan data ke file"""
        filepath = self.storage_path / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _load_from_storage(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load data dari file"""
        filepath = self.storage_path / filename
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
        return None
    
    async def submit_kyc_application(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit aplikasi KYC baru
        """
        try:
            # Validasi input
            required_fields = ["full_name", "date_of_birth", "nationality", "address", 
                             "phone_number", "email", "document_type", "document_number", 
                             "document_expiry", "selfie_photo", "document_photo"]
            
            for field in required_fields:
                if field not in user_data:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }
            
            # Generate user ID
            user_id = self._generate_id()
            
            # Buat objek identitas
            identity = UserIdentity(
                user_id=user_id,
                full_name=user_data["full_name"],
                date_of_birth=user_data["date_of_birth"],
                nationality=user_data["nationality"],
                address=user_data["address"],
                phone_number=user_data["phone_number"],
                email=user_data["email"],
                document_type=DocumentType(user_data["document_type"]),
                document_number=user_data["document_number"],
                document_expiry=user_data["document_expiry"],
                selfie_photo=user_data["selfie_photo"],
                document_photo=user_data["document_photo"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Simpan data user
            self.users_db[user_id] = identity
            self._save_to_storage(asdict(identity), f"user_{user_id}.json")
            
            # Mulai proses verifikasi
            verification_result = await self.verify_user(user_id)
            
            return {
                "success": True,
                "user_id": user_id,
                "verification_id": verification_result["verification_id"],
                "status": verification_result["status"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def verify_user(self, user_id: str) -> Dict[str, Any]:
        """
        Verifikasi user secara menyeluruh (KYC + AML)
        """
        try:
            if user_id not in self.users_db:
                return {
                    "success": False,
                    "error": "User not found"
                }
            
            user = self.users_db[user_id]
            verification_id = self._generate_id()
            
            # 1. Verifikasi dokumen
            document_result = await self.document_verification.verify_document(
                user.document_photo, user.document_type
            )
            
            # 2. Verifikasi selfie
            selfie_result = await self.document_verification.verify_selfie(
                user.selfie_photo, user.document_photo
            )
            
            # 3. Pemeriksaan AML
            aml_data = {
                "name": user.full_name,
                "date_of_birth": user.date_of_birth,
                "nationality": user.nationality
            }
            
            aml_result = await self.aml_screening.calculate_overall_risk_score(aml_data)
            
            # 4. Tentukan status verifikasi
            identity_verified = (
                document_result.get("valid", False) and 
                selfie_result.get("match", False) and
                document_result.get("confidence", 0) > 0.8 and
                selfie_result.get("confidence", 0) > 0.8
            )
            
            aml_check_passed = aml_result["risk_level"] != RiskLevel.PROHIBITED
            
            # 5. Buat hasil verifikasi
            if identity_verified and aml_check_passed:
                status = VerificationStatus.VERIFIED
                rejection_reason = None
                verified_at = datetime.now()
            else:
                status = VerificationStatus.REJECTED
                rejection_reason = []
                if not identity_verified:
                    rejection_reason.append("Identity verification failed")
                if not aml_check_passed:
                    rejection_reason.append("AML check failed - High risk")
                rejection_reason = "; ".join(rejection_reason)
                verified_at = None
            
            # 6. Simpan hasil verifikasi
            verification_result = VerificationResult(
                verification_id=verification_id,
                user_id=user_id,
                status=status,
                identity_verified=identity_verified,
                aml_check_passed=aml_check_passed,
                risk_level=aml_result["risk_level"],
                rejection_reason=rejection_reason,
                verified_at=verified_at,
                expires_at=datetime.now() + timedelta(days=365)  # Valid 1 tahun
            )
            
            self.verifications_db[verification_id] = verification_result
            self._save_to_storage(asdict(verification_result), f"verification_{verification_id}.json")
            
            # 7. Simpan hasil AML check
            aml_check = AMLCheck(
                check_id=self._generate_id(),
                user_id=user_id,
                risk_level=aml_result["risk_level"],
                sanctions_check=aml_result["sanctions_check"]["match_found"],
                pep_check=aml_result["pep_check"]["match_found"],
                adverse_media_check=aml_result["adverse_media_check"]["match_found"],
                transaction_monitoring=False,  # Akan diupdate saat ada transaksi
                risk_score=aml_result["overall_risk_score"],
                created_at=datetime.now()
            )
            
            self.aml_checks_db[user_id] = aml_check
            self._save_to_storage(asdict(aml_check), f"aml_check_{user_id}.json")
            
            return {
                "success": True,
                "verification_id": verification_id,
                "status": status.value,
                "identity_verified": identity_verified,
                "aml_check_passed": aml_check_passed,
                "risk_level": aml_result["risk_level"].value,
                "rejection_reason": rejection_reason,
                "document_verification": document_result,
                "selfie_verification": selfie_result,
                "aml_screening": aml_result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def monitor_transaction(self, user_id: str, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pantau transaksi untuk deteksi aktivitas mencurigakan
        """
        try:
            # Ambil riwayat transaksi user
            user_transactions = self._get_user_transactions(user_id)
            user_transactions.append(transaction_data)
            
            # Analisis transaksi
            analysis_result = await self.transaction_monitoring.analyze_transactions(
                user_id, user_transactions
            )
            
            # Update status monitoring di AML check
            if user_id in self.aml_checks_db:
                aml_check = self.aml_checks_db[user_id]
                aml_check.transaction_monitoring = analysis_result["monitoring_required"]
                self._save_to_storage(asdict(aml_check), f"aml_check_{user_id}.json")
            
            return {
                "success": True,
                "monitoring_required": analysis_result["monitoring_required"],
                "suspicious_activities": analysis_result["suspicious_activities"],
                "risk_indicators": analysis_result["risk_indicators"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_user_transactions(self, user_id: str) -> List[Dict[str, Any]]:
        """Ambil riwayat transaksi user (simulasi)"""
        # Dalam implementasi nyata, ini akan mengambil data dari database transaksi
        return []
    
    def get_verification_status(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Dapatkan status verifikasi user"""
        for verification in self.verifications_db.values():
            if verification.user_id == user_id:
                return {
                    "verification_id": verification.verification_id,
                    "status": verification.status.value,
                    "identity_verified": verification.identity_verified,
                    "aml_check_passed": verification.aml_check_passed,
                    "risk_level": verification.risk_level.value,
                    "rejection_reason": verification.rejection_reason,
                    "verified_at": verification.verified_at,
                    "expires_at": verification.expires_at
                }
        return None
    
    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate laporan kepatuhan"""
        total_users = len(self.users_db)
        total_verifications = len(self.verifications_db)
        
        status_counts = {}
        risk_level_counts = {}
        
        for verification in self.verifications_db.values():
            status_counts[verification.status.value] = status_counts.get(verification.status.value, 0) + 1
            risk_level_counts[verification.risk_level.value] = risk_level_counts.get(verification.risk_level.value, 0) + 1
        
        return {
            "total_users": total_users,
            "total_verifications": total_verifications,
            "verification_status_breakdown": status_counts,
            "risk_level_breakdown": risk_level_counts,
            "compliance_rate": (status_counts.get("verified", 0) / total_verifications * 100) if total_verifications > 0 else 0,
            "report_generated_at": datetime.now()
        }


# Contoh penggunaan
async def main():
    """Demo penggunaan KYC/AML System"""
    
    # Inisialisasi sistem
    kyc_system = KYCAMLSystem()
    
    # Data dummy untuk testing
    test_user_data = {
        "full_name": "John Doe",
        "date_of_birth": "1990-01-01",
        "nationality": "ID",
        "address": "Jl. Sudirman No. 123, Jakarta",
        "phone_number": "+6281234567890",
        "email": "john.doe@example.com",
        "document_type": "ktp",
        "document_number": "1234567890123456",
        "document_expiry": "2030-01-01",
        "selfie_photo": "base64_encoded_selfie_photo",
        "document_photo": "base64_encoded_document_photo"
    }
    
    print("=== SANGKURIANG KYC/AML System Demo ===\n")
    
    # 1. Submit KYC application
    print("1. Submitting KYC application...")
    result = await kyc_system.submit_kyc_application(test_user_data)
    
    if result["success"]:
        user_id = result["user_id"]
        verification_id = result["verification_id"]
        print(f"   ✓ KYC application submitted successfully")
        print(f"   - User ID: {user_id}")
        print(f"   - Verification ID: {verification_id}")
        print(f"   - Status: {result['status']}")
    else:
        print(f"   ✗ Failed to submit KYC application: {result['error']}")
        return
    
    print()
    
    # 2. Get verification status
    print("2. Getting verification status...")
    status = kyc_system.get_verification_status(user_id)
    
    if status:
        print(f"   ✓ Verification status retrieved")
        print(f"   - Status: {status['status']}")
        print(f"   - Identity Verified: {status['identity_verified']}")
        print(f"   - AML Check Passed: {status['aml_check_passed']}")
        print(f"   - Risk Level: {status['risk_level']}")
        if status['rejection_reason']:
            print(f"   - Rejection Reason: {status['rejection_reason']}")
    else:
        print("   ✗ No verification status found")
    
    print()
    
    # 3. Monitor transaction
    print("3. Monitoring transaction...")
    transaction_data = {
        "transaction_id": "TXN001",
        "amount": 5000000,  # Rp 5 juta
        "type": "credit",
        "timestamp": datetime.now().isoformat(),
        "counterparty": "PARTY001"
    }
    
    monitoring_result = await kyc_system.monitor_transaction(user_id, transaction_data)
    
    if monitoring_result["success"]:
        print(f"   ✓ Transaction monitoring completed")
        print(f"   - Monitoring Required: {monitoring_result['monitoring_required']}")
        print(f"   - Risk Indicators: {monitoring_result['risk_indicators']}")
        if monitoring_result['suspicious_activities']:
            print(f"   - Suspicious Activities: {len(monitoring_result['suspicious_activities'])}")
    else:
        print(f"   ✗ Transaction monitoring failed: {monitoring_result['error']}")
    
    print()
    
    # 4. Generate compliance report
    print("4. Generating compliance report...")
    report = kyc_system.generate_compliance_report()
    
    print(f"   ✓ Compliance report generated")
    print(f"   - Total Users: {report['total_users']}")
    print(f"   - Total Verifications: {report['total_verifications']}")
    print(f"   - Compliance Rate: {report['compliance_rate']:.2f}%")
    print(f"   - Report Generated At: {report['report_generated_at']}")
    
    print("\n=== Demo completed successfully! ===")


if __name__ == "__main__":
    asyncio.run(main())