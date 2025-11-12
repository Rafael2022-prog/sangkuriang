"""
PDP Law Compliance Module untuk SANGKURIANG
Modul kepatuhan terhadap Undang-Undang Perlindungan Data Pribadi (UU PDP)
"""

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import aiohttp
import asyncio
import logging
from cryptography.fernet import Fernet
import base64


class DataCategory(Enum):
    """Kategori data pribadi menurut UU PDP"""
    PERSONAL_IDENTITY = "personal_identity"  # Nama, NIK, tanggal lahir
    CONTACT_INFORMATION = "contact_information"  # Alamat, email, telepon
    FINANCIAL_DATA = "financial_data"  # Data keuangan, rekening
    BIOMETRIC_DATA = "biometric_data"  # Sidik jari, wajah, suara
    HEALTH_DATA = "health_data"  # Data kesehatan
    LOCATION_DATA = "location_data"  # Data lokasi
    BEHAVIORAL_DATA = "behavioral_data"  # Data perilaku online
    SENSITIVE_DATA = "sensitive_data"  # Agama, kepercayaan, politik
    CHILDREN_DATA = "children_data"  # Data anak-anak
    EMPLOYMENT_DATA = "employment_data"  # Data pekerjaan


class ProcessingPurpose(Enum):
    """Tujuan pemrosesan data menurut UU PDP"""
    SERVICE_PROVISION = "service_provision"
    LEGAL_OBLIGATION = "legal_obligation"
    CONTRACT_PERFORMANCE = "contract_performance"
    LEGITIMATE_INTEREST = "legitimate_interest"
    CONSENT = "consent"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_INTEREST = "public_interest"


class ConsentStatus(Enum):
    """Status persetujuan"""
    PENDING = "pending"
    GIVEN = "given"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    PARTIAL = "partial"


class DataSubjectRights(Enum):
    """Hak-hak subjek data menurut UU PDP"""
    RIGHT_TO_INFORMATION = "right_to_information"
    RIGHT_TO_ACCESS = "right_to_access"
    RIGHT_TO_CORRECTION = "right_to_correction"
    RIGHT_TO_DELETION = "right_to_deletion"
    RIGHT_TO_RESTRICTION = "right_to_restriction"
    RIGHT_TO_PORTABILITY = "right_to_portability"
    RIGHT_TO_OBJECT = "right_to_object"
    RIGHT_TO_NOT_BE_SUBJECT = "right_to_not_be_subject"


class DataBreachSeverity(Enum):
    """Tingkat keparahan pelanggaran data"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PersonalData:
    """Data pribadi yang dilindungi"""
    data_id: str
    data_subject_id: str
    category: DataCategory
    data_type: str
    data_value: str  # Encrypted value
    processing_purposes: List[ProcessingPurpose]
    consent_status: ConsentStatus
    consent_date: Optional[datetime]
    expiry_date: Optional[datetime]
    data_source: str
    third_parties: List[str]
    retention_period: int  # days
    created_at: datetime
    updated_at: datetime


@dataclass
class ConsentRecord:
    """Catatan persetujuan"""
    consent_id: str
    data_subject_id: str
    purposes: List[ProcessingPurpose]
    data_categories: List[DataCategory]
    consent_text: str
    consent_status: ConsentStatus
    given_at: Optional[datetime]
    withdrawn_at: Optional[datetime]
    ip_address: str
    user_agent: str
    version: str
    language: str


@dataclass
class DataProcessingActivity:
    """Aktivitas pemrosesan data"""
    activity_id: str
    activity_name: str
    data_categories: List[DataCategory]
    processing_purposes: List[ProcessingPurpose]
    legal_basis: str
    data_subjects_count: int
    data_retention: str
    third_parties: List[str]
    international_transfer: bool
    automated_decision_making: bool
    risk_assessment: str
    dpiaconducted: bool  # Data Protection Impact Assessment


@dataclass
class DataBreach:
    """Pelanggaran data"""
    breach_id: str
    discovery_date: datetime
    occurrence_date: datetime
    affected_data_subjects: int
    data_categories: List[DataCategory]
    breach_description: str
    root_cause: str
    containment_measures: List[str]
    notification_date: Optional[datetime]
    ojk_notification_date: Optional[datetime]
    severity: DataBreachSeverity
    status: str
    remediation_status: str


@dataclass
class DataSubjectRequest:
    """Permintaan dari subjek data"""
    request_id: str
    data_subject_id: str
    request_type: DataSubjectRights
    request_details: str
    submission_date: datetime
    status: str
    response_date: Optional[datetime]
    response_details: str
    documents_provided: List[str]


class DataEncryption:
    """Enkripsi data untuk keamanan"""
    
    def __init__(self, key: Optional[bytes] = None):
        self.key = key or Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def encrypt_data(self, data: str) -> str:
        """Enkripsi data string"""
        encrypted_data = self.cipher.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Dekripsi data string"""
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        decrypted_data = self.cipher.decrypt(encrypted_bytes)
        return decrypted_data.decode()
    
    def hash_data(self, data: str) -> str:
        """Hash data untuk pseudonymization"""
        return hashlib.sha256(data.encode()).hexdigest()


class ConsentManagement:
    """Manajemen persetujuan"""
    
    def __init__(self):
        self.consent_records = {}
        self.consent_templates = self._load_consent_templates()
    
    def _load_consent_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load template persetujuan"""
        return {
            "general_service": {
                "title": "Persetujuan Umum Layanan",
                "description": "Kami memproses data Anda untuk menyediakan layanan kami",
                "purposes": [ProcessingPurpose.SERVICE_PROVISION, ProcessingPurpose.LEGAL_OBLIGATION],
                "data_categories": [DataCategory.PERSONAL_IDENTITY, DataCategory.CONTACT_INFORMATION],
                "retention_period": 2555,  # 7 tahun
                "third_parties": ["payment_processors", "cloud_providers"]
            },
            "marketing": {
                "title": "Persetujuan Marketing",
                "description": "Kami ingin menggunakan data Anda untuk keperluan marketing",
                "purposes": [ProcessingPurpose.CONSENT],
                "data_categories": [DataCategory.PERSONAL_IDENTITY, DataCategory.CONTACT_INFORMATION, DataCategory.BEHAVIORAL_DATA],
                "retention_period": 730,  # 2 tahun
                "third_parties": ["marketing_partners"],
                "optional": True
            },
            "analytics": {
                "title": "Persetujuan Analitik",
                "description": "Kami menganalisis data Anda untuk meningkatkan layanan",
                "purposes": [ProcessingPurpose.LEGITIMATE_INTEREST],
                "data_categories": [DataCategory.BEHAVIORAL_DATA, DataCategory.LOCATION_DATA],
                "retention_period": 1095,  # 3 tahun
                "third_parties": ["analytics_providers"],
                "optional": True
            }
        }
    
    async def create_consent_request(self, data_subject_id: str, consent_type: str) -> Dict[str, Any]:
        """Buat permintaan persetujuan"""
        try:
            if consent_type not in self.consent_templates:
                return {
                    "success": False,
                    "error": f"Unknown consent type: {consent_type}"
                }
            
            template = self.consent_templates[consent_type]
            consent_id = str(uuid.uuid4())
            
            consent_record = ConsentRecord(
                consent_id=consent_id,
                data_subject_id=data_subject_id,
                purposes=template["purposes"],
                data_categories=template["data_categories"],
                consent_text=template["description"],
                consent_status=ConsentStatus.PENDING,
                given_at=None,
                withdrawn_at=None,
                ip_address="",  # Akan diisi saat persetujuan diberikan
                user_agent="",
                version="1.0",
                language="id"
            )
            
            self.consent_records[consent_id] = consent_record
            
            return {
                "success": True,
                "consent_id": consent_id,
                "consent_request": {
                    "title": template["title"],
                    "description": template["description"],
                    "purposes": [p.value for p in template["purposes"]],
                    "data_categories": [c.value for c in template["data_categories"]],
                    "retention_period": template["retention_period"],
                    "third_parties": template["third_parties"],
                    "optional": template.get("optional", False)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def give_consent(self, consent_id: str, ip_address: str, user_agent: str) -> Dict[str, Any]:
        """Beri persetujuan"""
        try:
            if consent_id not in self.consent_records:
                return {
                    "success": False,
                    "error": "Consent not found"
                }
            
            consent_record = self.consent_records[consent_id]
            consent_record.consent_status = ConsentStatus.GIVEN
            consent_record.given_at = datetime.now()
            consent_record.ip_address = ip_address
            consent_record.user_agent = user_agent
            
            return {
                "success": True,
                "consent_id": consent_id,
                "status": ConsentStatus.GIVEN.value,
                "given_at": consent_record.given_at.isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def withdraw_consent(self, consent_id: str) -> Dict[str, Any]:
        """Tarik kembali persetujuan"""
        try:
            if consent_id not in self.consent_records:
                return {
                    "success": False,
                    "error": "Consent not found"
                }
            
            consent_record = self.consent_records[consent_id]
            consent_record.consent_status = ConsentStatus.WITHDRAWN
            consent_record.withdrawn_at = datetime.now()
            
            return {
                "success": True,
                "consent_id": consent_id,
                "status": ConsentStatus.WITHDRAWN.value,
                "withdrawn_at": consent_record.withdrawn_at.isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_consent_status(self, data_subject_id: str) -> Dict[str, Any]:
        """Dapatkan status persetujuan untuk subjek data"""
        subject_consents = [
            consent for consent in self.consent_records.values()
            if consent.data_subject_id == data_subject_id
        ]
        
        return {
            "total_consents": len(subject_consents),
            "active_consents": sum(1 for c in subject_consents if c.consent_status == ConsentStatus.GIVEN),
            "withdrawn_consents": sum(1 for c in subject_consents if c.consent_status == ConsentStatus.WITHDRAWN),
            "consents": [
                {
                    "consent_id": c.consent_id,
                    "status": c.consent_status.value,
                    "purposes": [p.value for p in c.purposes],
                    "given_at": c.given_at.isoformat() if c.given_at else None,
                    "withdrawn_at": c.withdrawn_at.isoformat() if c.withdrawn_at else None
                }
                for c in subject_consents
            ]
        }


class DataBreachManagement:
    """Manajemen pelanggaran data"""
    
    def __init__(self):
        self.breach_records = {}
        self.notification_templates = self._load_notification_templates()
    
    def _load_notification_templates(self) -> Dict[str, str]:
        """Load template notifikasi pelanggaran"""
        return {
            "data_subject_notification": """
            Kepada Yth. {data_subject_name},
            
            Kami mengetahui adanya pelanggaran data pribadi yang mungkin memengaruhi data Anda.
            
            Detail pelanggaran:
            - Jenis data yang terpengaruh: {affected_data_types}
            - Tanggal kejadian: {occurrence_date}
            - Langkah-langkah yang telah kami ambil: {containment_measures}
            
            Kami mohon maaf atas ketidaknyamanan ini dan telah mengambil langkah-langkah teknis dan organisasi
            untuk mencegah terjadinya pelanggaran serupa di masa depan.
            
            Untuk informasi lebih lanjut, silakan hubungi kami di privacy@sangkuriang.id
            
            Hormat kami,
            Tim Privasi SANGKURIANG
            """,
            "ojk_notification": """
            Kepada Yth. Otoritas Jasa Keuangan (OJK),
            
            Sehubungan dengan kewajiban pelaporan pelanggaran data pribadi sesuai dengan UU PDP,
            kami melaporkan bahwa telah terjadi pelanggaran data pribadi dengan detail sebagai berikut:
            
            - ID Pelanggaran: {breach_id}
            - Tanggal Penemuan: {discovery_date}
            - Tanggal Kejadian: {occurrence_date}
            - Jumlah Subjek Data yang Terpengaruh: {affected_subjects}
            - Kategori Data: {data_categories}
            - Deskripsi: {breach_description}
            - Penyebab: {root_cause}
            - Langkah Penanggulangan: {containment_measures}
            
            Laporan lengkap terlampir.
            
            Hormat kami,
            PT SANGKURIANG Teknologi Finansial
            """
        }
    
    async def detect_breach(self, breach_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deteksi dan catat pelanggaran data"""
        try:
            breach_id = str(uuid.uuid4())
            
            # Validasi data pelanggaran
            required_fields = ["occurrence_date", "affected_data_subjects", "data_categories", "breach_description"]
            for field in required_fields:
                if field not in breach_data:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }
            
            # Tentukan tingkat keparahan
            severity = self._assess_breach_severity(breach_data)
            
            # Buat record pelanggaran
            breach_record = DataBreach(
                breach_id=breach_id,
                discovery_date=datetime.now(),
                occurrence_date=datetime.fromisoformat(breach_data["occurrence_date"]),
                affected_data_subjects=breach_data["affected_data_subjects"],
                data_categories=[DataCategory(cat) for cat in breach_data["data_categories"]],
                breach_description=breach_data["breach_description"],
                root_cause=breach_data.get("root_cause", "Unknown"),
                containment_measures=breach_data.get("containment_measures", []),
                notification_date=None,
                ojk_notification_date=None,
                severity=severity,
                status="detected",
                remediation_status="pending"
            )
            
            self.breach_records[breach_id] = breach_record
            
            # Lakukan notifikasi jika diperlukan
            notification_result = await self._handle_notifications(breach_record)
            
            return {
                "success": True,
                "breach_id": breach_id,
                "severity": severity.value,
                "notification_required": notification_result["notification_required"],
                "ojk_notification_required": notification_result["ojk_notification_required"],
                "timeline": notification_result["timeline"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _assess_breach_severity(self, breach_data: Dict[str, Any]) -> DataBreachSeverity:
        """Tentukan tingkat keparahan pelanggaran"""
        score = 0
        
        # Faktor 1: Jumlah subjek data yang terpengaruh
        affected_count = breach_data["affected_data_subjects"]
        if affected_count >= 1000:
            score += 40
        elif affected_count >= 100:
            score += 30
        elif affected_count >= 10:
            score += 20
        else:
            score += 10
        
        # Faktor 2: Kategori data yang terpengaruh
        sensitive_categories = [DataCategory.BIOMETRIC_DATA, DataCategory.HEALTH_DATA, 
                                DataCategory.SENSITIVE_DATA, DataCategory.CHILDREN_DATA]
        
        affected_categories = [DataCategory(cat) for cat in breach_data["data_categories"]]
        sensitive_affected = any(cat in sensitive_categories for cat in affected_categories)
        
        if sensitive_affected:
            score += 40
        else:
            score += 20
        
        # Faktor 3: Deskripsi pelanggaran
        description = breach_data["breach_description"].lower()
        if any(keyword in description for keyword in ["unauthorized access", "hacking", "malicious"]):
            score += 20
        elif any(keyword in description for keyword in ["accidental", "human error"]):
            score += 10
        else:
            score += 15
        
        # Tentukan severity berdasarkan total score
        if score >= 80:
            return DataBreachSeverity.CRITICAL
        elif score >= 60:
            return DataBreachSeverity.HIGH
        elif score >= 40:
            return DataBreachSeverity.MEDIUM
        else:
            return DataBreachSeverity.LOW
    
    async def _handle_notifications(self, breach_record: DataBreach) -> Dict[str, Any]:
        """Handle notifikasi pelanggaran"""
        notification_required = breach_record.severity in [DataBreachSeverity.HIGH, DataBreachSeverity.CRITICAL]
        ojk_notification_required = breach_record.severity in [DataBreachSeverity.MEDIUM, DataBreachSeverity.HIGH, DataBreachSeverity.CRITICAL]
        
        timeline = {}
        
        if notification_required:
            # Notifikasi ke subjek data harus dilakukan dalam 72 jam
            timeline["data_subject_notification"] = (breach_record.discovery_date + timedelta(hours=72)).isoformat()
            breach_record.notification_date = breach_record.discovery_date + timedelta(hours=24)  # Contoh: notifikasi dalam 24 jam
        
        if ojk_notification_required:
            # Notifikasi ke OJK harus dilakukan dalam 72 jam
            timeline["ojk_notification"] = (breach_record.discovery_date + timedelta(hours=72)).isoformat()
            breach_record.ojk_notification_date = breach_record.discovery_date + timedelta(hours=48)  # Contoh: notifikasi dalam 48 jam
        
        return {
            "notification_required": notification_required,
            "ojk_notification_required": ojk_notification_required,
            "timeline": timeline
        }
    
    def get_breach_statistics(self) -> Dict[str, Any]:
        """Dapatkan statistik pelanggaran data"""
        total_breaches = len(self.breach_records)
        
        severity_breakdown = {}
        status_breakdown = {}
        monthly_trend = {}
        
        for breach in self.breach_records.values():
            severity_breakdown[breach.severity.value] = severity_breakdown.get(breach.severity.value, 0) + 1
            status_breakdown[breach.status] = status_breakdown.get(breach.status, 0) + 1
            
            # Trend bulanan
            month_key = breach.discovery_date.strftime("%Y-%m")
            monthly_trend[month_key] = monthly_trend.get(month_key, 0) + 1
        
        total_affected_subjects = sum(breach.affected_data_subjects for breach in self.breach_records.values())
        
        return {
            "total_breaches": total_breaches,
            "total_affected_subjects": total_affected_subjects,
            "severity_breakdown": severity_breakdown,
            "status_breakdown": status_breakdown,
            "monthly_trend": monthly_trend,
            "average_affected_per_breach": total_affected_subjects / total_breaches if total_breaches > 0 else 0
        }


class DataSubjectRightsManager:
    """Manajemen hak-hak subjek data"""
    
    def __init__(self):
        self.requests_db = {}
        self.processing_activities = {}
        self.response_templates = self._load_response_templates()
    
    def _load_response_templates(self) -> Dict[str, str]:
        """Load template respons untuk hak subjek data"""
        return {
            "access_response": """
            Berdasarkan permintaan Anda mengenai hak akses data pribadi, berikut kami sampaikan informasi yang diminta:
            
            {data_summary}
            
            Data pribadi Anda diproses untuk tujuan berikut:
            {processing_purposes}
            
            Data Anda akan disimpan selama {retention_period} dan mungkin dibagikan dengan:
            {third_parties}
            
            Jika Anda memiliki pertanyaan lebih lanjut, silakan hubungi kami.
            """,
            "deletion_response": """
            Permintaan penghapusan data pribadi Anda telah kami proses.
            
            Status penghapusan: {deletion_status}
            {deletion_details}
            
            Perlu diperhatikan bahwa beberapa data mungkin perlu kami simpan untuk keperluan hukum atau audit.
            """
        }
    
    async def submit_data_subject_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit permintaan dari subjek data"""
        try:
            request_id = str(uuid.uuid4())
            
            # Validasi data permintaan
            required_fields = ["data_subject_id", "request_type", "request_details"]
            for field in required_fields:
                if field not in request_data:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }
            
            # Buat record permintaan
            request_record = DataSubjectRequest(
                request_id=request_id,
                data_subject_id=request_data["data_subject_id"],
                request_type=DataSubjectRights(request_data["request_type"]),
                request_details=request_data["request_details"],
                submission_date=datetime.now(),
                status="received",
                response_date=None,
                response_details="",
                documents_provided=[]
            )
            
            self.requests_db[request_id] = request_record
            
            # Proses permintaan secara otomatis untuk beberapa jenis
            if request_record.request_type in [DataSubjectRights.RIGHT_TO_ACCESS, DataSubjectRights.RIGHT_TO_INFORMATION]:
                await self._process_access_request(request_id)
            
            return {
                "success": True,
                "request_id": request_id,
                "status": "received",
                "estimated_response_time": "30 days"  # Sesuai UU PDP
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _process_access_request(self, request_id: str) -> Dict[str, Any]:
        """Proses permintaan akses data"""
        try:
            if request_id not in self.requests_db:
                return {
                    "success": False,
                    "error": "Request not found"
                }
            
            request_record = self.requests_db[request_id]
            
            # Simulasi pengambilan data (dalam implementasi nyata akan mengambil dari database)
            data_summary = {
                "personal_data_categories": ["personal_identity", "contact_information", "financial_data"],
                "data_retention_period": "7 years",
                "third_parties": ["payment_processors", "cloud_providers", "analytics_services"],
                "processing_purposes": ["service_provision", "legal_obligation", "legitimate_interest"]
            }
            
            # Update status permintaan
            request_record.status = "processed"
            request_record.response_date = datetime.now()
            request_record.response_details = json.dumps(data_summary, indent=2)
            
            return {
                "success": True,
                "request_id": request_id,
                "status": "processed",
                "data_provided": data_summary
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_request_status(self, data_subject_id: str) -> Dict[str, Any]:
        """Dapatkan status permintaan untuk subjek data"""
        subject_requests = [
            request for request in self.requests_db.values()
            if request.data_subject_id == data_subject_id
        ]
        
        return {
            "total_requests": len(subject_requests),
            "pending_requests": sum(1 for r in subject_requests if r.status == "received"),
            "processed_requests": sum(1 for r in subject_requests if r.status == "processed"),
            "requests": [
                {
                    "request_id": r.request_id,
                    "request_type": r.request_type.value,
                    "status": r.status,
                    "submission_date": r.submission_date.isoformat(),
                    "response_date": r.response_date.isoformat() if r.response_date else None
                }
                for r in subject_requests
            ]
        }


class PDPLawComplianceManager:
    """Manajer utama untuk kepatuhan UU PDP"""
    
    def __init__(self, storage_path: str = "pdp_compliance_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        self.encryption = DataEncryption()
        self.consent_management = ConsentManagement()
        self.breach_management = DataBreachManagement()
        self.rights_manager = DataSubjectRightsManager()
        
        # Database untuk menyimpan data
        self.personal_data_db = {}
        self.processing_activities_db = {}
        self.compliance_logs = []
        
        # Inisialisasi audit trail
        self._setup_audit_logging()
    
    def _setup_audit_logging(self):
        """Setup audit logging"""
        audit_handler = logging.FileHandler(self.storage_path / "audit_log.json")
        audit_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        audit_handler.setFormatter(formatter)
        
        self.audit_logger = logging.getLogger('PDP_Audit')
        self.audit_logger.addHandler(audit_handler)
        self.audit_logger.setLevel(logging.INFO)
    
    def _log_activity(self, activity: str, details: Dict[str, Any]):
        """Log aktivitas untuk audit trail"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "activity": activity,
            "details": details
        }
        self.audit_logger.info(json.dumps(log_entry))
        self.compliance_logs.append(log_entry)
    
    async def register_data_processing_activity(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Registrasi aktivitas pemrosesan data"""
        try:
            activity_id = str(uuid.uuid4())
            
            # Validasi data aktivitas
            required_fields = ["activity_name", "data_categories", "processing_purposes", "legal_basis"]
            for field in required_fields:
                if field not in activity_data:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }
            
            # Buat record aktivitas
            processing_activity = DataProcessingActivity(
                activity_id=activity_id,
                activity_name=activity_data["activity_name"],
                data_categories=[DataCategory(cat) for cat in activity_data["data_categories"]],
                processing_purposes=[ProcessingPurpose(p) for p in activity_data["processing_purposes"]],
                legal_basis=activity_data["legal_basis"],
                data_subjects_count=activity_data.get("data_subjects_count", 0),
                data_retention=activity_data.get("data_retention", "7 years"),
                third_parties=activity_data.get("third_parties", []),
                international_transfer=activity_data.get("international_transfer", False),
                automated_decision_making=activity_data.get("automated_decision_making", False),
                risk_assessment=activity_data.get("risk_assessment", "low"),
                dpiaconducted=activity_data.get("dpia_conducted", False)
            )
            
            self.processing_activities_db[activity_id] = processing_activity
            
            # Log aktivitas
            self._log_activity("PROCESSING_ACTIVITY_REGISTERED", {
                "activity_id": activity_id,
                "activity_name": activity_data["activity_name"],
                "data_categories": activity_data["data_categories"]
            })
            
            return {
                "success": True,
                "activity_id": activity_id,
                "status": "registered"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def process_personal_data(self, data_subject_id: str, data: Dict[str, Any], processing_purpose: ProcessingPurpose) -> Dict[str, Any]:
        """Proses data pribadi dengan mematuhi UU PDP"""
        try:
            # Cek persetujuan
            consent_status = self.consent_management.get_consent_status(data_subject_id)
            
            if consent_status["active_consents"] == 0:
                return {
                    "success": False,
                    "error": "No valid consent found for data processing"
                }
            
            # Enkripsi data sensitif
            encrypted_data = {}
            for key, value in data.items():
                if self._is_sensitive_data(key):
                    encrypted_data[key] = self.encryption.encrypt_data(str(value))
                else:
                    encrypted_data[key] = value
            
            # Simpan data
            data_id = str(uuid.uuid4())
            personal_data = PersonalData(
                data_id=data_id,
                data_subject_id=data_subject_id,
                category=self._categorize_data(data),
                data_type=list(data.keys())[0] if data else "unknown",
                data_value=json.dumps(encrypted_data),
                processing_purposes=[processing_purpose],
                consent_status=ConsentStatus.GIVEN,
                consent_date=datetime.now(),
                expiry_date=datetime.now() + timedelta(days=2555),  # 7 tahun
                data_source="user_input",
                third_parties=[],
                retention_period=2555,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.personal_data_db[data_id] = personal_data
            
            # Log pemrosesan
            self._log_activity("PERSONAL_DATA_PROCESSED", {
                "data_id": data_id,
                "data_subject_id": data_subject_id,
                "processing_purpose": processing_purpose.value,
                "data_categories": [cat.value for cat in personal_data.category]
            })
            
            return {
                "success": True,
                "data_id": data_id,
                "processing_status": "completed"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_personal_data_async(self, data_subject_id: str, data: Dict[str, Any], processing_purpose: ProcessingPurpose) -> Dict[str, Any]:
        """Proses data pribadi secara async dengan mematuhi UU PDP"""
        return self.process_personal_data(data_subject_id, data, processing_purpose)
    
    def _is_sensitive_data(self, data_key: str) -> bool:
        """Cek apakah data termasuk kategori sensitif"""
        sensitive_keywords = ["password", "pin", "biometric", "health", "financial", "credit_card"]
        return any(keyword in data_key.lower() for keyword in sensitive_keywords)
    
    def _categorize_data(self, data: Dict[str, Any]) -> List[DataCategory]:
        """Kategorikan data berdasarkan kontennya"""
        categories = []
        
        for key in data.keys():
            key_lower = key.lower()
            
            if any(word in key_lower for word in ["name", "nik", "birth"]):
                categories.append(DataCategory.PERSONAL_IDENTITY)
            elif any(word in key_lower for word in ["email", "phone", "address"]):
                categories.append(DataCategory.CONTACT_INFORMATION)
            elif any(word in key_lower for word in ["bank", "account", "financial", "income"]):
                categories.append(DataCategory.FINANCIAL_DATA)
            elif any(word in key_lower for word in ["fingerprint", "face", "biometric"]):
                categories.append(DataCategory.BIOMETRIC_DATA)
            elif any(word in key_lower for word in ["health", "medical"]):
                categories.append(DataCategory.HEALTH_DATA)
            elif any(word in key_lower for word in ["location", "gps", "address"]):
                categories.append(DataCategory.LOCATION_DATA)
            else:
                categories.append(DataCategory.PERSONAL_IDENTITY)  # Default
        
        return list(set(categories))  # Hapus duplikat
    
    def record_consent(self, consent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Catat persetujuan dari pengguna (sync)"""
        return self._record_consent_impl(consent_data)
    
    async def record_consent_async(self, consent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Catat persetujuan dari pengguna (async)"""
        return self._record_consent_impl(consent_data)
    
    def _record_consent_impl(self, consent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Implementasi catat persetujuan dari pengguna"""
        try:
            consent_id = str(uuid.uuid4())
            
            # Validasi data persetujuan
            required_fields = ["user_id", "consent_text", "data_categories", "purposes"]
            for field in required_fields:
                if field not in consent_data:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }
            
            # Buat record persetujuan
            consent_record = ConsentRecord(
                consent_id=consent_id,
                data_subject_id=consent_data["user_id"],
                purposes=[ProcessingPurpose(p) for p in consent_data["purposes"]],
                data_categories=[DataCategory(cat) for cat in consent_data["data_categories"]],
                consent_text=consent_data["consent_text"],
                consent_status=ConsentStatus.GIVEN,
                given_at=datetime.now(),
                withdrawn_at=None,
                ip_address="127.0.0.1",  # Dummy IP
                user_agent="Test Browser",
                version="1.0",
                language="id"
            )
            
            self.consent_management.consent_records[consent_id] = consent_record
            
            # Log aktivitas
            self._log_activity("CONSENT_RECORDED", {
                "consent_id": consent_id,
                "data_subject_id": consent_data["user_id"],
                "consent_text": consent_data["consent_text"]
            })
            
            return {
                "success": True,
                "consent_id": consent_id,
                "consent_status": "ACTIVE"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def handle_data_breach(self, breach_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pelanggaran data (sync)"""
        return self._handle_data_breach_impl(breach_data)
    
    async def handle_data_breach_async(self, breach_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pelanggaran data (async)"""
        return self._handle_data_breach_impl(breach_data)
    
    def _handle_data_breach_impl(self, breach_data: Dict[str, Any]) -> Dict[str, Any]:
        """Implementasi handle pelanggaran data"""
        try:
            breach_id = str(uuid.uuid4())
            
            # Validasi data pelanggaran
            required_fields = ["breach_type", "affected_data_categories", "affected_individuals"]
            for field in required_fields:
                if field not in breach_data:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }
            
            # Buat record pelanggaran
            breach_record = DataBreach(
                breach_id=breach_id,
                discovery_date=datetime.fromisoformat(breach_data.get("discovery_date", datetime.now().isoformat())),
                occurrence_date=datetime.fromisoformat(breach_data.get("occurrence_date", datetime.now().isoformat())),
                affected_data_subjects=int(breach_data["affected_individuals"]),
                data_categories=[DataCategory(cat) for cat in breach_data["affected_data_categories"]],
                breach_description=breach_data.get("breach_description", "Data breach incident"),
                root_cause=breach_data.get("root_cause", "Unknown"),
                containment_measures=breach_data.get("containment_measures", []),
                notification_date=None,
                ojk_notification_date=None,
                severity=DataBreachSeverity.HIGH,
                status="INVESTIGATING",
                remediation_status="PENDING"
            )
            
            # Simpan breach record ke database internal
            if not hasattr(self, 'breach_records'):
                self.breach_records = {}
            self.breach_records[breach_id] = breach_record
            
            # Log aktivitas
            self._log_activity("DATA_BREACH_RECORDED", {
                "breach_id": breach_id,
                "breach_type": breach_data["breach_type"],
                "affected_individuals": breach_data["affected_individuals"]
            })
            
            return {
                "success": True,
                "breach_response": {
                    "breach_id": breach_id,
                    "notification_deadline": (datetime.now() + timedelta(hours=72)).isoformat(),
                    "required_actions": [
                        "Notify affected individuals within 72 hours",
                        "Report to supervisory authority",
                        "Implement containment measures",
                        "Conduct post-breach review"
                    ]
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def process_data_subject_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Proses permintaan subjek data (sync)"""
        return self._process_data_subject_request_impl(request_data)
    
    async def process_data_subject_request_async(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Proses permintaan subjek data (async)"""
        return self._process_data_subject_request_impl(request_data)
    
    def _process_data_subject_request_impl(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Implementasi proses permintaan subjek data"""
        try:
            request_id = str(uuid.uuid4())
            
            # Validasi data permintaan
            required_fields = ["data_subject_id", "request_type"]
            for field in required_fields:
                if field not in request_data:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }
            
            # Proses berdasarkan jenis permintaan
            request_type = request_data["request_type"]
            
            if request_type == "ACCESS_REQUEST":
                # Proses permintaan akses data
                response_data = self._handle_access_request(request_data["data_subject_id"])
                response_deadline = (datetime.now() + timedelta(days=30)).isoformat()
                
            elif request_type == "CORRECTION_REQUEST":
                # Proses permintaan koreksi data
                response_data = self._handle_correction_request(request_data["data_subject_id"], request_data.get("correction_data", {}))
                response_deadline = (datetime.now() + timedelta(days=30)).isoformat()
                
            elif request_type == "DELETION_REQUEST":
                # Proses permintaan penghapusan data
                response_data = self._handle_deletion_request(request_data["data_subject_id"])
                response_deadline = (datetime.now() + timedelta(days=30)).isoformat()
                
            else:
                return {
                    "success": False,
                    "error": f"Unsupported request type: {request_type}"
                }
            
            # Log aktivitas
            self._log_activity("DATA_SUBJECT_REQUEST_PROCESSED", {
                "request_id": request_id,
                "data_subject_id": request_data["data_subject_id"],
                "request_type": request_type
            })
            
            return {
                "success": True,
                "request_status": "PROCESSING",
                "response_deadline": response_deadline,
                "request_data": response_data
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_access_request(self, data_subject_id: str) -> Dict[str, Any]:
        """Handle permintaan akses data"""
        # Cari data yang dimiliki oleh subjek data
        subject_data = [data for data in self.personal_data_db.values() if data.data_subject_id == data_subject_id]
        
        return {
            "total_records": len(subject_data),
            "data_categories": list(set(cat.value for data in subject_data for cat in data.category)),
            "processing_purposes": list(set(purpose.value for data in subject_data for purpose in data.processing_purposes)),
            "retention_periods": list(set(str(data.retention_period) for data in subject_data))
        }
    
    def _handle_correction_request(self, data_subject_id: str, correction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle permintaan koreksi data"""
        # Implementasi koreksi data
        return {
            "correction_status": "PENDING_REVIEW",
            "correction_data": correction_data,
            "review_deadline": (datetime.now() + timedelta(days=14)).isoformat()
        }
    
    def _handle_deletion_request(self, data_subject_id: str) -> Dict[str, Any]:
        """Handle permintaan penghapusan data"""
        # Implementasi penghapusan data
        return {
            "deletion_status": "PENDING_VERIFICATION",
            "verification_deadline": (datetime.now() + timedelta(days=14)).isoformat(),
            "retention_exceptions": ["LEGAL_OBLIGATION", "TAX_RECORDS"]
        }
    
    def get_compliance_summary(self) -> Dict[str, Any]:
        """Dapatkan ringkasan kepatuhan UU PDP"""
        total_data_subjects = len(set(data.data_subject_id for data in self.personal_data_db.values()))
        total_processing_activities = len(self.processing_activities_db)
        total_breaches = len(self.breach_management.breach_records)
        
        # Hitung statistik persetujuan
        total_consents = len(self.consent_management.consent_records)
        active_consents = sum(1 for consent in self.consent_management.consent_records.values() 
                              if consent.consent_status == ConsentStatus.GIVEN)
        
        # Statistik pelanggaran
        breach_stats = self.breach_management.get_breach_statistics()
        
        return {
            "total_data_subjects": total_data_subjects,
            "total_processing_activities": total_processing_activities,
            "total_personal_data_records": len(self.personal_data_db),
            "consent_statistics": {
                "total_consents": total_consents,
                "active_consents": active_consents,
                "consent_rate": (active_consents / total_consents * 100) if total_consents > 0 else 0
            },
            "data_breach_statistics": breach_stats,
            "compliance_status": "compliant" if total_breaches == 0 else "review_required",
            "last_updated": datetime.now().isoformat()
        }
    
    def generate_privacy_report(self) -> Dict[str, Any]:
        """Generate laporan privasi untuk regulator"""
        compliance_summary = self.get_compliance_summary()
        
        return {
            "report_id": f"PDP-RPT-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "report_date": datetime.now().isoformat(),
            "compliance_summary": compliance_summary,
            "data_processing_activities": len(self.processing_activities_db),
            "consent_management_status": {
                "total_templates": len(self.consent_management.consent_templates),
                "active_consents": compliance_summary["consent_statistics"]["active_consents"]
            },
            "data_breaches": {
                "total_incidents": compliance_summary["data_breach_statistics"]["total_breaches"],
                "severity_breakdown": compliance_summary["data_breach_statistics"]["severity_breakdown"]
            },
            "recommendations": [
                "Lakukan penilaian ulang risiko secara berkala",
                "Pastikan semua aktivitas pemrosesan memiliki dasar hukum yang jelas",
                "Update kebijakan privasi secara berkala",
                "Latih staf tentang perlindungan data pribadi"
            ]
        }


# Contoh penggunaan
async def main():
    """Demo penggunaan PDP Law Compliance Module"""
    
    # Inisialisasi manajer kepatuhan
    pdp_manager = PDPLawComplianceManager()
    
    print("=== SANGKURIANG PDP Law Compliance Module Demo ===\n")
    
    # 1. Registrasi aktivitas pemrosesan data
    print("1. Registering data processing activity...")
    activity_data = {
        "activity_name": "User Registration and KYC Processing",
        "data_categories": ["personal_identity", "contact_information", "biometric_data"],
        "processing_purposes": ["service_provision", "legal_obligation"],
        "legal_basis": "Consent and Legal Obligation",
        "data_subjects_count": 1,
        "data_retention": "7 years",
        "third_parties": ["KYC_service_providers"],
        "international_transfer": False,
        "automated_decision_making": True,
        "dpia_conducted": True
    }
    
    result = await pdp_manager.register_data_processing_activity(activity_data)
    if result["success"]:
        print(f"   ✓ Activity registered successfully")
        print(f"   - Activity ID: {result['activity_id']}")
    
    print()
    
    # 2. Create consent request
    print("2. Creating consent request...")
    consent_result = await pdp_manager.consent_management.create_consent_request("USER_001", "general_service")
    
    if consent_result["success"]:
        print(f"   ✓ Consent request created")
        print(f"   - Consent ID: {consent_result['consent_id']}")
        print(f"   - Title: {consent_result['consent_request']['title']}")
        print(f"   - Purposes: {consent_result['consent_request']['purposes']}")
        
        # Give consent
        consent_given = await pdp_manager.consent_management.give_consent(
            consent_result["consent_id"], 
            "192.168.1.1", 
            "Mozilla/5.0"
        )
        
        if consent_given["success"]:
            print(f"   ✓ Consent given successfully")
    
    print()
    
    # 3. Process personal data
    print("3. Processing personal data...")
    user_data = {
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+6281234567890",
        "nik": "1234567890123456",
        "date_of_birth": "1990-01-01"
    }
    
    processing_result = await pdp_manager.process_personal_data(
        "USER_001", 
        user_data, 
        ProcessingPurpose.SERVICE_PROVISION
    )
    
    if processing_result["success"]:
        print(f"   ✓ Personal data processed successfully")
        print(f"   - Data ID: {processing_result['data_id']}")
    
    print()
    
    # 4. Submit data subject request
    print("4. Submitting data subject request...")
    request_data = {
        "data_subject_id": "USER_001",
        "request_type": "right_to_access",
        "request_details": "I want to know what personal data you have about me"
    }
    
    request_result = await pdp_manager.rights_manager.submit_data_subject_request(request_data)
    
    if request_result["success"]:
        print(f"   ✓ Data subject request submitted")
        print(f"   - Request ID: {request_result['request_id']}")
        print(f"   - Status: {request_result['status']}")
    
    print()
    
    # 5. Simulate data breach
    print("5. Simulating data breach...")
    breach_data = {
        "occurrence_date": datetime.now().isoformat(),
        "affected_data_subjects": 150,
        "data_categories": ["personal_identity", "contact_information"],
        "breach_description": "Unauthorized access to user database due to misconfigured security settings",
        "root_cause": "Human error - incorrect security configuration",
        "containment_measures": ["Fixed security configuration", "Reset affected user passwords", "Enhanced monitoring"]
    }
    
    breach_result = await pdp_manager.breach_management.detect_breach(breach_data)
    
    if breach_result["success"]:
        print(f"   ✓ Data breach detected and recorded")
        print(f"   - Breach ID: {breach_result['breach_id']}")
        print(f"   - Severity: {breach_result['severity']}")
        print(f"   - Notification Required: {breach_result['notification_required']}")
    
    print()
    
    # 6. Get compliance summary
    print("6. Getting compliance summary...")
    compliance_summary = pdp_manager.get_compliance_summary()
    
    print(f"   ✓ Compliance summary retrieved")
    print(f"   - Total Data Subjects: {compliance_summary['total_data_subjects']}")
    print(f"   - Processing Activities: {compliance_summary['total_processing_activities']}")
    print(f"   - Personal Data Records: {compliance_summary['total_personal_data_records']}")
    print(f"   - Active Consents: {compliance_summary['consent_statistics']['active_consents']}")
    print(f"   - Data Breaches: {compliance_summary['data_breach_statistics']['total_breaches']}")
    
    print()
    
    # 7. Generate privacy report
    print("7. Generating privacy report...")
    privacy_report = pdp_manager.generate_privacy_report()
    
    print(f"   ✓ Privacy report generated")
    print(f"   - Report ID: {privacy_report['report_id']}")
    print(f"   - Report Date: {privacy_report['report_date']}")
    print(f"   - Processing Activities: {privacy_report['data_processing_activities']}")
    
    print("\n=== Demo completed successfully! ===")


if __name__ == "__main__":
    asyncio.run(main())