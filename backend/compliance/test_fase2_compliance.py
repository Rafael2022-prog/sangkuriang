"""
Test untuk Fase 2: Security & Compliance - Regulatory Compliance
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from compliance.kyc_aml_system import KYCAMLSystem
from compliance.ojk_compliance import OJKComplianceManager
from compliance.pdp_law_compliance import PDPLawComplianceManager
from compliance.tax_reporting_system import TaxReportingManager, ReportPeriod


class TestKYCAMLSystem:
    """Test untuk KYC/AML System"""
    
    @pytest.fixture
    def kyc_aml_system(self):
        return KYCAMLSystem()
    
    def test_initialization(self, kyc_aml_system):
        """Test inisialisasi KYC/AML system"""
        assert kyc_aml_system is not None
        assert len(kyc_aml_system.document_verifiers) > 0
        assert kyc_aml_system.sanctions_database is not None
    
    @pytest.mark.asyncio
    async def test_kyc_application_submission(self, kyc_aml_system):
        """Test pengajuan aplikasi KYC"""
        application_data = {
            "user_id": "USER_001",
            "full_name": "John Doe",
            "date_of_birth": "1990-01-01",
            "nationality": "Indonesia",
            "phone_number": "+6281234567890",
            "email": "john.doe@example.com",
            "address": "Jl. Sudirman No. 123, Jakarta",
            "occupation": "Software Engineer",
            "source_of_funds": "Salary",
            "estimated_monthly_volume": "50000000",
            "documents": [
                {"type": "ktp", "document_id": "1234567890123456"},
                {"type": "npwp", "document_id": "123456789012345"}
            ]
        }
        
        result = await kyc_aml_system.submit_kyc_application(application_data)
        
        assert result["success"] is True
        assert "application_id" in result
        assert "verification_status" in result
        assert result["verification_status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_document_verification(self, kyc_aml_system):
        """Test verifikasi dokumen"""
        document_data = {
            "document_type": "ktp",
            "document_id": "1234567890123456",
            "document_image": "base64_encoded_image_data",
            "user_id": "USER_001"
        }
        
        result = await kyc_aml_system.verify_document(document_data)
        
        assert result["success"] is True
        assert "verification_result" in result
        assert "document_status" in result["verification_result"]
    
    @pytest.mark.asyncio
    async def test_aml_screening(self, kyc_aml_system):
        """Test AML screening"""
        user_data = {
            "full_name": "John Doe",
            "nationality": "Indonesia",
            "date_of_birth": "1990-01-01",
            "address": "Jl. Sudirman No. 123, Jakarta"
        }
        
        result = await kyc_aml_system.screen_aml(user_data)
        
        assert result["success"] is True
        assert "aml_screening_result" in result
        assert "risk_level" in result["aml_screening_result"]
        assert "sanctions_check" in result["aml_screening_result"]
    
    @pytest.mark.asyncio
    async def test_transaction_monitoring(self, kyc_aml_system):
        """Test pemantauan transaksi"""
        transaction_data = {
            "transaction_id": "TXN_001",
            "user_id": "USER_001",
            "transaction_type": "crypto_purchase",
            "amount": "100000000",  # 100 juta IDR
            "currency": "IDR",
            "counterparty": "EXCHANGE_001",
            "transaction_date": datetime.now().isoformat()
        }
        
        result = await kyc_aml_system.monitor_transaction(transaction_data)
        
        assert result["success"] is True
        assert "monitoring_result" in result
        assert "alert_triggered" in result["monitoring_result"]
        assert "risk_score" in result["monitoring_result"]


class TestOJKCompliance:
    """Test untuk OJK Compliance"""
    
    @pytest.fixture
    def ojk_compliance(self):
        return OJKComplianceManager()
    
    def test_initialization(self, ojk_compliance):
        """Test inisialisasi OJK compliance"""
        assert ojk_compliance is not None
        assert ojk_compliance.regulation_db is not None
        assert ojk_compliance.reporting_system is not None
    
    def test_license_management(self, ojk_compliance):
        """Test manajemen lisensi OJK"""
        license_data = {
            "license_type": "PAYMENT_SERVICE_PROVIDER",
            "applicant_name": "SANGKURIANG PT",
            "business_address": "Jakarta",
            "authorized_capital": "10000000000",  # 10 miliar
            "paid_up_capital": "2500000000",  # 2.5 miliar
            "directors": [
                {"name": "Director 1", "id_number": "123456789"},
                {"name": "Director 2", "id_number": "987654321"}
            ],
            "compliance_officer": {"name": "Compliance Officer", "certification": "OJK"}
        }
        
        result = ojk_compliance.submit_license_application(license_data)
        
        assert result["success"] is True
        assert "application_id" in result
        assert "status" in result
    
    def test_risk_assessment(self, ojk_compliance):
        """Test penilaian risiko OJK"""
        business_data = {
            "business_type": "CRYPTO_EXCHANGE",
            "transaction_volume_monthly": "5000000000",  # 5 miliar
            "number_of_customers": 10000,
            "geographical_coverage": ["Indonesia"],
            "technology_platform": "blockchain",
            "compliance_history": "clean"
        }
        
        result = ojk_compliance.assess_risk_category(business_data)
        
        assert result["success"] is True
        assert "risk_category" in result
        assert "risk_score" in result
        assert result["risk_category"] in ["LOW", "MODERATE", "HIGH"]
    
    def test_reporting_generation(self, ojk_compliance):
        """Test pembuatan laporan OJK"""
        report_data = {
            "report_type": "MONTHLY_TRANSACTION_REPORT",
            "reporting_period": "2024-01",
            "institution_id": "SANGKURIANG_001",
            "transaction_summary": {
                "total_transactions": 1000,
                "total_volume": "5000000000",
                "total_fees": "50000000",
                "number_of_customers": 5000
            },
            "compliance_status": "COMPLIANT",
            "risk_indicators": []
        }
        
        result = ojk_compliance.generate_report(report_data)
        
        assert result["success"] is True
        assert "report_id" in result
        assert "submission_deadline" in result
        assert "report_status" in result
    
    def test_consumer_protection(self, ojk_compliance):
        """Test perlindungan konsumen OJK"""
        complaint_data = {
            "complaint_id": "COMP_001",
            "customer_id": "CUST_001",
            "complaint_type": "TRANSACTION_DISPUTE",
            "complaint_description": "Unauthorized transaction",
            "transaction_reference": "TXN_001",
            "amount_disputed": "1000000",
            "complaint_date": datetime.now().isoformat()
        }
        
        result = ojk_compliance.handle_consumer_complaint(complaint_data)
        
        assert result["success"] is True
        assert "complaint_status" in result
        assert "resolution_deadline" in result


class TestPDPCompliance:
    """Test untuk PDP Law Compliance"""
    
    @pytest.fixture
    def pdp_compliance(self):
        return PDPLawComplianceManager()
    
    def test_initialization(self, pdp_compliance):
        """Test inisialisasi PDP compliance"""
        assert pdp_compliance is not None
        assert pdp_compliance.consent_management is not None
        assert pdp_compliance.breach_management is not None
    
    @pytest.mark.asyncio
    async def test_consent_management(self, pdp_compliance):
        """Test manajemen persetujuan"""
        consent_data = {
            "user_id": "USER_001",
            "consent_text": "Saya setuju untuk pemrosesan data pribadi saya",
            "data_categories": ["personal_identity", "contact_information"],
            "purposes": ["service_provision", "legal_obligation"]
        }
        
        result = await pdp_compliance.record_consent_async(consent_data)
        
        print(f"Consent result: {result}")  # Debug output
        assert result["success"] is True
        assert "consent_id" in result
        assert "consent_status" in result
        assert result["consent_status"] == "ACTIVE"
    
    @pytest.mark.asyncio
    async def test_data_processing_registration(self, pdp_compliance):
        """Test registrasi aktivitas pemrosesan data"""
        processing_data = {
            "activity_name": "Customer KYC Processing",
            "data_categories": ["personal_identity", "financial_data"],
            "processing_purposes": ["service_provision", "legal_obligation"],
            "legal_basis": "consent",
            "data_subjects_count": 100,
            "data_retention": "7 years",
            "third_parties": ["payment_processors"],
            "international_transfer": False,
            "automated_decision_making": False,
            "risk_assessment": "low",
            "dpia_conducted": False
        }
        
        result = await pdp_compliance.register_data_processing_activity(processing_data)
        
        assert result["success"] is True
        assert "activity_id" in result
        assert "status" in result
    
    @pytest.mark.asyncio
    async def test_data_breach_management(self, pdp_compliance):
        """Test manajemen pelanggaran data"""
        breach_data = {
            "breach_type": "UNAUTHORIZED_ACCESS",
            "affected_data_categories": ["personal_identity", "contact_information"],
            "affected_individuals": 1000
        }
        
        result = await pdp_compliance.handle_data_breach_async(breach_data)

        print(f"Breach result: {result}")  # Debug output
        assert result["success"] is True
        assert "breach_response" in result
        assert "notification_deadline" in result["breach_response"]
        assert "required_actions" in result["breach_response"]
    
    @pytest.mark.asyncio
    async def test_data_subject_rights(self, pdp_compliance):
        """Test hak subjek data"""
        rights_request = {
            "data_subject_id": "USER_001",
            "request_type": "ACCESS_REQUEST"
        }
        
        result = await pdp_compliance.process_data_subject_request_async(rights_request)
        
        assert result["success"] is True
        assert "request_status" in result
        assert "response_deadline" in result
        assert result["request_status"] == "PROCESSING"


class TestTaxReportingSystem:
    """Test untuk Tax Reporting System"""
    
    @pytest.fixture
    def tax_manager(self):
        print("DEBUG: Creating TaxReportingManager")
        manager = TaxReportingManager(storage_path="test_tax_reports")
        print(f"DEBUG: Created manager with storage: {manager.storage_path}")
        return manager
    
    def test_initialization(self, tax_manager):
        """Test inisialisasi tax reporting manager"""
        assert tax_manager is not None
        assert tax_manager.tax_rate_db is not None
        assert tax_manager.transaction_processor is not None
        assert tax_manager.tax_calculator is not None
    
    @pytest.mark.asyncio
    async def test_crypto_transaction_processing(self, tax_manager):
        """Test pemrosesan transaksi kripto"""
        transaction_data = {
            "user_id": "USER_001",
            "taxpayer_id": "NPWP_123456789",
            "taxpayer_type": "individual",
            "transaction_type": "crypto_sale",
            "amount_crypto": "0.1",
            "amount_idr": "95000000",  # 0.1 BTC * 950 juta IDR per BTC
            "crypto_currency": "BTC",
            "transaction_date": datetime.now().isoformat(),
            "fees_idr": "50000",
            "description": "Sale of 0.1 BTC",
            "reference_number": "TXN-001",
            "location": "Jakarta",
            "payment_method": "bank_transfer"
        }
        
        result = await tax_manager.process_crypto_transaction(transaction_data)
        
        assert result["success"] is True
        assert "transaction_id" in result
        assert "tax_withheld" in result
        assert float(result["tax_withheld"]) > 0
    
    @pytest.mark.asyncio
    async def test_monthly_tax_calculation(self, tax_manager):
        """Test perhitungan pajak bulanan"""
        print("=== STARTING MONTHLY TAX CALCULATION TEST ===")
        
        # Data transaksi untuk satu bulan - menggunakan data yang terbukti berhasil
        transactions = [
            {
                "user_id": "USER_001",
                "taxpayer_id": "NPWP_123456789",
                "taxpayer_type": "individual",
                "transaction_type": "crypto_sale",
                "amount_crypto": "0.05",
                "amount_idr": "47500000",  # 47.5 juta IDR
                "crypto_currency": "BTC",
                "transaction_date": "2024-01-15T10:00:00",
                "fees_idr": "25000",
                "description": "Sale of 0.05 BTC",
                "reference_number": "TXN-001",
                "location": "Jakarta",
                "payment_method": "bank_transfer"
            }
        ]

        # Proses transaksi
        print(f"DEBUG: Processing {len(transactions)} transactions...")
        for i, transaction_data in enumerate(transactions):
            print(f"DEBUG: Processing transaction {i+1}...")
            result = await tax_manager.process_crypto_transaction(transaction_data)
            print(f"DEBUG: Transaction {i+1} result: success={result.get('success')}, id={result.get('transaction_id')}")
            assert result["success"] is True
            assert "transaction_id" in result

        # Hitung pajak bulanan - ini akan otomatis mendapatkan transaksi yang tersimpan
        print(f"DEBUG: Calling calculate_monthly_tax...")
        result = await tax_manager.calculate_monthly_tax("NPWP_123456789", "2024-01")
        print(f"DEBUG: Tax calculation result: {result}")

        # Verifikasi hasil
        assert result["success"] is True, f"Tax calculation failed: {result.get('error')}"
        assert "total_tax_payable" in result, "Missing total_tax_payable in result"
        
        total_tax = float(result["total_tax_payable"])
        print(f"DEBUG: Total tax payable: {total_tax}")
        
        # Verifikasi bahwa pajak yang dihitung masuk akal
        assert total_tax > 0, f"Expected tax > 0, but got {total_tax}. Full result: {result}"
        
        # Jika ada tax_breakdown, verifikasi isinya
        if "tax_breakdown" in result:
            print(f"DEBUG: Tax breakdown: {result['tax_breakdown']}")
            for tax_type, breakdown in result["tax_breakdown"].items():
                assert float(breakdown["tax_amount"]) >= 0, f"Invalid tax amount for {tax_type}"
        
        # Verifikasi due_date ada dan valid (format ISO datetime)
        assert "due_date" in result, "Missing due_date in result"
        from datetime import datetime
        due_date_str = result["due_date"]
        # Parse ISO datetime string
        if 'T' in due_date_str:
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
        else:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
        
        # Untuk Januari 2024, due date seharusnya Februari 2024
        assert due_date.year == 2024 and due_date.month == 2, f"Due date should be Feb 2024, got: {due_date}"
        assert "due_date" in result
    
    @pytest.mark.asyncio
    async def test_tax_report_generation(self, tax_manager):
        """Test pembuatan laporan pajak"""
        # Proses transaksi terlebih dahulu
        transaction_data = {
            "user_id": "USER_001",
            "taxpayer_id": "NPWP_123456789",
            "taxpayer_type": "individual",
            "transaction_type": "crypto_sale",
            "amount_crypto": "0.1",
            "amount_idr": "95000000",  # 0.1 BTC * 950 juta IDR per BTC
            "crypto_currency": "BTC",
            "transaction_date": datetime.now().isoformat(),
            "fees_idr": "50000",
            "description": "Sale of 0.1 BTC",
            "reference_number": "TXN-001",
            "location": "Jakarta",
            "payment_method": "bank_transfer"
        }
        
        await tax_manager.process_crypto_transaction(transaction_data)
        
        # Generate laporan pajak
        result = await tax_manager.generate_tax_report("NPWP_123456789", "2024-01", ReportPeriod.MONTHLY)
        
        assert result["success"] is True
        assert "report_id" in result
        assert "total_tax_liability" in result
        assert "status" in result
    
    @pytest.mark.asyncio
    async def test_tax_payment_processing(self, tax_manager):
        """Test pemrosesan pembayaran pajak"""
        # Hitung pajak terlebih dahulu
        await tax_manager.calculate_monthly_tax("NPWP_123456789", "2024-01")
        
        payment_data = {
            "taxpayer_id": "NPWP_123456789",
            "liability_id": "TAX-NPWP_123456789-2024-01",
            "payment_amount": "9500000",  # Rp 9.5 juta
            "payment_method": "virtual_account",
            "tax_type": "final_tax",
            "tax_period": "2024-01",
            "notes": "Payment for January 2024 crypto taxes"
        }
        
        result = await tax_manager.process_tax_payment(payment_data)
        
        assert result["success"] is True
        assert "payment_id" in result
        assert "bank_reference" in result
        assert "processing_fee" in result
    
    def test_taxpayer_summary(self, tax_manager):
        """Test ringkasan status pajak taxpayer"""
        summary = tax_manager.get_taxpayer_summary("NPWP_123456789")
        
        assert summary["taxpayer_id"] == "NPWP_123456789"
        assert "tax_summary" in summary
        assert "payment_history" in summary
        assert "compliance_status" in summary
        assert "last_updated" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])