"""
Smart Contract Audit Engine for SANGKURIANG
Advanced security audit for smart contracts with Indonesian compliance
"""

import re
import json
import ast
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
import hashlib
import subprocess
import tempfile
import os

from engine import CryptoAuditEngine, AuditResult
from advanced_engine import AdvancedCryptoAuditEngine


@dataclass
class SmartContractIssue:
    """Represents a security or compliance issue in smart contract"""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: str  # SECURITY, COMPLIANCE, PERFORMANCE, GAS, LOGIC
    title: str
    description: str
    line_number: int
    code_snippet: str
    recommendation: str
    cwe_id: Optional[str] = None
    owasp_id: Optional[str] = None
    compliance_standard: Optional[str] = None


@dataclass
class SmartContractAuditResult:
    """Result of smart contract audit"""
    contract_address: str
    contract_name: str
    blockchain: str  # ethereum, polygon, bnb, solana, etc
    audit_timestamp: datetime
    overall_score: int  # 0-100
    security_score: int  # 0-100
    gas_optimization_score: int  # 0-100
    compliance_score: int  # 0-100
    issues: List[SmartContractIssue]
    recommendations: List[str]
    badge_url: Optional[str] = None
    audit_hash: Optional[str] = None
    is_verified: bool = False
    
    def __post_init__(self):
        if self.audit_timestamp is None:
            self.audit_timestamp = datetime.now()
        
        # Generate audit hash for integrity
        audit_data = f"{self.contract_address}{self.contract_name}{self.audit_timestamp.isoformat()}"
        self.audit_hash = hashlib.sha256(audit_data.encode()).hexdigest()


class SmartContractAuditEngine:
    """Advanced smart contract security audit engine"""
    
    def __init__(self):
        self.crypto_engine = CryptoAuditEngine()
        self.advanced_engine = AdvancedCryptoAuditEngine()
        
        # Smart contract specific vulnerability patterns
        self.vulnerability_patterns = self._load_smart_contract_patterns()
        
        # Indonesian compliance requirements
        self.indonesian_compliance = self._load_indonesian_compliance()
        
        # Gas optimization patterns
        self.gas_patterns = self._load_gas_optimization_patterns()
    
    def _load_smart_contract_patterns(self) -> Dict[str, List[Dict]]:
        """Load smart contract vulnerability patterns"""
        return {
            "reentrancy": [
                {
                    "pattern": r"function.*payable.*\{[^}]*\(.*call\.value",
                    "description": "Potential reentrancy vulnerability",
                    "severity": "CRITICAL",
                    "recommendation": "Use Checks-Effects-Interactions pattern and consider reentrancy guards"
                }
            ],
            "integer_overflow": [
                {
                    "pattern": r"(\+|-|\*|/)\s*uint",
                    "description": "Potential integer overflow/underflow",
                    "severity": "HIGH",
                    "recommendation": "Use SafeMath library or Solidity 0.8+ built-in overflow protection"
                }
            ],
            "access_control": [
                {
                    "pattern": r"function.*\{[^}]*owner\s*!=\s*msg\.sender",
                    "description": "Weak access control implementation",
                    "severity": "HIGH",
                    "recommendation": "Use OpenZeppelin's Ownable or AccessControl patterns"
                }
            ],
            "unchecked_external_calls": [
                {
                    "pattern": r"\.call\(.*?\)(?!\s*;\s*require)",
                    "description": "Unchecked external call return value",
                    "severity": "MEDIUM",
                    "recommendation": "Always check return values of external calls"
                }
            ],
            "tx_origin": [
                {
                    "pattern": r"tx\.origin",
                    "description": "Use of tx.origin for authentication",
                    "severity": "HIGH",
                    "recommendation": "Use msg.sender instead of tx.origin"
                }
            ],
            "block_timestamp": [
                {
                    "pattern": r"block\.timestamp",
                    "description": "Use of block.timestamp for critical logic",
                    "severity": "MEDIUM",
                    "recommendation": "Be aware that block.timestamp can be manipulated by miners"
                }
            ],
            "storage_collision": [
                {
                    "pattern": r"delegatecall.*upgradeable",
                    "description": "Potential storage collision in upgradeable contracts",
                    "severity": "HIGH",
                    "recommendation": "Use proper storage layout patterns for upgradeable contracts"
                }
            ],
            "randomness": [
                {
                    "pattern": r"block\.hash|block\.number",
                    "description": "Weak randomness source",
                    "severity": "MEDIUM",
                    "recommendation": "Use Chainlink VRF or other secure randomness sources"
                }
            ]
        }
    
    def _load_indonesian_compliance(self) -> Dict[str, Any]:
        """Load Indonesian regulatory compliance requirements"""
        return {
            "BAPPEBTI": {
                "requirements": [
                    "Smart contracts must be auditable by BAPPEBTI",
                    "All transactions must be traceable",
                    "KYC/AML compliance required for all participants",
                    "Maximum transaction limits must be enforced"
                ],
                "forbidden_functions": [
                    "anonymous transactions",
                    "privacy coins integration",
                    "mixers/tumblers"
                ]
            },
            "BI": {
                "requirements": [
                    "Cannot issue currency or stablecoins without BI approval",
                    "Must comply with payment system regulations",
                    "Cannot replace rupiah as legal tender"
                ]
            },
            "OJK": {
                "requirements": [
                    "Financial service contracts need OJK approval",
                    "Must implement consumer protection measures",
                    "Risk disclosure requirements"
                ]
            }
        }
    
    def _load_gas_optimization_patterns(self) -> Dict[str, Any]:
        """Load gas optimization patterns and anti-patterns"""
        return {
            "inefficient_patterns": [
                {
                    "pattern": r"storage.*memory.*loop",
                    "description": "Storage access in loops",
                    "gas_impact": "HIGH",
                    "recommendation": "Use memory variables for temporary calculations"
                },
                {
                    "pattern": r"string.*concatenation",
                    "description": "String concatenation in storage",
                    "gas_impact": "HIGH",
                    "recommendation": "Use events for logging instead of storage strings"
                }
            ],
            "optimization_opportunities": [
                {
                    "pattern": r"mapping.*length",
                    "description": "Using mapping with separate length counter",
                    "gas_impact": "MEDIUM",
                    "recommendation": "Consider using arrays with proper indexing"
                }
            ]
        }
    
    async def audit_smart_contract(
        self, 
        contract_source: str, 
        contract_address: str,
        contract_name: str,
        blockchain: str = "ethereum",
        additional_context: Optional[Dict] = None
    ) -> SmartContractAuditResult:
        """
        Perform comprehensive smart contract audit
        
        Args:
            contract_source: Source code of the smart contract
            contract_address: Blockchain address of the contract
            contract_name: Name of the contract
            blockchain: Blockchain platform (ethereum, polygon, etc.)
            additional_context: Additional context for audit
            
        Returns:
            SmartContractAuditResult with comprehensive audit findings
        """
        
        issues = []
        recommendations = []
        
        try:
            # 1. Security vulnerability analysis
            security_issues = await self._analyze_security_vulnerabilities(
                contract_source, contract_address
            )
            issues.extend(security_issues)
            
            # 2. Gas optimization analysis
            gas_issues = await self._analyze_gas_optimization(contract_source)
            issues.extend(gas_issues)
            
            # 3. Indonesian compliance analysis
            compliance_issues = await self._analyze_indonesian_compliance(
                contract_source, additional_context
            )
            issues.extend(compliance_issues)
            
            # 4. Logic and design pattern analysis
            logic_issues = await self._analyze_contract_logic(contract_source)
            issues.extend(logic_issues)
            
            # 5. Cryptographic analysis (if applicable)
            crypto_issues = await self._analyze_cryptography(contract_source)
            issues.extend(crypto_issues)
            
            # Calculate scores
            security_score = self._calculate_security_score(issues)
            gas_score = self._calculate_gas_optimization_score(issues)
            compliance_score = self._calculate_compliance_score(issues)
            overall_score = int((security_score + gas_score + compliance_score) / 3)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(issues)
            
            # Generate badge URL
            badge_url = self._generate_audit_badge(overall_score, contract_address)
            
            return SmartContractAuditResult(
                contract_address=contract_address,
                contract_name=contract_name,
                blockchain=blockchain,
                audit_timestamp=datetime.now(),
                overall_score=overall_score,
                security_score=security_score,
                gas_optimization_score=gas_score,
                compliance_score=compliance_score,
                issues=issues,
                recommendations=recommendations,
                badge_url=badge_url,
                is_verified=overall_score >= 70  # Minimum passing score
            )
            
        except Exception as e:
            # Critical audit failure
            return SmartContractAuditResult(
                contract_address=contract_address,
                contract_name=contract_name,
                blockchain=blockchain,
                audit_timestamp=datetime.now(),
                overall_score=0,
                security_score=0,
                gas_optimization_score=0,
                compliance_score=0,
                issues=[
                    SmartContractIssue(
                        severity="CRITICAL",
                        category="AUDIT_ERROR",
                        title="Audit Process Failed",
                        description=f"Smart contract audit failed: {str(e)}",
                        line_number=0,
                        code_snippet="",
                        recommendation="Review contract syntax and audit configuration"
                    )
                ],
                recommendations=["Fix audit errors before proceeding"],
                is_verified=False
            )
    
    async def _analyze_security_vulnerabilities(
        self, 
        contract_source: str, 
        contract_address: str
    ) -> List[SmartContractIssue]:
        """Analyze smart contract for security vulnerabilities with enhanced detection"""
        issues = []
        lines = contract_source.split('\n')
        
        # Enhanced reentrancy detection
        issues.extend(self._detect_reentrancy_vulnerabilities(contract_source))
        
        # Pattern-based vulnerability detection
        for vulnerability_type, patterns in self.vulnerability_patterns.items():
            for pattern_info in patterns:
                regex_pattern = re.compile(pattern_info["pattern"], re.IGNORECASE | re.MULTILINE)
                
                for i, line in enumerate(lines, 1):
                    if regex_pattern.search(line):
                        issues.append(SmartContractIssue(
                            severity=pattern_info["severity"],
                            category="SECURITY",
                            title=f"Potential {vulnerability_type.replace('_', ' ').title()}",
                            description=pattern_info["description"],
                            line_number=i,
                            code_snippet=line.strip(),
                            recommendation=pattern_info["recommendation"],
                            cwe_id=self._get_cwe_id(vulnerability_type),
                            owasp_id=self._get_owasp_id(vulnerability_type)
                        ))
        
        return issues
    
    def _detect_reentrancy_vulnerabilities(self, contract_source: str) -> List[SmartContractIssue]:
        """Detect reentrancy vulnerabilities with better pattern matching"""
        issues = []
        lines = contract_source.split('\n')
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check for external calls before state updates
            if any(pattern in line_stripped for pattern in ['.call{', '.call(', '.send(', '.transfer(']):
                # Look for state updates after external calls in the same function
                function_start = i
                function_end = len(lines)
                
                # Find function boundaries
                for j in range(i-1, -1, -1):
                    if 'function ' in lines[j]:
                        function_start = j
                        break
                
                for j in range(i+1, len(lines)):
                    if 'function ' in lines[j] and j > i:
                        function_end = j
                        break
                
                # Check if state update comes after external call
                state_updated_after = False
                for j in range(i+1, function_end):
                    if any(pattern in lines[j] for pattern in ['balances[', 'mapping(', '-=', '+=']):
                        state_updated_after = True
                        break
                
                if state_updated_after:
                    issues.append(SmartContractIssue(
                        title="Reentrancy Vulnerability",
                        description=f"External call on line {i+1} before state update - vulnerable to reentrancy attack",
                        severity="CRITICAL",
                        category="SECURITY",
                        line_number=i+1,
                        code_snippet=line.strip(),
                        recommendation="Use Checks-Effects-Interactions pattern or ReentrancyGuard modifier"
                    ))
        
        return issues
    
    async def _analyze_gas_optimization(self, contract_source: str) -> List[SmartContractIssue]:
        """Analyze gas optimization opportunities"""
        issues = []
        lines = contract_source.split('\n')
        
        for category, patterns in self.gas_patterns.items():
            for pattern_info in patterns:
                regex_pattern = re.compile(pattern_info["pattern"], re.IGNORECASE | re.MULTILINE)
                
                for i, line in enumerate(lines, 1):
                    if regex_pattern.search(line):
                        severity = "MEDIUM" if pattern_info["gas_impact"] == "MEDIUM" else "HIGH"
                        issues.append(SmartContractIssue(
                            severity=severity,
                            category="PERFORMANCE",
                            title=f"Gas Optimization: {pattern_info['description']}",
                            description=f"{pattern_info['description']} - Gas impact: {pattern_info['gas_impact']}",
                            line_number=i,
                            code_snippet=line.strip(),
                            recommendation=pattern_info["recommendation"]
                        ))
        
        return issues
    
    async def _analyze_indonesian_compliance(
        self, 
        contract_source: str, 
        additional_context: Optional[Dict]
    ) -> List[SmartContractIssue]:
        """Analyze compliance with Indonesian regulations"""
        issues = []
        
        # Check for forbidden functions
        for regulator, requirements in self.indonesian_compliance.items():
            if "forbidden_functions" in requirements:
                for forbidden in requirements["forbidden_functions"]:
                    if forbidden.lower() in contract_source.lower():
                        issues.append(SmartContractIssue(
                            severity="HIGH",
                            category="COMPLIANCE",
                            title=f"BI Compliance: {forbidden}",
                            description=f"Functionality not allowed by {regulator}: {forbidden}",
                            line_number=0,
                            code_snippet=forbidden,
                            recommendation=f"Remove {forbidden} functionality to comply with {regulator} regulations"
                        ))
        
        # Check for financial services that need OJK approval
        financial_keywords = ["lending", "borrowing", "interest", "yield", "staking", "insurance"]
        for keyword in financial_keywords:
            if keyword.lower() in contract_source.lower():
                issues.append(SmartContractIssue(
                    severity="MEDIUM",
                    category="COMPLIANCE",
                    title="OJK Financial Service Warning",
                    description=f"Contract contains {keyword} functionality that may require OJK approval",
                    line_number=0,
                    code_snippet=keyword,
                    recommendation="Ensure compliance with OJK regulations for financial services"
                ))
        
        return issues
    
    async def _analyze_contract_logic(self, contract_source: str) -> List[SmartContractIssue]:
        """Analyze contract logic and design patterns"""
        issues = []
        
        # Check for proper event emission
        if "emit " not in contract_source:
            issues.append(SmartContractIssue(
                severity="MEDIUM",
                category="LOGIC",
                title="Missing Event Emissions",
                description="Contract does not emit events for important state changes",
                line_number=0,
                code_snippet="",
                recommendation="Emit events for all important state changes to improve transparency"
            ))
        
        # Check for proper access control patterns
        if "onlyOwner" not in contract_source and "AccessControl" not in contract_source:
            issues.append(SmartContractIssue(
                severity="HIGH",
                category="SECURITY",
                title="Missing Access Control",
                description="Contract lacks proper access control mechanisms",
                line_number=0,
                code_snippet="",
                recommendation="Implement proper access control using OpenZeppelin libraries"
            ))
        
        return issues
    
    async def _analyze_cryptography(self, contract_source: str) -> List[SmartContractIssue]:
        """Analyze cryptographic implementations"""
        issues = []
        
        # Use existing crypto audit engine
        try:
            # Create temporary file for analysis
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sol', delete=False) as f:
                f.write(contract_source)
                temp_file = f.name
            
            # Run crypto audit
            crypto_result = await self.crypto_engine.audit_project(
                os.path.dirname(temp_file), 
                "smart_contract_crypto"
            )
            
            # Convert crypto issues to smart contract issues
            for vuln in crypto_result.vulnerabilities:
                issues.append(SmartContractIssue(
                    severity=vuln.get("severity", "MEDIUM").upper(),
                    category="SECURITY",
                    title=f"Cryptography: {vuln.get('category', 'Unknown')}",
                    description=vuln.get("description", "Cryptographic vulnerability"),
                    line_number=vuln.get("line", 0),
                    code_snippet=vuln.get("code", ""),
                    recommendation=vuln.get("recommendation", "Review cryptographic implementation")
                ))
            
            # Cleanup
            os.unlink(temp_file)
            
        except Exception as e:
            issues.append(SmartContractIssue(
                severity="LOW",
                category="SECURITY",
                title="Crypto Audit Skipped",
                description=f"Cryptographic audit skipped: {str(e)}",
                line_number=0,
                code_snippet="",
                recommendation="Manual review of cryptographic implementation recommended"
            ))
        
        return issues
    
    def _calculate_security_score(self, issues: List[SmartContractIssue]) -> int:
        """Calculate security score based on issues with stricter penalties"""
        base_score = 100
        critical_count = 0
        high_count = 0

        for issue in issues:
            if issue.category == "SECURITY":
                if issue.severity == "CRITICAL":
                    critical_count += 1
                    base_score -= 40
                elif issue.severity == "HIGH":
                    high_count += 1
                    base_score -= 25
                elif issue.severity == "MEDIUM":
                    base_score -= 10
                elif issue.severity == "LOW":
                    base_score -= 5

        # Additional penalty for multiple critical/high issues
        base_score -= (critical_count * 10 + high_count * 5)
        return max(0, base_score)
    
    def _calculate_gas_optimization_score(self, issues: List[SmartContractIssue]) -> int:
        """Calculate gas optimization score"""
        base_score = 100

        for issue in issues:
            if issue.category == "PERFORMANCE":
                if issue.severity == "HIGH":
                    base_score -= 15
                elif issue.severity == "MEDIUM":
                    base_score -= 8

        return max(0, base_score)
    
    def _calculate_compliance_score(self, issues: List[SmartContractIssue]) -> int:
        """Calculate compliance score"""
        base_score = 100

        for issue in issues:
            if issue.category == "COMPLIANCE":
                if issue.severity == "HIGH":
                    base_score -= 30
                elif issue.severity == "MEDIUM":
                    base_score -= 15

        return max(0, base_score)
    
    def _generate_recommendations(self, issues: List[SmartContractIssue]) -> List[str]:
        """Generate prioritized recommendations"""
        recommendations = []
        
        # Group issues by severity
        critical_issues = [i for i in issues if i.severity == "CRITICAL"]
        high_issues = [i for i in issues if i.severity == "HIGH"]
        
        if critical_issues:
            recommendations.append("🚨 **CRITICAL: Fix all critical vulnerabilities before deployment**")
            for issue in critical_issues[:3]:  # Top 3 critical
                recommendations.append(f"   - {issue.title}: {issue.recommendation}")
        
        if high_issues:
            recommendations.append("⚠️  **HIGH PRIORITY: Address high-severity issues**")
            for issue in high_issues[:2]:  # Top 2 high
                recommendations.append(f"   - {issue.title}: {issue.recommendation}")
        
        # General recommendations
        recommendations.extend([
            "✅ Use OpenZeppelin battle-tested libraries",
            "✅ Implement comprehensive access control",
            "✅ Add extensive event logging for transparency",
            "✅ Consider formal verification for critical contracts",
            "✅ Regular security audits and penetration testing"
        ])
        
        return recommendations
    
    def _generate_audit_badge(self, score: int, contract_address: str) -> str:
        """Generate audit badge URL based on score"""
        if score >= 90:
            badge = "certified-excellent"
        elif score >= 80:
            badge = "certified-good"
        elif score >= 70:
            badge = "certified-pass"
        else:
            badge = "needs-improvement"
        
        # Generate badge URL (in production, this would point to actual badge service)
        return f"https://sangkuriang.id/badges/smart-contract/{badge}/{contract_address[:10]}"
    
    def _get_cwe_id(self, vulnerability_type: str) -> Optional[str]:
        """Get CWE ID for vulnerability type"""
        cwe_mapping = {
            "reentrancy": "CWE-841",
            "integer_overflow": "CWE-190",
            "access_control": "CWE-284",
            "unchecked_external_calls": "CWE-252",
            "tx_origin": "CWE-285"
        }
        return cwe_mapping.get(vulnerability_type)
    
    def _get_owasp_id(self, vulnerability_type: str) -> Optional[str]:
        """Get OWASP ID for vulnerability type"""
        owasp_mapping = {
            "reentrancy": "OWASP-SC01",
            "integer_overflow": "OWASP-SC02",
            "access_control": "OWASP-SC03",
            "unchecked_external_calls": "OWASP-SC04"
        }
        return owasp_mapping.get(vulnerability_type)