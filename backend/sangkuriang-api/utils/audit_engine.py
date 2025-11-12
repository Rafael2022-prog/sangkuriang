import asyncio
import aiohttp
import json
import hashlib
import subprocess
import tempfile
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import re
from dataclasses import dataclass

@dataclass
class AuditResult:
    """Audit result data structure."""
    overall_score: float
    security_level: str
    findings: List[Dict[str, Any]]
    recommendations: List[str]
    analysis_summary: Dict[str, Any]

class AuditEngine:
    """Cryptographic audit engine for analyzing code security."""
    
    def __init__(self):
        self.security_standards = {
            "NIST": self.load_nist_standards(),
            "ISO": self.load_iso_standards(),
            "OWASP": self.load_owasp_guidelines()
        }
        
        self.vulnerability_patterns = {
            "weak_encryption": [
                r"md5\(",
                r"sha1\(",
                r"DES\(",
                r"RC4\(",
                r"ECB\(",
                r"AES\.ECB",
                r"DES3\.ECB"
            ],
            "hardcoded_secrets": [
                r"password\s*=\s*['\"][^'\"]{0,20}['\"]",
                r"api_key\s*=\s*['\"][^'\"]{0,50}['\"]",
                r"secret\s*=\s*['\"][^'\"]{0,50}['\"]",
                r"private_key\s*=\s*['\"].*['\"]",
                r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----"
            ],
            "weak_random": [
                r"random\.random\(",
                r"random\.randint\(",
                r"math\.random\(",
                r"new\s+Random\(\)"
            ],
            "crypto_misuse": [
                r"crypto\.createCipher\(",
                r"crypto\.createDecipher\(",
                r"EVP_EncryptInit_ex.*NULL.*NULL",
                r"EVP_DecryptInit_ex.*NULL.*NULL"
            ],
            "insecure_protocols": [
                r"http://",
                r"ftp://",
                r"telnet://",
                r"ssl://",
                r"tls://.*TLSv1(?!\.[0-9])"
            ]
        }
        
        self.quantum_safe_algorithms = [
            "CRYSTALS-Kyber", "CRYSTALS-Dilithium", "FALCON", "SPHINCS+",
            "BIKE", "Classic McEliece", "HQC", "SIKE"
        ]
        
        self.secure_algorithms = {
            "symmetric": ["AES-256", "AES-192", "AES-128", "ChaCha20", "XSalsa20"],
            "asymmetric": ["RSA-2048", "RSA-3072", "RSA-4096", "ECDSA", "EdDSA"],
            "hash": ["SHA-256", "SHA-384", "SHA-512", "SHA3-256", "SHA3-384", "SHA3-512", "BLAKE2b", "BLAKE2s"],
            "key_derivation": ["PBKDF2", "bcrypt", "scrypt", "Argon2"]
        }
    
    async def perform_security_audit(
        self, 
        repo_analysis: Dict[str, Any], 
        audit_type: str = "comprehensive"
    ) -> AuditResult:
        """Perform comprehensive security audit on repository."""
        
        findings = []
        recommendations = []
        analysis_summary = {
            "total_files": len(repo_analysis.get("files", [])),
            "crypto_files": 0,
            "vulnerabilities_found": 0,
            "quantum_safe": False,
            "compliance_score": 0.0
        }
        
        # Analyze each file
        for file_info in repo_analysis.get("files", []):
            if self.is_crypto_related(file_info):
                analysis_summary["crypto_files"] += 1
                file_findings = await self.analyze_file_security(file_info)
                findings.extend(file_findings)
        
        # Check for quantum resistance
        quantum_analysis = await self.analyze_quantum_safety(repo_analysis)
        analysis_summary["quantum_safe"] = quantum_analysis["is_quantum_safe"]
        
        # Check compliance with standards
        compliance_analysis = await self.analyze_compliance(repo_analysis)
        analysis_summary["compliance_score"] = compliance_analysis["score"]
        
        # Generate recommendations
        recommendations = self.generate_recommendations(findings, analysis_summary)
        
        # Calculate overall score
        overall_score = self.calculate_overall_score(findings, analysis_summary)
        
        # Determine security level
        security_level = self.determine_security_level(overall_score, findings)
        
        analysis_summary["vulnerabilities_found"] = len(findings)
        
        return AuditResult(
            overall_score=overall_score,
            security_level=security_level,
            findings=findings,
            recommendations=recommendations,
            analysis_summary=analysis_summary
        )
    
    def is_crypto_related(self, file_info: Dict[str, Any]) -> bool:
        """Check if file contains cryptographic code."""
        crypto_keywords = [
            "crypto", "encrypt", "decrypt", "cipher", "hash", "md5", "sha", "aes",
            "rsa", "signature", "verify", "key", "password", "auth", "token",
            "ssl", "tls", "https", "certificate", "random", "salt"
        ]
        
        file_path = file_info.get("path", "").lower()
        file_content = file_info.get("content", "").lower()
        
        # Check file extension
        crypto_extensions = [".py", ".js", ".java", ".cpp", ".c", ".go", ".rs"]
        if not any(file_path.endswith(ext) for ext in crypto_extensions):
            return False
        
        # Check for crypto keywords
        content_check = any(keyword in file_content for keyword in crypto_keywords)
        path_check = any(keyword in file_path for keyword in crypto_keywords)
        
        return content_check or path_check
    
    async def analyze_file_security(self, file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze individual file for security issues."""
        findings = []
        file_path = file_info.get("path", "")
        content = file_info.get("content", "")
        lines = content.split('\n')
        
        # Check for vulnerability patterns
        for vuln_type, patterns in self.vulnerability_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    findings.append({
                        "type": vuln_type,
                        "severity": self.get_severity(vuln_type),
                        "title": self.get_finding_title(vuln_type),
                        "description": self.get_finding_description(vuln_type, match.group()),
                        "recommendation": self.get_recommendation(vuln_type),
                        "file_path": file_path,
                        "line_number": line_num,
                        "matched_code": match.group().strip()
                    })
        
        # Check for secure algorithm usage
        secure_findings = await self.analyze_secure_algorithms(content, file_path)
        findings.extend(secure_findings)
        
        # Check for proper key management
        key_mgmt_findings = await self.analyze_key_management(content, file_path)
        findings.extend(key_mgmt_findings)
        
        return findings
    
    def get_severity(self, vuln_type: str) -> str:
        """Get severity level for vulnerability type."""
        severity_map = {
            "weak_encryption": "critical",
            "hardcoded_secrets": "critical",
            "crypto_misuse": "high",
            "weak_random": "high",
            "insecure_protocols": "medium"
        }
        return severity_map.get(vuln_type, "low")
    
    def get_finding_title(self, vuln_type: str) -> str:
        """Get title for finding type."""
        title_map = {
            "weak_encryption": "Weak Encryption Algorithm",
            "hardcoded_secrets": "Hardcoded Secrets",
            "crypto_misuse": "Cryptographic Misuse",
            "weak_random": "Weak Random Number Generation",
            "insecure_protocols": "Insecure Communication Protocol"
        }
        return title_map.get(vuln_type, "Security Issue")
    
    def get_finding_description(self, vuln_type: str, matched_code: str) -> str:
        """Get description for finding."""
        desc_map = {
            "weak_encryption": f"Detected usage of weak encryption algorithm: {matched_code}",
            "hardcoded_secrets": f"Found hardcoded secret in code: {matched_code[:50]}...",
            "crypto_misuse": f"Cryptographic function used incorrectly: {matched_code}",
            "weak_random": f"Weak random number generator used: {matched_code}",
            "insecure_protocols": f"Insecure protocol detected: {matched_code}"
        }
        return desc_map.get(vuln_type, f"Security issue detected: {matched_code}")
    
    def get_recommendation(self, vuln_type: str) -> str:
        """Get recommendation for fixing the issue."""
        rec_map = {
            "weak_encryption": "Use AES-256, ChaCha20, or other modern encryption algorithms",
            "hardcoded_secrets": "Store secrets in environment variables or secure key management systems",
            "crypto_misuse": "Follow cryptographic best practices and use established libraries",
            "weak_random": "Use cryptographically secure random number generators (CSPRNG)",
            "insecure_protocols": "Use HTTPS, TLS 1.3, or other secure communication protocols"
        }
        return rec_map.get(vuln_type, "Review and fix the security issue")
    
    async def analyze_secure_algorithms(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Analyze usage of secure algorithms."""
        findings = []
        
        # Check for secure symmetric encryption
        secure_symmetric = ["AES-256", "ChaCha20", "XSalsa20"]
        for algorithm in secure_symmetric:
            if algorithm.lower() in content.lower():
                findings.append({
                    "type": "secure_algorithm",
                    "severity": "info",
                    "title": "Secure Algorithm Usage",
                    "description": f"Found usage of secure algorithm: {algorithm}",
                    "recommendation": "Good practice - continue using secure algorithms",
                    "file_path": file_path,
                    "line_number": 0,
                    "matched_code": algorithm
                })
        
        return findings
    
    async def analyze_key_management(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Analyze key management practices."""
        findings = []
        
        # Check for key derivation functions
        kdf_patterns = ["PBKDF2", "bcrypt", "scrypt", "Argon2"]
        for pattern in kdf_patterns:
            if pattern.lower() in content.lower():
                findings.append({
                    "type": "secure_key_management",
                    "severity": "info",
                    "title": "Secure Key Derivation",
                    "description": f"Found usage of secure key derivation function: {pattern}",
                    "recommendation": "Good practice - using secure key derivation",
                    "file_path": file_path,
                    "line_number": 0,
                    "matched_code": pattern
                })
        
        return findings
    
    async def analyze_quantum_safety(self, repo_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze quantum resistance of cryptographic implementations."""
        is_quantum_safe = False
        quantum_algorithms_found = []
        
        for file_info in repo_analysis.get("files", []):
            content = file_info.get("content", "")
            
            for algorithm in self.quantum_safe_algorithms:
                if algorithm.lower() in content.lower():
                    quantum_algorithms_found.append(algorithm)
                    is_quantum_safe = True
        
        return {
            "is_quantum_safe": is_quantum_safe,
            "quantum_algorithms": quantum_algorithms_found,
            "recommendation": "Consider implementing quantum-resistant algorithms" if not is_quantum_safe else "Good quantum resistance"
        }
    
    async def analyze_compliance(self, repo_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze compliance with security standards."""
        compliance_score = 0.0
        compliance_issues = []
        
        # Check for documentation
        has_readme = any(f.get("path", "").lower().endswith("readme.md") 
                        for f in repo_analysis.get("files", []))
        has_security_policy = any("security" in f.get("path", "").lower() 
                                 for f in repo_analysis.get("files", []))
        
        if has_readme:
            compliance_score += 20
        else:
            compliance_issues.append("Missing README documentation")
        
        if has_security_policy:
            compliance_score += 30
        else:
            compliance_issues.append("Missing security policy")
        
        # Check for license
        has_license = any("license" in f.get("path", "").lower() 
                         for f in repo_analysis.get("files", []))
        if has_license:
            compliance_score += 20
        else:
            compliance_issues.append("Missing license file")
        
        # Check for dependency management
        has_dependencies = any(
            f.get("path", "").endswith(("requirements.txt", "package.json", "pom.xml", "Cargo.toml"))
            for f in repo_analysis.get("files", [])
        )
        if has_dependencies:
            compliance_score += 30
        else:
            compliance_issues.append("Missing dependency management")
        
        return {
            "score": min(compliance_score, 100),
            "issues": compliance_issues,
            "has_documentation": has_readme,
            "has_security_policy": has_security_policy,
            "has_license": has_license,
            "has_dependencies": has_dependencies
        }
    
    def generate_recommendations(
        self, 
        findings: List[Dict[str, Any]], 
        analysis_summary: Dict[str, Any]
    ) -> List[str]:
        """Generate security recommendations."""
        recommendations = []
        
        # Critical findings recommendations
        critical_count = sum(1 for f in findings if f["severity"] == "critical")
        if critical_count > 0:
            recommendations.append(f"Address {critical_count} critical security issues immediately")
        
        # Quantum safety recommendations
        if not analysis_summary.get("quantum_safe", False):
            recommendations.append("Consider implementing quantum-resistant cryptographic algorithms")
        
        # Documentation recommendations
        if analysis_summary.get("compliance_score", 0) < 50:
            recommendations.append("Improve project documentation and security policies")
        
        # General recommendations
        recommendations.extend([
            "Regularly update cryptographic libraries to latest versions",
            "Implement proper key management practices",
            "Use established cryptographic libraries instead of custom implementations",
            "Conduct regular security audits and penetration testing"
        ])
        
        return recommendations
    
    def calculate_overall_score(
        self, 
        findings: List[Dict[str, Any]], 
        analysis_summary: Dict[str, Any]
    ) -> float:
        """Calculate overall security score."""
        base_score = 100.0
        
        # Deduct points for findings
        severity_weights = {
            "critical": 15,
            "high": 10,
            "medium": 5,
            "low": 2
        }
        
        for finding in findings:
            if finding["severity"] in severity_weights:
                base_score -= severity_weights[finding["severity"]]
        
        # Add points for good practices
        if analysis_summary.get("quantum_safe", False):
            base_score += 5
        
        if analysis_summary.get("compliance_score", 0) > 80:
            base_score += 5
        
        return max(0.0, min(100.0, base_score))
    
    def determine_security_level(self, score: float, findings: List[Dict[str, Any]]) -> str:
        """Determine security level based on score and findings."""
        critical_count = sum(1 for f in findings if f["severity"] == "critical")
        
        if critical_count > 0:
            return "critical"
        elif score >= 90:
            return "excellent"
        elif score >= 80:
            return "good"
        elif score >= 70:
            return "fair"
        elif score >= 60:
            return "poor"
        else:
            return "critical"
    
    def load_nist_standards(self) -> Dict[str, Any]:
        """Load NIST cryptographic standards."""
        return {
            "approved_algorithms": [
                "AES", "SHA-256", "SHA-384", "SHA-512", "SHA3-256", 
                "SHA3-384", "SHA3-512", "HMAC", "PBKDF2"
            ],
            "deprecated_algorithms": ["DES", "3DES", "MD5", "SHA1"],
            "key_lengths": {
                "AES": [128, 192, 256],
                "RSA": [2048, 3072, 4096],
                "EC": [256, 384, 521]
            }
        }
    
    def load_iso_standards(self) -> Dict[str, Any]:
        """Load ISO cryptographic standards."""
        return {
            "standards": ["ISO/IEC 27001", "ISO/IEC 27002", "ISO/IEC 15408"],
            "approved_algorithms": ["AES", "SHA-2", "SHA-3", "HMAC"]
        }
    
    def load_owasp_guidelines(self) -> Dict[str, Any]:
        """Load OWASP cryptographic guidelines."""
        return {
            "guidelines": [
                "Use strong, up-to-date cryptographic algorithms",
                "Use appropriate key sizes",
                "Store keys securely",
                "Use secure random number generation",
                "Implement proper key rotation"
            ],
            "common_vulnerabilities": [
                "Weak encryption algorithms",
                "Hardcoded encryption keys",
                "Insecure random number generation",
                "Improper key management"
            ]
        }