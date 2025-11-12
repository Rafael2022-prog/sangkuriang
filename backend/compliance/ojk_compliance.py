"""
OJK Compliance Module untuk SANGKURIANG
Modul kepatuhan terhadap regulasi Otoritas Jasa Keuangan (OJK) Indonesia
"""

import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import aiohttp
import asyncio


class OJKLicenseType(Enum):
    """Jenis lisensi OJK"""
    PAYMENT_SYSTEM = "payment_system"
    FUNDING_PLATFORM = "funding_platform"
    DIGITAL_WALLET = "digital_wallet"
    CROWDFUNDING = "crowdfunding"
    INVESTMENT_MANAGER = "investment_manager"


class ComplianceStatus(Enum):
    """Status kepatuhan"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING_REVIEW = "pending_review"
    UNDER_INVESTIGATION = "under_investigation"
    SUSPENDED = "suspended"


class RiskCategory(Enum):
    """Kategori risiko OJK"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


class ReportType(Enum):
    """Jenis laporan untuk OJK"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    INCIDENT = "incident"
    AUDIT = "audit"


@dataclass
class OJKLicense:
    """Data lisensi OJK"""
    license_id: str
    license_type: OJKLicenseType
    license_number: str
    issue_date: datetime
    expiry_date: datetime
    status: str
    scope_of_activities: List[str]
    conditions: List[str]
    issuing_authority: str


@dataclass
class ComplianceRequirement:
    """Persyaratan kepatuhan OJK"""
    requirement_id: str
    title: str
    description: str
    regulation_reference: str
    deadline: datetime
    status: ComplianceStatus
    evidence_documents: List[str]
    responsible_party: str
    completion_date: Optional[datetime]


@dataclass
class RiskAssessment:
    """Penilaian risiko OJK"""
    assessment_id: str
    entity_id: str
    risk_category: RiskCategory
    risk_score: float
    risk_factors: Dict[str, float]
    mitigation_measures: List[str]
    next_review_date: datetime
    assessor: str
    assessment_date: datetime


@dataclass
class TransactionReport:
    """Laporan transaksi untuk OJK"""
    report_id: str
    report_type: ReportType
    reporting_period_start: datetime
    reporting_period_end: datetime
    total_transactions: int
    total_volume: float
    suspicious_transactions: int
    compliance_violations: int
    data_quality_score: float
    submission_date: datetime
    status: str


@dataclass
class ConsumerProtectionRecord:
    """Catatan perlindungan konsumen"""
    record_id: str
    complaint_id: str
    consumer_id: str
    complaint_type: str
    description: str
    severity: str
    resolution_status: str
    resolution_date: Optional[datetime]
    compensation_amount: float
    ojk_escalation: bool


class OJKRegulationDatabase:
    """Database regulasi OJK"""
    
    def __init__(self):
        self.regulations = self._load_regulations()
        self.circulars = self._load_circulars()
        self.guidelines = self._load_guidelines()
    
    def _load_regulations(self) -> Dict[str, Dict[str, Any]]:
        """Load regulasi OJK"""
        return {
            "POJK_77_2016": {
                "title": "POJK 77/2016 tentang Layanan Pinjam Meminjam",
                "effective_date": "2016-12-01",
                "scope": ["fintech", "lending", "crowdfunding"],
                "key_requirements": [
                    "Minimum modal Rp 1 miliar",
                    "Kewajiban registrasi di OJK",
                    "Pembatasan bunga maksimal",
                    "Perlindungan data konsumen"
                ]
            },
            "POJK_13_2018": {
                "title": "POJK 13/2018 tentang Penyelenggaraan Inovasi Teknologi Keuangan",
                "effective_date": "2018-07-01",
                "scope": ["fintech", "innovation", "sandbox"],
                "key_requirements": [
                    "Registrasi di OJK Regulatory Sandbox",
                    "Uji teknologi dan bisnis model",
                    "Pelaporan berkala",
                    "Evaluasi risiko"
                ]
            },
            "POJK_23_2018": {
                "title": "POJK 23/2018 tentang Perlindungan Konsumen Sektor Jasa Keuangan",
                "effective_date": "2018-08-01",
                "scope": ["consumer_protection", "dispute_resolution"],
                "key_requirements": [
                    "Penyampaian informasi yang jelas",
                    "Penyelesaian pengaduan konsumen",
                    "Kompensasi atas kerugian konsumen",
                    "Edukasi keuangan"
                ]
            },
            "POJK_34_2021": {
                "title": "POJK 34/2021 tentang Penyelenggaraan Teknologi Finansial Berbasis Teknologi Kripto",
                "effective_date": "2021-09-01",
                "scope": ["crypto", "blockchain", "digital_assets"],
                "key_requirements": [
                    "Pemisahan aset konsumen",
                    "Sistem keamanan cyber",
                    "Kewajiban audit rutin",
                    "Pelaporan transaksi mencurigakan"
                ]
            }
        }
    
    def _load_circulars(self) -> Dict[str, Dict[str, Any]]:
        """Load surat edaran OJK"""
        return {
            "SEOJK_14_2020": {
                "title": "SEOJK 14/2020 tentang Penerapan Manajemen Risiko",
                "effective_date": "2020-04-01",
                "scope": ["risk_management", "compliance"],
                "key_points": [
                    "Identifikasi risiko operasional",
                    "Pengukuran risiko",
                    "Pengendalian risiko",
                    "Pelaporan risiko"
                ]
            },
            "SEOJK_21_2021": {
                "title": "SEOJK 21/2021 tentang Pelaporan dan Transparansi",
                "effective_date": "2021-06-01",
                "scope": ["reporting", "transparency"],
                "key_points": [
                    "Format pelaporan standard",
                    "Frekuensi pelaporan",
                    "Publikasi informasi",
                    "Akses informasi publik"
                ]
            }
        }
    
    def _load_guidelines(self) -> Dict[str, Dict[str, Any]]:
        """Load pedoman teknis OJK"""
        return {
            "cyber_security_guidelines": {
                "title": "Pedoman Keamanan Siber untuk Fintech",
                "version": "2.0",
                "key_areas": [
                    "Keamanan infrastruktur",
                    "Manajemen identitas",
                    "Enkripsi data",
                    "Incident response"
                ]
            },
            "data_protection_guidelines": {
                "title": "Pedoman Perlindungan Data Pribadi",
                "version": "1.5",
                "key_areas": [
                    "Persyaratan persetujuan",
                    "Hak-hak konsumen",
                    "Keamanan data",
                    "Cross-border data transfer"
                ]
            }
        }
    
    def get_applicable_regulations(self, business_type: str) -> List[Dict[str, Any]]:
        """Dapatkan regulasi yang berlaku untuk jenis bisnis tertentu"""
        applicable = []
        
        for reg_id, reg_data in self.regulations.items():
            if business_type in reg_data["scope"]:
                applicable.append({
                    "regulation_id": reg_id,
                    "title": reg_data["title"],
                    "effective_date": reg_data["effective_date"],
                    "key_requirements": reg_data["key_requirements"]
                })
        
        return applicable


class OJKReportingSystem:
    """Sistem pelaporan untuk OJK"""
    
    def __init__(self):
        self.reports_db = {}
        self.submission_history = []
        self.report_templates = self._load_report_templates()
    
    def _load_report_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load template laporan OJK"""
        return {
            "monthly_transaction_report": {
                "fields": [
                    "total_transactions",
                    "total_volume",
                    "average_transaction_size",
                    "geographic_distribution",
                    "demographic_breakdown",
                    "suspicious_activities"
                ],
                "format": "XLSX",
                "deadline": "10th of following month"
            },
            "quarterly_risk_report": {
                "fields": [
                    "risk_assessment_summary",
                    "risk_mitigation_activities",
                    "incident_reports",
                    "compliance_violations",
                    "consumer_complaints"
                ],
                "format": "PDF",
                "deadline": "15th of month following quarter end"
            },
            "annual_compliance_report": {
                "fields": [
                    "compliance_status_summary",
                    "regulatory_changes_impact",
                    "training_activities",
                    "audit_results",
                    "remediation_actions"
                ],
                "format": "PDF",
                "deadline": "March 31st of following year"
            }
        }
    
    async def generate_monthly_report(self, month: int, year: int) -> TransactionReport:
        """Generate laporan bulanan"""
        report_id = str(uuid.uuid4())
        
        # Simulasi data transaksi (dalam implementasi nyata akan diambil dari database)
        total_transactions = 15000
        total_volume = 45000000000  # Rp 45 miliar
        suspicious_transactions = 23
        compliance_violations = 2
        data_quality_score = 0.95
        
        report = TransactionReport(
            report_id=report_id,
            report_type=ReportType.MONTHLY,
            reporting_period_start=datetime(year, month, 1),
            reporting_period_end=datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1),
            total_transactions=total_transactions,
            total_volume=total_volume,
            suspicious_transactions=suspicious_transactions,
            compliance_violations=compliance_violations,
            data_quality_score=data_quality_score,
            submission_date=datetime.now(),
            status="generated"
        )
        
        self.reports_db[report_id] = report
        return report
    
    async def submit_report_to_ojk(self, report_id: str) -> Dict[str, Any]:
        """Submit laporan ke OJK"""
        try:
            if report_id not in self.reports_db:
                return {
                    "success": False,
                    "error": "Report not found"
                }
            
            report = self.reports_db[report_id]
            
            # Simulasi pengiriman ke OJK (dalam implementasi nyata akan menggunakan API resmi)
            submission_result = {
                "submission_id": f"OJK-{report_id}",
                "status": "received",
                "timestamp": datetime.now(),
                "ojk_reference": f"OJK/REP/{datetime.now().strftime('%Y%m%d')}/{len(self.submission_history) + 1:04d}"
            }
            
            report.status = "submitted"
            self.submission_history.append(submission_result)
            
            return {
                "success": True,
                "submission_id": submission_result["submission_id"],
                "ojk_reference": submission_result["ojk_reference"],
                "status": submission_result["status"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class ConsumerProtectionSystem:
    """Sistem perlindungan konsumen sesuai regulasi OJK"""
    
    def __init__(self):
        self.complaints_db = {}
        self.dispute_resolution_records = []
        self.compensation_records = []
    
    async def file_complaint(self, complaint_data: Dict[str, Any]) -> Dict[str, Any]:
        """File keluhan konsumen"""
        try:
            complaint_id = str(uuid.uuid4())
            
            # Validasi data keluhan
            required_fields = ["consumer_id", "complaint_type", "description", "severity"]
            for field in required_fields:
                if field not in complaint_data:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }
            
            # Buat record keluhan
            record = ConsumerProtectionRecord(
                record_id=str(uuid.uuid4()),
                complaint_id=complaint_id,
                consumer_id=complaint_data["consumer_id"],
                complaint_type=complaint_data["complaint_type"],
                description=complaint_data["description"],
                severity=complaint_data["severity"],
                resolution_status="open",
                resolution_date=None,
                compensation_amount=0.0,
                ojk_escalation=False
            )
            
            self.complaints_db[complaint_id] = record
            
            return {
                "success": True,
                "complaint_id": complaint_id,
                "status": "open",
                "estimated_resolution_time": "14 business days"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def resolve_complaint(self, complaint_id: str, resolution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Selesaikan keluhan konsumen"""
        try:
            if complaint_id not in self.complaints_db:
                return {
                    "success": False,
                    "error": "Complaint not found"
                }
            
            record = self.complaints_db[complaint_id]
            record.resolution_status = resolution_data.get("status", "resolved")
            record.resolution_date = datetime.now()
            record.compensation_amount = resolution_data.get("compensation_amount", 0.0)
            
            # Cek apakah perlu eskalasi ke OJK
            if record.severity == "high" or resolution_data.get("ojk_escalation", False):
                record.ojk_escalation = True
                
                # Generate laporan untuk OJK
                ojk_report = {
                    "complaint_id": complaint_id,
                    "severity": record.severity,
                    "resolution_status": record.resolution_status,
                    "compensation_amount": record.compensation_amount,
                    "escalation_date": datetime.now(),
                    "report_reference": f"OJK/COM/{datetime.now().strftime('%Y%m%d')}/{complaint_id[:8]}"
                }
                
                return {
                    "success": True,
                    "status": "resolved_with_ojk_escalation",
                    "ojk_reference": ojk_report["report_reference"],
                    "compensation_amount": record.compensation_amount
                }
            
            return {
                "success": True,
                "status": "resolved",
                "resolution_date": record.resolution_date,
                "compensation_amount": record.compensation_amount
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_consumer_protection_stats(self) -> Dict[str, Any]:
        """Dapatkan statistik perlindungan konsumen"""
        total_complaints = len(self.complaints_db)
        
        status_breakdown = {}
        severity_breakdown = {}
        total_compensation = 0.0
        escalated_to_ojk = 0
        
        for record in self.complaints_db.values():
            status_breakdown[record.resolution_status] = status_breakdown.get(record.resolution_status, 0) + 1
            severity_breakdown[record.severity] = severity_breakdown.get(record.severity, 0) + 1
            total_compensation += record.compensation_amount
            
            if record.ojk_escalation:
                escalated_to_ojk += 1
        
        resolution_rate = (status_breakdown.get("resolved", 0) / total_complaints * 100) if total_complaints > 0 else 0
        
        return {
            "total_complaints": total_complaints,
            "status_breakdown": status_breakdown,
            "severity_breakdown": severity_breakdown,
            "total_compensation": total_compensation,
            "escalated_to_ojk": escalated_to_ojk,
            "resolution_rate": resolution_rate,
            "average_resolution_time": "12 days"  # Simulasi
        }


class OJKComplianceManager:
    """Manajer utama untuk kepatuhan OJK"""
    
    def __init__(self):
        self.regulation_db = OJKRegulationDatabase()
        self.reporting_system = OJKReportingSystem()
        self.consumer_protection = ConsumerProtectionSystem()
        
        self.compliance_requirements = {}
        self.risk_assessments = {}
        self.licenses = {}
        
        # Inisialisasi data kepatuhan
        self._initialize_compliance_data()
    
    def _initialize_compliance_data(self):
        """Inisialisasi data kepatuhan awal"""
        # Lisensi dummy
        self.licenses["SANGKURIANG_001"] = OJKLicense(
            license_id="SANGKURIANG_001",
            license_type=OJKLicenseType.CROWDFUNDING,
            license_number="OJK-CPF-2024-001",
            issue_date=datetime(2024, 1, 15),
            expiry_date=datetime(2027, 1, 15),
            status="active",
            scope_of_activities=["crowdfunding", "payment_processing", "digital_wallet"],
            conditions=["Maintain minimum capital", "Quarterly reporting", "Consumer protection compliance"],
            issuing_authority="OJK"
        )
    
    async def conduct_risk_assessment(self, entity_id: str) -> RiskAssessment:
        """Lakukan penilaian risiko"""
        assessment_id = str(uuid.uuid4())
        
        # Simulasi penilaian risiko
        risk_factors = {
            "operational_risk": 0.3,
            "credit_risk": 0.2,
            "market_risk": 0.15,
            "liquidity_risk": 0.2,
            "compliance_risk": 0.15
        }
        
        overall_risk_score = sum(risk_factors.values()) / len(risk_factors)
        
        # Tentukan kategori risiko
        if overall_risk_score >= 0.8:
            risk_category = RiskCategory.EXTREME
        elif overall_risk_score >= 0.6:
            risk_category = RiskCategory.HIGH
        elif overall_risk_score >= 0.4:
            risk_category = RiskCategory.MODERATE
        else:
            risk_category = RiskCategory.LOW
        
        # Saran mitigasi risiko
        mitigation_measures = [
            "Enhance operational controls",
            "Improve compliance monitoring",
            "Strengthen cybersecurity measures",
            "Regular risk review meetings"
        ]
        
        assessment = RiskAssessment(
            assessment_id=assessment_id,
            entity_id=entity_id,
            risk_category=risk_category,
            risk_score=overall_risk_score,
            risk_factors=risk_factors,
            mitigation_measures=mitigation_measures,
            next_review_date=datetime.now() + timedelta(days=90),
            assessor="OJK_Compliance_System",
            assessment_date=datetime.now()
        )
        
        self.risk_assessments[assessment_id] = assessment
        return assessment
    
    def submit_license_application(self, license_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit permohonan lisensi OJK"""
        try:
            application_id = str(uuid.uuid4())
            
            # Validasi data permohonan
            required_fields = ["license_type", "applicant_name", "business_address", "authorized_capital", "paid_up_capital"]
            for field in required_fields:
                if field not in license_data:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }
            
            # Simulasi proses permohonan
            return {
                "success": True,
                "application_id": application_id,
                "status": "submitted",
                "estimated_processing_time": "30-60 days",
                "next_steps": [
                    "Document verification",
                    "Business plan review",
                    "Technical assessment",
                    "Final approval"
                ]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def assess_risk_category(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """Penilaian kategori risiko bisnis"""
        try:
            # Faktor-faktor risiko
            risk_score = 0.0
            risk_factors = {}
            
            # Volume transaksi
            if "transaction_volume_monthly" in business_data:
                volume = float(business_data["transaction_volume_monthly"])
                if volume > 10000000000:  # > 10 miliar
                    risk_factors["transaction_volume"] = 0.3
                elif volume > 1000000000:  # > 1 miliar
                    risk_factors["transaction_volume"] = 0.2
                else:
                    risk_factors["transaction_volume"] = 0.1
            
            # Jumlah pelanggan
            if "number_of_customers" in business_data:
                customers = int(business_data["number_of_customers"])
                if customers > 100000:
                    risk_factors["customer_base"] = 0.2
                elif customers > 10000:
                    risk_factors["customer_base"] = 0.15
                else:
                    risk_factors["customer_base"] = 0.1
            
            # Jenis teknologi
            if "technology_platform" in business_data:
                tech = business_data["technology_platform"].lower()
                if "blockchain" in tech or "crypto" in tech:
                    risk_factors["technology_risk"] = 0.25
                else:
                    risk_factors["technology_risk"] = 0.1
            
            # Riwayat kepatuhan
            if "compliance_history" in business_data:
                history = business_data["compliance_history"].lower()
                if history == "clean":
                    risk_factors["compliance_history"] = 0.05
                else:
                    risk_factors["compliance_history"] = 0.15
            
            # Hitung total risiko
            risk_score = sum(risk_factors.values()) / len(risk_factors) if risk_factors else 0.0
            
            # Tentukan kategori risiko
            if risk_score >= 0.25:
                risk_category = RiskCategory.HIGH
            elif risk_score >= 0.15:
                risk_category = RiskCategory.MODERATE
            else:
                risk_category = RiskCategory.LOW
            
            return {
                "success": True,
                "risk_category": risk_category.value,
                "risk_score": risk_score,
                "risk_factors": risk_factors,
                "recommendations": [
                    "Implement enhanced monitoring systems",
                    "Regular compliance reviews",
                    "Strengthen risk management procedures"
                ]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate laporan untuk OJK"""
        try:
            report_id = str(uuid.uuid4())
            
            # Validasi data laporan
            required_fields = ["report_type", "reporting_period", "institution_id"]
            for field in required_fields:
                if field not in report_data:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }
            
            # Simulasi pembuatan laporan
            return {
                "success": True,
                "report_id": report_id,
                "status": "generated",
                "submission_deadline": (datetime.now() + timedelta(days=30)).isoformat(),
                "report_summary": {
                    "report_type": report_data["report_type"],
                    "period": report_data["reporting_period"],
                    "total_transactions": report_data.get("transaction_summary", {}).get("total_transactions", 0),
                    "compliance_status": report_data.get("compliance_status", "PENDING")
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def handle_consumer_complaint(self, complaint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle keluhan konsumen"""
        try:
            complaint_id = str(uuid.uuid4())
            
            # Validasi data keluhan
            required_fields = ["consumer_id", "complaint_type", "description"]
            for field in required_fields:
                if field not in complaint_data:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }
            
            # Simulasi penanganan keluhan
            return {
                "success": True,
                "complaint_id": complaint_id,
                "complaint_status": "received",
                "resolution_deadline": (datetime.now() + timedelta(days=14)).isoformat(),
                "estimated_resolution_time": "7-14 business days",
                "next_steps": [
                    "Investigation",
                    "Customer communication",
                    "Resolution",
                    "Follow-up"
                ]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_compliance_status(self) -> Dict[str, Any]:
        """Dapatkan status kepatuhan keseluruhan"""
        total_requirements = len(self.compliance_requirements)
        compliant_requirements = sum(1 for req in self.compliance_requirements.values() 
                                   if req.status == ComplianceStatus.COMPLIANT)
        
        compliance_rate = (compliant_requirements / total_requirements * 100) if total_requirements > 0 else 0
        
        # Status lisensi
        active_licenses = sum(1 for license in self.licenses.values() if license.status == "active")
        expired_licenses = sum(1 for license in self.licenses.values() if license.status == "expired")
        
        # Statistik konsumen
        consumer_stats = self.consumer_protection.get_consumer_protection_stats()
        
        return {
            "overall_compliance_rate": compliance_rate,
            "total_requirements": total_requirements,
            "compliant_requirements": compliant_requirements,
            "active_licenses": active_licenses,
            "expired_licenses": expired_licenses,
            "consumer_protection_stats": consumer_stats,
            "last_assessment_date": datetime.now(),
            "next_review_date": datetime.now() + timedelta(days=30)
        }
    
    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate laporan kepatuhan lengkap untuk OJK"""
        status = self.get_compliance_status()
        
        return {
            "report_id": f"OJK-COMP-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "generated_date": datetime.now(),
            "compliance_summary": status,
            "applicable_regulations": self.regulation_db.get_applicable_regulations("fintech"),
            "recommendations": [
                "Continue monitoring consumer complaints",
                "Ensure timely reporting to OJK",
                "Maintain adequate capital requirements",
                "Regular review of risk management procedures"
            ],
            "next_actions": [
                "Submit monthly transaction report",
                "Conduct quarterly risk assessment",
                "Review and update compliance procedures",
                "Prepare for annual OJK audit"
            ]
        }


# Contoh penggunaan
async def main():
    """Demo penggunaan OJK Compliance Module"""
    
    # Inisialisasi manajer kepatuhan
    compliance_manager = OJKComplianceManager()
    
    print("=== SANGKURIANG OJK Compliance Module Demo ===\n")
    
    # 1. Conduct risk assessment
    print("1. Conducting risk assessment...")
    risk_assessment = await compliance_manager.conduct_risk_assessment("SANGKURIANG_ENTITY_001")
    
    print(f"   ✓ Risk Assessment Completed")
    print(f"   - Assessment ID: {risk_assessment.assessment_id}")
    print(f"   - Risk Category: {risk_assessment.risk_category.value}")
    print(f"   - Risk Score: {risk_assessment.risk_score:.2f}")
    print(f"   - Next Review: {risk_assessment.next_review_date.strftime('%Y-%m-%d')}")
    
    print()
    
    # 2. Generate monthly report
    print("2. Generating monthly report...")
    monthly_report = await compliance_manager.reporting_system.generate_monthly_report(
        datetime.now().month, datetime.now().year
    )
    
    print(f"   ✓ Monthly Report Generated")
    print(f"   - Report ID: {monthly_report.report_id}")
    print(f"   - Total Transactions: {monthly_report.total_transactions:,}")
    print(f"   - Total Volume: Rp {monthly_report.total_volume:,.0f}")
    print(f"   - Suspicious Transactions: {monthly_report.suspicious_transactions}")
    
    # Submit report to OJK
    submission_result = await compliance_manager.reporting_system.submit_report_to_ojk(monthly_report.report_id)
    
    if submission_result["success"]:
        print(f"   ✓ Report Submitted to OJK")
        print(f"   - OJK Reference: {submission_result['ojk_reference']}")
    
    print()
    
    # 3. Handle consumer complaint
    print("3. Handling consumer complaint...")
    complaint_data = {
        "consumer_id": "CONSUMER_001",
        "complaint_type": "service_disruption",
        "description": "Platform tidak dapat diakses selama 2 jam",
        "severity": "medium"
    }
    
    complaint_result = await compliance_manager.consumer_protection.file_complaint(complaint_data)
    
    if complaint_result["success"]:
        print(f"   ✓ Complaint Filed")
        print(f"   - Complaint ID: {complaint_result['complaint_id']}")
        print(f"   - Estimated Resolution: {complaint_result['estimated_resolution_time']}")
        
        # Resolve complaint
        resolution_data = {
            "status": "resolved",
            "compensation_amount": 500000,  # Rp 500 ribu
            "ojk_escalation": False
        }
        
        resolution_result = await compliance_manager.consumer_protection.resolve_complaint(
            complaint_result["complaint_id"], resolution_data
        )
        
        if resolution_result["success"]:
            print(f"   ✓ Complaint Resolved")
            print(f"   - Compensation: Rp {resolution_result['compensation_amount']:,}")
    
    print()
    
    # 4. Get compliance status
    print("4. Getting compliance status...")
    compliance_status = compliance_manager.get_compliance_status()
    
    print(f"   ✓ Compliance Status Retrieved")
    print(f"   - Overall Compliance Rate: {compliance_status['overall_compliance_rate']:.1f}%")
    print(f"   - Active Licenses: {compliance_status['active_licenses']}")
    print(f"   - Total Consumer Complaints: {compliance_status['consumer_protection_stats']['total_complaints']}")
    print(f"   - Resolution Rate: {compliance_status['consumer_protection_stats']['resolution_rate']:.1f}%")
    
    print()
    
    # 5. Generate comprehensive compliance report
    print("5. Generating comprehensive compliance report...")
    compliance_report = compliance_manager.generate_compliance_report()
    
    print(f"   ✓ Compliance Report Generated")
    print(f"   - Report ID: {compliance_report['report_id']}")
    print(f"   - Generated Date: {compliance_report['generated_date'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   - Applicable Regulations: {len(compliance_report['applicable_regulations'])}")
    print(f"   - Next Actions: {len(compliance_report['next_actions'])}")
    
    print("\n=== Demo completed successfully! ===")


if __name__ == "__main__":
    asyncio.run(main())