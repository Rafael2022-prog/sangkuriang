"""
Advanced Cryptography Audit Engine - SANGKURIANG
Enhanced security audit engine with advanced vulnerability detection
"""

import hashlib
import secrets
import re
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec, dsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
import ast
import os


class AdvancedCryptoAuditEngine:
    """Enhanced cryptography audit engine with advanced security features"""
    
    def __init__(self):
        self.vulnerabilities = []
        self.recommendations = []
        self.security_score = 100
        self.compliance_score = 100
        self.performance_score = 100
        
        # Vulnerability patterns (untuk kompatibilitas dengan test)
        self.vulnerability_patterns = {
            'timing_attacks': [
                r'secret.*?==.*?constant',
                r'if.*?secret.*?==',
                r'memcmp.*?secret',
                r'strcmp.*?secret'
            ],
            'padding_oracle': [
                r'PKCS1v15.*?decrypt',
                r'pkcs.*?(padding|unpadding)',
                r'padding.*?(oracle|vulnerable)'
            ],
            'side_channel': [
                r'password.*?(length|size)',
                r'secret.*?(length|size)',
                r'key.*?(length|size).*?if'
            ],
            'weak_random': [
                r'random\.random\(\)',
                r'Math\.random\(\)',
                r'rand\(\)',
                r'srand\(time\(NULL\)\)'
            ],
            'crypto_bombs': [
                r'zip.*?password.*?(1024|2048|4096)',
                r'gzip.*?password.*?(1024|2048|4096)',
                r'compress.*?encrypt.*?(1024|2048|4096)'
            ]
        }
        
        # Advanced vulnerability patterns
        self.advanced_vulnerability_patterns = {
            'timing_attacks': [
                r'secret.*?==.*?constant',
                r'if.*?secret.*?==',
                r'memcmp.*?secret',
                r'strcmp.*?secret'
            ],
            'padding_oracle': [
                r'PKCS1v15.*?decrypt',
                r'pkcs.*?(padding|unpadding)',
                r'padding.*?(oracle|vulnerable)'
            ],
            'side_channel': [
                r'password.*?(length|size)',
                r'secret.*?(length|size)',
                r'key.*?(length|size).*?if'
            ],
            'weak_random': [
                r'random\.random\(\)',
                r'Math\.random\(\)',
                r'rand\(\)',
                r'srand\(time\(NULL\)\)'
            ],
            'crypto_bombs': [
                r'zip.*?password.*?(1024|2048|4096)',
                r'gzip.*?password.*?(1024|2048|4096)',
                r'compress.*?encrypt.*?(1024|2048|4096)'
            ]
        }
        
        # Advanced cryptographic standards
        self.nist_standards = {
            'symmetric_ciphers': ['AES-128', 'AES-192', 'AES-256', 'AES-128-GCM', 'AES-192-GCM', 'AES-256-GCM', '3DES'],
            'asymmetric_ciphers': ['RSA-2048', 'RSA-3072', 'RSA-4096'],
            'hash_functions': ['SHA-256', 'SHA-384', 'SHA-512', 'SHA3-256', 'SHA3-512', 'PBKDF2-HMAC-SHA256', 'PBKDF2-HMAC-SHA384', 'PBKDF2-HMAC-SHA512'],
            'key_exchange': ['ECDH-P256', 'ECDH-P384', 'ECDH-P521', 'DH-2048'],
            'signatures': ['ECDSA-P256', 'ECDSA-P384', 'RSA-PSS', 'Ed25519']
        }
        
        # ISO standards untuk test compatibility
        self.iso_standards = {
            'iso_27001': ['information_security', 'risk_management'],
            'iso_27017': ['cloud_security', 'data_protection'],
            'iso_27018': ['personal_data', 'privacy_protection'],
            'iso_27799': ['health_informatics', 'data_security']
        }
        
        self.iso_compliance = {
            'iso_27001': ['information_security', 'risk_management'],
            'iso_27017': ['cloud_security', 'data_protection'],
            'iso_27018': ['personal_data', 'privacy_protection'],
            'iso_27799': ['health_informatics', 'data_security']
        }

    def advanced_cryptographic_audit(self, code_content: str, file_path: str = "") -> Dict:
        """Perform advanced cryptographic audit with enhanced vulnerability detection"""
        
        self.vulnerabilities = []
        self.recommendations = []
        self.security_score = 100
        self.compliance_score = 100
        self.performance_score = 100
        
        audit_results = {
            'file_path': file_path,
            'timestamp': datetime.now().isoformat(),
            'audit_level': 'ADVANCED',
            'vulnerabilities': [],
            'vulnerability_count': 0,
            'recommendations': [],
            'security_score': 100,
            'compliance_score': 100,
            'performance_score': 100,
            'overall_score': 100,
            'certification_status': 'PENDING',
            'nist_compliance': {},
            'iso_compliance': {},
            'quantum_resistance': {},
            'side_channel_vulnerabilities': [],
            'timing_attack_risks': [],
            'advanced_threats': []
        }
        
        try:
            # Advanced vulnerability detection
            self._detect_timing_attacks(code_content)
            self._detect_padding_oracle_vulnerabilities(code_content)
            self._detect_side_channel_attacks(code_content)
            self._detect_weak_random_number_generators(code_content)
            self._detect_crypto_bombs(code_content)
            self._detect_quantum_vulnerabilities(code_content)
            self._detect_advanced_persistence_threats(code_content)
            
            # Compliance checking
            self._check_nist_compliance(code_content)
            self._check_iso_compliance(code_content)
            self._check_quantum_resistance(code_content)
            
            # Performance and security scoring
            self._calculate_advanced_scores(code_content)
            
            # Certification process
            self._evaluate_certification_status()
            
            # Hitung vulnerability count
            vulnerability_count = len(self.vulnerabilities)
            
            audit_results.update({
                'vulnerabilities': self.vulnerabilities,
                'vulnerability_count': vulnerability_count,
                'recommendations': self.recommendations,
                'security_score': self.security_score,
                'compliance_score': self.compliance_score,
                'performance_score': self.performance_score,
                'overall_score': (self.security_score + self.compliance_score + self.performance_score) / 3,
                'certification_status': self._get_certification_status(),
                'nist_compliance': self.nist_standards,
                'iso_compliance': self.iso_compliance,
                'side_channel_vulnerabilities': self._get_side_channel_vulnerabilities(),
                'timing_attack_risks': self._get_timing_attack_risks(),
                'advanced_threats': self._get_advanced_threats()
            })
            
        except Exception as e:
            audit_results['error'] = str(e)
            self.vulnerabilities.append({
                'type': 'AUDIT_ERROR',
                'severity': 'HIGH',
                'description': f'Error during advanced audit: {str(e)}',
                'line': 0,
                'recommendation': 'Review audit configuration and code syntax'
            })
        
        return audit_results

    async def comprehensive_audit(self, code_content: str, file_path: str = "") -> Dict:
        """Async wrapper untuk comprehensive audit"""
        audit_result = self.advanced_cryptographic_audit(code_content, file_path)
        
        # Format untuk test compatibility
        return {
            "success": True,
            "audit_results": audit_result,
            "vulnerability_count": len(audit_result.get("vulnerabilities", [])),
            "security_score": audit_result.get("security_score", 0),
            "compliance_score": audit_result.get("compliance_score", 0),
            "overall_score": audit_result.get("overall_score", 0)
        }

    def check_quantum_resistance(self, crypto_config: Dict) -> Dict:
        """Check quantum resistance of cryptographic configuration"""
        result = {
            "quantum_safe": True,
            "quantum_risk_level": "LOW",
            "vulnerable_algorithms": [],
            "recommendations": []
        }
        
        # Check for quantum-vulnerable algorithms
        vulnerable_algorithms = ['RSA', 'DSA', 'ECDSA', 'DH']
        quantum_safe_algorithms = ['AES-256', 'SHA3-512', 'ChaCha20-Poly1305']
        
        algorithm = crypto_config.get("algorithm", "")
        key_size = crypto_config.get("key_size", 0)
        
        if any(vuln_algo in algorithm for vuln_algo in vulnerable_algorithms):
            result["quantum_safe"] = False
            result["quantum_risk_level"] = "HIGH"
            result["vulnerable_algorithms"].append(algorithm)
            result["recommendations"].append(f"Consider migrating from {algorithm} to quantum-resistant algorithms")
        
        # Check key size for quantum resistance
        if algorithm == "RSA" and key_size < 2048:
            result["quantum_safe"] = False
            result["quantum_risk_level"] = "CRITICAL"
            result["recommendations"].append("RSA key size should be at least 2048 bits for quantum resistance")
        
        return result
    
    def check_nist_compliance(self, config: Dict) -> Dict[str, Any]:
        """Check NIST compliance - returns dictionary for test compatibility"""
        result = {
            "nist_compliant": True,
            "compliance_issues": [],
            "recommendations": []
        }
        
        # Check encryption algorithm
        encryption_algo = config.get("encryption_algorithm", "")
        if encryption_algo not in self.nist_standards.get("symmetric_ciphers", []):
            result["nist_compliant"] = False
            result["compliance_issues"].append(f"Encryption algorithm {encryption_algo} not NIST approved")
            result["recommendations"].append("Use NIST-approved symmetric ciphers like AES-128, AES-192, or AES-256")
        
        # Check key derivation
        key_derivation = config.get("key_derivation", "")
        if key_derivation and key_derivation not in self.nist_standards.get("hash_functions", []):
            result["nist_compliant"] = False
            result["compliance_issues"].append(f"Key derivation {key_derivation} not NIST approved")
            result["recommendations"].append("Use NIST-approved hash functions like SHA-256, SHA-384, or SHA-512")
        
        # Check random number generator
        rng = config.get("random_number_generator", "")
        if rng and "NIST_SP_800_90A" not in rng:
            result["nist_compliant"] = False
            result["compliance_issues"].append("Random number generator not compliant with NIST SP 800-90A")
            result["recommendations"].append("Use NIST SP 800-90A compliant random number generators")
        
        return result

    def _detect_timing_attacks(self, code: str) -> None:
        """Detect potential timing attack vulnerabilities"""
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern in self.advanced_vulnerability_patterns['timing_attacks']:
                if re.search(pattern, line, re.IGNORECASE):
                    self.vulnerabilities.append({
                        'type': 'TIMING_ATTACK',
                        'severity': 'HIGH',
                        'description': 'Potential timing attack vulnerability detected',
                        'line': i,
                        'code': line.strip(),
                        'recommendation': 'Use constant-time comparison functions (e.g., hmac.compare_digest)'
                    })
                    self.security_score -= 15

    def _detect_padding_oracle_vulnerabilities(self, code: str) -> None:
        """Detect padding oracle vulnerabilities"""
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern in self.advanced_vulnerability_patterns['padding_oracle']:
                if re.search(pattern, line, re.IGNORECASE):
                    self.vulnerabilities.append({
                        'type': 'PADDING_ORACLE',
                        'severity': 'CRITICAL',
                        'description': 'Potential padding oracle vulnerability',
                        'line': i,
                        'code': line.strip(),
                        'recommendation': 'Use authenticated encryption (AES-GCM) or implement proper padding verification'
                    })
                    self.security_score -= 25

    def _detect_side_channel_attacks(self, code: str) -> None:
        """Detect side-channel attack vulnerabilities"""
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern in self.advanced_vulnerability_patterns['side_channel']:
                if re.search(pattern, line, re.IGNORECASE):
                    self.vulnerabilities.append({
                        'type': 'SIDE_CHANNEL',
                        'severity': 'MEDIUM',
                        'description': 'Potential side-channel attack vulnerability',
                        'line': i,
                        'code': line.strip(),
                        'recommendation': 'Ensure constant-time operations and avoid branching on secret data'
                    })
                    self.security_score -= 10

    def _detect_weak_random_number_generators(self, code: str) -> None:
        """Detect weak random number generators"""
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern in self.advanced_vulnerability_patterns['weak_random']:
                if re.search(pattern, line):
                    self.vulnerabilities.append({
                        'type': 'WEAK_RANDOM',
                        'severity': 'HIGH',
                        'description': 'Weak random number generator detected',
                        'line': i,
                        'code': line.strip(),
                        'recommendation': 'Use cryptographically secure random generators (secrets, os.urandom)'
                    })
                    self.security_score -= 20

    def _detect_crypto_bombs(self, code: str) -> None:
        """Detect potential crypto bombs (decompression bombs)"""
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern in self.advanced_vulnerability_patterns['crypto_bombs']:
                if re.search(pattern, line, re.IGNORECASE):
                    self.vulnerabilities.append({
                        'type': 'CRYPTO_BOMB',
                        'severity': 'HIGH',
                        'description': 'Potential crypto bomb vulnerability',
                        'line': i,
                        'code': line.strip(),
                        'recommendation': 'Implement size limits and resource constraints for compressed data'
                    })
                    self.security_score -= 15

    def _detect_quantum_vulnerabilities(self, code: str) -> None:
        """Detect vulnerabilities to quantum attacks"""
        quantum_vulnerable = [
            'RSA-1024', 'RSA-512', 'DSA-1024', 'ECDSA-P192',
            'SHA-1', 'MD5', 'RC4', 'DES'
        ]
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            for vuln in quantum_vulnerable:
                if vuln in line.upper():
                    self.vulnerabilities.append({
                        'type': 'QUANTUM_VULNERABLE',
                        'severity': 'MEDIUM',
                        'description': f'Quantum-vulnerable algorithm detected: {vuln}',
                        'line': i,
                        'code': line.strip(),
                        'recommendation': 'Consider post-quantum cryptography (Lattice-based, Hash-based signatures)'
                    })
                    self.security_score -= 8

    def _detect_advanced_persistence_threats(self, code: str) -> None:
        """Detect advanced persistent threat (APT) indicators"""
        apt_indicators = [
            'hardcoded.*api.*key',
            'hardcoded.*password',
            'backdoor.*password',
            'debug.*password',
            'test.*password',
            'admin.*123',
            'password.*admin'
        ]
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            for indicator in apt_indicators:
                if re.search(indicator, line, re.IGNORECASE):
                    self.vulnerabilities.append({
                        'type': 'APT_INDICATOR',
                        'severity': 'CRITICAL',
                        'description': f'Potential APT indicator: {indicator}',
                        'line': i,
                        'code': line.strip(),
                        'recommendation': 'Remove hardcoded credentials and implement secure key management'
                    })
                    self.security_score -= 30

    def _check_nist_compliance(self, code: str) -> None:
        """Check compliance with NIST standards"""
        compliance_issues = []
        
        # Check for deprecated algorithms
        deprecated_algorithms = ['DES', '3DES', 'RC4', 'MD5', 'SHA1']
        for algo in deprecated_algorithms:
            if algo in code.upper():
                compliance_issues.append(f"Deprecated algorithm: {algo}")
                self.compliance_score -= 10
        
        # Check key sizes
        weak_key_patterns = [
            r'RSA.*?(\d{3,4})',
            r'AES.*?(\d{2,3})',
            r'EC.*?(\d{2,3})'
        ]
        
        for pattern in weak_key_patterns:
            matches = re.findall(pattern, code, re.IGNORECASE)
            for match in matches:
                key_size = int(match)
                if 'RSA' in pattern and key_size < 2048:
                    compliance_issues.append(f"Weak RSA key size: {key_size}")
                    self.compliance_score -= 15
                elif 'AES' in pattern and key_size < 128:
                    compliance_issues.append(f"Weak AES key size: {key_size}")
                    self.compliance_score -= 10
        
        if compliance_issues:
            self.recommendations.append({
                'type': 'NIST_COMPLIANCE',
                'issues': compliance_issues,
                'recommendation': 'Update to NIST-approved algorithms and key sizes'
            })

    def _check_iso_compliance(self, code: str) -> None:
        """Check ISO compliance"""
        iso_issues = []
        
        # Check for proper data handling
        if not re.search(r'encrypt.*?(personal|sensitive|private)', code, re.IGNORECASE):
            iso_issues.append("Personal data encryption not explicitly mentioned")
            self.compliance_score -= 5
        
        if not re.search(r'access.*?(control|permission)', code, re.IGNORECASE):
            iso_issues.append("Access control not explicitly implemented")
            self.compliance_score -= 5
        
        if iso_issues:
            self.recommendations.append({
                'type': 'ISO_COMPLIANCE',
                'issues': iso_issues,
                'recommendation': 'Implement ISO 27001/27799 compliance measures'
            })

    def _check_quantum_resistance(self, code: str) -> None:
        """Check quantum resistance capabilities"""
        quantum_resistant_algos = ['Kyber', 'Dilithium', 'Falcon', 'SPHINCS+']
        has_quantum_resistant = any(algo in code for algo in quantum_resistant_algos)
        
        if not has_quantum_resistant:
            self.recommendations.append({
                'type': 'QUANTUM_RESISTANCE',
                'recommendation': 'Consider implementing post-quantum cryptography for future-proofing'
            })

    def _calculate_advanced_scores(self, code: str) -> None:
        """Calculate advanced security scores"""
        # Base scoring with advanced metrics
        if len(self.vulnerabilities) == 0:
            self.security_score = 100
        else:
            # Calculate weighted score based on vulnerability severity
            critical_count = sum(1 for v in self.vulnerabilities if v['severity'] == 'CRITICAL')
            high_count = sum(1 for v in self.vulnerabilities if v['severity'] == 'HIGH')
            medium_count = sum(1 for v in self.vulnerabilities if v['severity'] == 'MEDIUM')
            
            penalty = (critical_count * 25) + (high_count * 15) + (medium_count * 8)
            self.security_score = max(0, 100 - penalty)
        
        # Performance scoring based on code complexity
        lines_of_code = len(code.split('\n'))
        if lines_of_code > 1000:
            self.performance_score -= 10
        
        # Ensure scores are within valid range
        self.security_score = max(0, min(100, self.security_score))
        self.compliance_score = max(0, min(100, self.compliance_score))
        self.performance_score = max(0, min(100, self.performance_score))

    def _evaluate_certification_status(self) -> None:
        """Evaluate certification eligibility"""
        overall_score = (self.security_score + self.compliance_score + self.performance_score) / 3
        
        if overall_score >= 90:
            self.certification_status = 'CERTIFIED_GOLD'
        elif overall_score >= 80:
            self.certification_status = 'CERTIFIED_SILVER'
        elif overall_score >= 70:
            self.certification_status = 'CERTIFIED_BRONZE'
        elif overall_score >= 60:
            self.certification_status = 'CONDITIONAL'
        else:
            self.certification_status = 'NOT_CERTIFIED'

    def _get_certification_status(self) -> str:
        """Get current certification status"""
        return self.certification_status

    def _get_side_channel_vulnerabilities(self) -> List[Dict]:
        """Get side-channel vulnerabilities"""
        return [v for v in self.vulnerabilities if v['type'] == 'SIDE_CHANNEL']

    def _get_timing_attack_risks(self) -> List[Dict]:
        """Get timing attack risks"""
        return [v for v in self.vulnerabilities if v['type'] == 'TIMING_ATTACK']

    def _get_advanced_threats(self) -> List[Dict]:
        """Get advanced threat indicators"""
        return [v for v in self.vulnerabilities if v['type'] in ['APT_INDICATOR', 'QUANTUM_VULNERABLE']]

    def generate_security_report(self, audit_results: Dict) -> str:
        """Generate comprehensive security report"""
        report = f"""
# SANGKURIANG Advanced Security Audit Report

## Executive Summary
- **Overall Security Score**: {audit_results['overall_score']:.1f}/100
- **Certification Status**: {audit_results['certification_status']}
- **Total Vulnerabilities**: {len(audit_results['vulnerabilities'])}
- **Audit Level**: {audit_results['audit_level']}

## Detailed Findings
"""
        
        # Group vulnerabilities by type
        vuln_by_type = {}
        for vuln in audit_results['vulnerabilities']:
            vuln_type = vuln['type']
            if vuln_type not in vuln_by_type:
                vuln_by_type[vuln_type] = []
            vuln_by_type[vuln_type].append(vuln)
        
        for vuln_type, vulns in vuln_by_type.items():
            report += f"\n### {vuln_type.replace('_', ' ').title()}\n"
            report += f"**Count**: {len(vulns)}\n\n"
            for vuln in vulns:
                report += f"- **Line {vuln['line']}**: {vuln['description']}\n"
                report += f"  - Severity: {vuln['severity']}\n"
                report += f"  - Recommendation: {vuln['recommendation']}\n\n"
        
        report += f"""
## Compliance Status
- **NIST Compliance Score**: {audit_results['compliance_score']}/100
- **ISO Compliance Score**: {audit_results['compliance_score']}/100
- **Quantum Resistance**: {'Available' if audit_results.get('quantum_resistance', False) else 'Not Implemented'}

## Recommendations
{chr(10).join(f"- {rec['recommendation']}" for rec in audit_results['recommendations'])}

## Next Steps
1. Address all CRITICAL and HIGH severity vulnerabilities
2. Implement recommended security controls
3. Re-audit after remediation
4. Consider post-quantum cryptography migration
"""
        
        return report
    
    def get_audit_summary(self, code_content: str, file_path: str = "") -> Dict:
        """Get audit summary for test compatibility"""
        audit_results = self.advanced_cryptographic_audit(code_content, file_path)
        return {
            "success": True,
            "audit_results": audit_results,
            "vulnerability_count": len(audit_results.get("vulnerabilities", [])),
            "security_score": audit_results.get("security_score", 0),
            "compliance_score": audit_results.get("compliance_score", 0),
            "overall_score": audit_results.get("overall_score", 0)
        }