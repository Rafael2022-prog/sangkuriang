"""
Test untuk Fase 2: Security & Compliance - Security Enhancement
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'crypto-audit'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from advanced_engine import AdvancedCryptoAuditEngine
from vulnerability_scanner import AutomatedVulnerabilityScanner
from penetration_testing import WebApplicationTester, APITester
from security_certification import SecurityCertificationEngine


class TestAdvancedCryptoAuditEngine:
    """Test untuk Advanced Crypto Audit Engine"""
    
    @pytest.fixture
    def audit_engine(self):
        return AdvancedCryptoAuditEngine()
    
    def test_initialization(self, audit_engine):
        """Test inisialisasi engine"""
        assert audit_engine is not None
        assert len(audit_engine.vulnerability_patterns) > 0
        assert len(audit_engine.nist_standards) > 0
        assert len(audit_engine.iso_standards) > 0
    
    @pytest.mark.asyncio
    async def test_comprehensive_audit(self, audit_engine):
        """Test comprehensive audit dengan kode yang aman"""
        safe_code = '''
import hashlib
import secrets
from cryptography.fernet import Fernet

# Generate secure key
key = Fernet.generate_key()
cipher = Fernet(key)

# Secure random number generation
secure_random = secrets.token_bytes(32)

# Proper password hashing
def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_bytes(32)
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)

# Secure encryption
def encrypt_data(data, key):
    return cipher.encrypt(data.encode())
'''
        
        result = await audit_engine.comprehensive_audit(safe_code, "test_safe.py")
        
        assert result["success"] is True
        assert "audit_results" in result
        assert "vulnerability_count" in result["audit_results"]
        assert result["audit_results"]["vulnerability_count"] == 0
    
    @pytest.mark.asyncio
    async def test_vulnerability_detection(self, audit_engine):
        """Test deteksi kerentanan"""
        vulnerable_code = '''
import random
import hashlib

# Weak random number generation
weak_key = random.randint(0, 1000)

# Weak hashing without salt
def weak_hash(password):
    return hashlib.md5(password.encode()).hexdigest()

# Timing attack vulnerability
def check_password(password, stored_hash):
    if password == stored_hash:  # Direct comparison - timing attack
        return True
    return False
'''
        
        result = await audit_engine.comprehensive_audit(vulnerable_code, "test_vulnerable.py")
        
        assert result["success"] is True
        assert result["audit_results"]["vulnerability_count"] > 0
        assert len(result["audit_results"]["vulnerabilities"]) > 0
    
    def test_quantum_resistance_check(self, audit_engine):
        """Test quantum resistance check"""
        # Test dengan algoritma yang rentan terhadap quantum
        vulnerable_crypto = {
            "algorithm": "RSA",
            "key_size": 1024,
            "usage": "encryption"
        }
        
        result = audit_engine.check_quantum_resistance(vulnerable_crypto)
        assert result["quantum_safe"] is False
        assert "quantum_risk_level" in result
    
    def test_nist_compliance(self, audit_engine):
        """Test NIST compliance check"""
        compliant_config = {
            "encryption_algorithm": "AES-256-GCM",
            "key_derivation": "PBKDF2-HMAC-SHA256",
            "random_number_generator": "NIST_SP_800_90A"
        }
        
        result = audit_engine.check_nist_compliance(compliant_config)
        assert result["nist_compliant"] is True
        assert len(result["compliance_issues"]) == 0


class TestVulnerabilityScanner:
    """Test untuk Automated Vulnerability Scanner"""
    
    @pytest.fixture
    def scanner(self):
        return AutomatedVulnerabilityScanner()
    
    def test_initialization(self, scanner):
        """Test inisialisasi scanner"""
        assert scanner is not None
        assert len(scanner.vulnerability_db) > 0
        assert len(scanner.cve_database) > 0
    
    @pytest.mark.asyncio
    async def test_comprehensive_scan(self, scanner):
        """Test comprehensive vulnerability scan"""
        # Mock target system
        target_config = {
            "target_url": "http://localhost:8000",
            "target_type": "web_application",
            "scan_depth": "comprehensive"
        }
        
        result = await scanner.comprehensive_scan(target_config)
        
        assert result["success"] is True
        assert "scan_results" in result
        assert "total_vulnerabilities" in result["scan_results"]
        assert "risk_score" in result["scan_results"]
    
    def test_crypto_vulnerability_scan(self, scanner):
        """Test crypto vulnerability scan"""
        crypto_config = {
            "algorithms": ["AES-128", "RSA-1024", "MD5"],
            "key_sizes": [1024, 2048],
            "protocols": ["SSLv3", "TLS 1.0", "TLS 1.2"]
        }
        
        result = scanner.scan_crypto_vulnerabilities(crypto_config)
        assert "crypto_vulnerabilities" in result
        assert len(result["crypto_vulnerabilities"]) >= 0
    
    def test_compliance_scan(self, scanner):
        """Test compliance scan"""
        compliance_config = {
            "standards": ["ISO27001", "NIST", "GDPR"],
            "jurisdiction": "Indonesia"
        }
        
        result = scanner.scan_compliance_violations(compliance_config)
        assert "compliance_violations" in result
        assert "compliance_score" in result


class TestPenetrationTesting:
    """Test untuk Penetration Testing Framework"""
    
    @pytest.fixture
    def web_tester(self):
        return WebApplicationTester()
    
    @pytest.fixture
    def api_tester(self):
        return APITester()
    
    @pytest.mark.asyncio
    async def test_web_application_testing(self, web_tester):
        """Test web application penetration testing"""
        target_config = {
            "target_url": "http://localhost:8000",
            "test_categories": ["sql_injection", "xss", "path_traversal"],
            "auth_required": False
        }
        
        result = await web_tester.run_comprehensive_test(target_config)
        
        assert result["success"] is True
        assert "test_results" in result
        assert "total_tests_run" in result["test_results"]
        assert "vulnerabilities_found" in result["test_results"]
    
    @pytest.mark.asyncio
    async def test_api_security_testing(self, api_tester):
        """Test API security testing"""
        api_config = {
            "base_url": "http://localhost:8000/api",
            "endpoints": ["/users", "/projects", "/funding"],
            "auth_token": "test_token"
        }
        
        result = await api_tester.test_api_endpoints(api_config)
        
        assert result["success"] is True
        assert "api_test_results" in result
        assert "endpoints_tested" in result["api_test_results"]
    
    def test_payload_generation(self):
        """Test payload generation"""
        from security.penetration_testing import PayloadGenerator
        
        generator = PayloadGenerator()
        
        # Test SQL injection payloads
        sql_payloads = generator.generate_sql_injection_payloads()
        assert len(sql_payloads) > 0
        assert "' OR 1=1--" in sql_payloads
        
        # Test XSS payloads
        xss_payloads = generator.generate_xss_payloads()
        assert len(xss_payloads) > 0
        assert "<script>alert('XSS')</script>" in xss_payloads


class TestSecurityCertification:
    """Test untuk Security Certification Engine"""
    
    @pytest.fixture
    def cert_engine(self):
        return SecurityCertificationEngine()
    
    def test_initialization(self, cert_engine):
        """Test inisialisasi certification engine"""
        assert cert_engine is not None
        assert len(cert_engine.requirements_manager.requirements) > 0
    
    @pytest.mark.asyncio
    async def test_security_assessment(self, cert_engine):
        """Test security assessment"""
        system_config = {
            "system_name": "SANGKURIANG Test System",
            "components": ["web_server", "database", "api", "crypto_module"],
            "security_level": "high",
            "compliance_requirements": ["ISO27001", "NIST"]
        }
        
        result = await cert_engine.conduct_security_assessment(system_config)
        
        assert result["success"] is True
        assert "assessment_results" in result
        assert "compliance_score" in result["assessment_results"]
        assert "risk_level" in result["assessment_results"]
    
    @pytest.mark.asyncio
    async def test_certificate_issuance(self, cert_engine):
        """Test certificate issuance"""
        assessment_results = {
            "compliance_score": 95,
            "risk_level": "low",
            "critical_vulnerabilities": 0,
            "high_vulnerabilities": 1,
            "medium_vulnerabilities": 2,
            "low_vulnerabilities": 3
        }
        
        result = await cert_engine.issue_security_certificate(
            "SANGKURIANG-TEST-001",
            assessment_results,
            "SANGKURIANG Test System"
        )
        
        assert result["success"] is True
        assert "certificate" in result
        assert "certificate_id" in result["certificate"]
        assert "validity_period" in result["certificate"]
    
    def test_certificate_verification(self, cert_engine):
        """Test certificate verification"""
        # Create a test certificate
        cert_data = {
            "certificate_id": "CERT-TEST-001",
            "system_name": "Test System",
            "issued_date": datetime.now(),
            "expiry_date": datetime.now(),
            "compliance_level": "high",
            "assessment_score": 95
        }
        
        result = cert_engine.verify_certificate(cert_data)
        assert "valid" in result
        assert "verification_status" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])