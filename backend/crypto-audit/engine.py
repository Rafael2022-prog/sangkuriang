"""
Crypto Audit Engine for SANGKURIANG
Analyzes cryptographic implementations for security vulnerabilities
"""

import ast
import re
import subprocess
import tempfile
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
from datetime import datetime

import numpy as np
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec, dsa
from cryptography.exceptions import InvalidSignature

@dataclass
class AuditResult:
    """Result of cryptographic audit"""
    project_id: str
    overall_score: int  # 0-100
    security_score: int  # 0-100
    performance_score: int  # 0-100
    compliance_score: int  # 0-100
    vulnerabilities: List[Dict[str, Any]]
    recommendations: List[str]
    badge_url: Optional[str] = None
    audit_timestamp: datetime = None
    audit_request_id: Optional[str] = None
    
    def __post_init__(self):
        if self.audit_timestamp is None:
            self.audit_timestamp = datetime.now()
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit result to dictionary"""
        return {
            "project_id": self.project_id,
            "overall_score": self.overall_score,
            "security_score": self.security_score,
            "performance_score": self.performance_score,
            "compliance_score": self.compliance_score,
            "vulnerabilities": self.vulnerabilities,
            "recommendations": self.recommendations,
            "badge_url": self.badge_url,
            "audit_timestamp": self.audit_timestamp.isoformat() if self.audit_timestamp else None,
            "audit_request_id": self.audit_request_id
        }

class CryptoAuditEngine:
    """Main cryptographic audit engine"""
    
    def __init__(self):
        self.vulnerability_patterns = self._load_vulnerability_patterns()
        self.crypto_algorithms = self._load_crypto_algorithms()
        self.compliance_standards = self._load_compliance_standards()
        
    def _load_vulnerability_patterns(self) -> Dict[str, List[str]]:
        """Load known cryptographic vulnerability patterns"""
        return {
            "weak_algorithms": [
                r"md5\(",
                r"sha1\(",
                r"des\(",
                r"3des\(",
                r"rc4\(",
            ],
            "weak_random": [
                r"random\.random\(",
                r"random\.randint\(",
                r"Math\.random\(",
            ],
            "hardcoded_secrets": [
                r"password\s*=\s*[\"'][^\"']+[\"']",
                r"api_key\s*=\s*[\"'][^\"']+[\"']",
                r"secret\s*=\s*[\"'][^\"']+[\"']",
            ],
            "ecb_mode": [
                r"AES\.MODE_ECB",
                r"DES\.MODE_ECB",
            ],
            "static_iv": [
                r"iv\s*=\s*[\"'][^\"']+[\"']",
                r"IV\s*=\s*[\"'][^\"']+[\"']",
            ],
            "weak_key_sizes": [
                r"RSA\.generate\(1024\)",
                r"key_size\s*=\s*1024",
            ]
        }
    
    def _load_crypto_algorithms(self) -> Dict[str, Any]:
        """Load cryptographic algorithm specifications"""
        return {
            "symmetric": {
                "recommended": ["AES-256-GCM", "ChaCha20-Poly1305", "AES-256-CBC"],
                "deprecated": ["DES", "3DES", "RC4", "AES-ECB"],
                "minimum_key_size": 128
            },
            "asymmetric": {
                "recommended": ["RSA-2048+", "ECDSA-P256", "Ed25519"],
                "deprecated": ["RSA-1024", "DSA-1024"],
                "minimum_key_size": 2048
            },
            "hashing": {
                "recommended": ["SHA-256", "SHA-384", "SHA-512", "BLAKE2"],
                "deprecated": ["MD5", "SHA1", "RIPEMD"],
                "minimum_bits": 256
            },
            "random": {
                "recommended": ["secrets", "os.urandom", "crypto.randomBytes"],
                "deprecated": ["random.random", "Math.random"]
            }
        }
    
    def _load_compliance_standards(self) -> Dict[str, Any]:
        """Load compliance standards requirements"""
        return {
            "NIST": {
                "key_management": "SP 800-57",
                "random_number": "SP 800-90A",
                "digital_signatures": "FIPS 186-4",
                "encryption": "FIPS 140-2"
            },
            "ISO": {
                "key_management": "ISO/IEC 11770",
                "random_number": "ISO/IEC 18031",
                "encryption": "ISO/IEC 19790"
            }
        }
    
    async def audit_project(self, project_path: str, project_id: str) -> AuditResult:
        """Perform comprehensive cryptographic audit"""
        try:
            # Scan for cryptographic code
            crypto_files = self._find_crypto_files(project_path)
            
            if not crypto_files:
                return AuditResult(
                    project_id=project_id,
                    overall_score=0,
                    security_score=0,
                    performance_score=0,
                    compliance_score=0,
                    vulnerabilities=[{
                        "severity": "high",
                        "category": "missing_crypto",
                        "description": "No cryptographic implementation found",
                        "recommendation": "Project should include cryptographic components"
                    }],
                    recommendations=["Add cryptographic implementation to project"]
                )
            
            # Analyze each file
            all_vulnerabilities = []
            all_recommendations = []
            
            for file_path in crypto_files:
                vulnerabilities, recommendations = await self._analyze_file(file_path)
                all_vulnerabilities.extend(vulnerabilities)
                all_recommendations.extend(recommendations)
            
            # Calculate scores
            security_score = self._calculate_security_score(all_vulnerabilities)
            performance_score = self._calculate_performance_score(crypto_files)
            compliance_score = self._calculate_compliance_score(crypto_files)
            overall_score = int((security_score + performance_score + compliance_score) / 3)
            
            # Generate badge URL based on score
            badge_url = self._generate_badge_url(overall_score)
            
            return AuditResult(
                project_id=project_id,
                overall_score=overall_score,
                security_score=security_score,
                performance_score=performance_score,
                compliance_score=compliance_score,
                vulnerabilities=all_vulnerabilities,
                recommendations=list(set(all_recommendations)),  # Remove duplicates
                badge_url=badge_url
            )
            
        except Exception as e:
            logger.error(f"Audit failed for project {project_id}: {str(e)}")
            raise Exception(f"Crypto audit failed: {str(e)}")
    
    def _find_crypto_files(self, project_path: str) -> List[str]:
        """Find files containing cryptographic implementations"""
        crypto_files = []
        crypto_keywords = [
            "crypto", "encrypt", "decrypt", "cipher", "hash", "sign", "verify",
            "rsa", "aes", "sha", "md5", "key", "password", "token", "jwt"
        ]
        
        for root, dirs, files in os.walk(project_path):
            # Skip common non-crypto directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules']]
            
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.go', '.rs', '.cpp', '.c')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read().lower()
                            if any(keyword in content for keyword in crypto_keywords):
                                crypto_files.append(file_path)
                    except Exception:
                        continue
        
        return crypto_files
    
    async def _analyze_file(self, file_path: str) -> tuple[List[Dict], List[str]]:
        """Analyze a single file for cryptographic vulnerabilities"""
        vulnerabilities = []
        recommendations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check for weak algorithms
            for pattern in self.vulnerability_patterns["weak_algorithms"]:
                if re.search(pattern, content, re.IGNORECASE):
                    vulnerabilities.append({
                        "severity": "high",
                        "category": "weak_algorithm",
                        "file": file_path,
                        "description": f"Weak cryptographic algorithm detected: {pattern}",
                        "recommendation": "Use modern cryptographic algorithms like AES-256, SHA-256, or ChaCha20-Poly1305"
                    })
            
            # Check for weak random number generation
            for pattern in self.vulnerability_patterns["weak_random"]:
                if re.search(pattern, content, re.IGNORECASE):
                    vulnerabilities.append({
                        "severity": "high",
                        "category": "weak_random",
                        "file": file_path,
                        "description": f"Weak random number generation: {pattern}",
                        "recommendation": "Use cryptographically secure random number generators like secrets or os.urandom"
                    })
            
            # Check for hardcoded secrets
            for pattern in self.vulnerability_patterns["hardcoded_secrets"]:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    vulnerabilities.append({
                        "severity": "critical",
                        "category": "hardcoded_secret",
                        "file": file_path,
                        "description": f"Hardcoded secret detected: {match[:50]}...",
                        "recommendation": "Never hardcode secrets. Use environment variables or secure key management systems"
                    })
            
            # Check for ECB mode
            for pattern in self.vulnerability_patterns["ecb_mode"]:
                if re.search(pattern, content, re.IGNORECASE):
                    vulnerabilities.append({
                        "severity": "high",
                        "category": "weak_mode",
                        "file": file_path,
                        "description": "ECB mode detected - not semantically secure",
                        "recommendation": "Use authenticated encryption modes like GCM or ChaCha20-Poly1305"
                    })
            
            # Check for static IVs
            for pattern in self.vulnerability_patterns["static_iv"]:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    vulnerabilities.append({
                        "severity": "high",
                        "category": "static_iv",
                        "file": file_path,
                        "description": f"Static IV detected: {match}",
                        "recommendation": "Use random IV for each encryption operation"
                    })
            
            # Check for weak key sizes
            for pattern in self.vulnerability_patterns["weak_key_sizes"]:
                if re.search(pattern, content, re.IGNORECASE):
                    vulnerabilities.append({
                        "severity": "high",
                        "category": "weak_key_size",
                        "file": file_path,
                        "description": "Weak key size detected (1024 bits or less)",
                        "recommendation": "Use minimum 2048-bit RSA keys or 256-bit ECC keys"
                    })
            
            # Generate recommendations based on findings
            if not vulnerabilities:
                recommendations.append("Excellent! No cryptographic vulnerabilities detected.")
            
            # Add general recommendations
            recommendations.extend([
                "Use authenticated encryption (AES-GCM or ChaCha20-Poly1305)",
                "Implement proper key management and rotation",
                "Use cryptographically secure random number generation",
                "Follow NIST and ISO cryptographic standards",
                "Regularly update cryptographic libraries"
            ])
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {str(e)}")
            vulnerabilities.append({
                "severity": "medium",
                "category": "analysis_error",
                "file": file_path,
                "description": f"Error analyzing file: {str(e)}",
                "recommendation": "Manual review required"
            })
        
        return vulnerabilities, recommendations
    
    def _calculate_security_score(self, vulnerabilities: List[Dict]) -> int:
        """Calculate security score based on vulnerabilities"""
        if not vulnerabilities:
            return 100
        
        score = 100
        severity_weights = {
            "critical": 25,
            "high": 15,
            "medium": 10,
            "low": 5
        }
        
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "medium")
            score -= severity_weights.get(severity, 10)
        
        return max(0, score)
    
    def _calculate_performance_score(self, crypto_files: List[str]) -> int:
        """Calculate performance score based on implementation quality"""
        # This is a simplified calculation
        # In practice, this would analyze actual code complexity and efficiency
        score = 80  # Base score
        
        # Bonus for having crypto implementations
        if crypto_files:
            score += 10
        
        # Bonus for multiple files (modular design)
        if len(crypto_files) > 1:
            score += 10
        
        return min(100, score)
    
    def _calculate_compliance_score(self, crypto_files: List[str]) -> int:
        """Calculate compliance score based on standards adherence"""
        score = 70  # Base score
        
        # Check for compliance-related keywords
        compliance_keywords = ["nist", "iso", "fips", "standard", "compliance"]
        
        for file_path in crypto_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                    if any(keyword in content for keyword in compliance_keywords):
                        score += 10
                        break
            except Exception:
                continue
        
        return min(100, score)
    
    def _generate_badge_url(self, score: int) -> str:
        """Generate badge URL based on score"""
        color = "red" if score < 50 else "yellow" if score < 80 else "green"
        return f"https://img.shields.io/badge/security-{score}%25-{color}"

# Global audit engine instance
crypto_audit_engine = CryptoAuditEngine()

# For async usage
async def audit_crypto_project(project_path: str, project_id: str) -> AuditResult:
    """Async wrapper for crypto audit"""
    return await crypto_audit_engine.audit_project(project_path, project_id)