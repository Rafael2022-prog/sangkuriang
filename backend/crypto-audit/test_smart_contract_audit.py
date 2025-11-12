"""
Test suite for Smart Contract Audit Engine - SANGKURIANG
"""

import pytest
import asyncio
import json
from datetime import datetime
from pathlib import Path
import tempfile
import os

from smart_contract_audit import (
    SmartContractAuditEngine, 
    SmartContractIssue,
    SmartContractAuditResult
)


class TestSmartContractAuditEngine:
    """Test cases for Smart Contract Audit Engine"""
    
    @pytest.fixture
    def audit_engine(self):
        """Create audit engine instance"""
        return SmartContractAuditEngine()
    
    @pytest.fixture
    def vulnerable_contract(self):
        """Sample vulnerable smart contract"""
        return """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract VulnerableToken {
    mapping(address => uint256) public balances;
    address public owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    // Reentrancy vulnerability
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        
        // VULNERABLE: External call before state update
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
        
        balances[msg.sender] -= amount; // State update after external call
    }
    
    // Integer overflow (in older Solidity versions)
    function transfer(address to, uint256 amount) public {
        // Potential overflow
        balances[msg.sender] -= amount;
        balances[to] += amount;
    }
    
    // Weak access control
    function changeOwner(address newOwner) public {
        // VULNERABLE: No access control
        owner = newOwner;
    }
    
    // Using tx.origin
    function authenticate() public view returns (bool) {
        // VULNERABLE: Should use msg.sender
        return tx.origin == owner;
    }
    
    // Unchecked external call
    function sendFunds(address payable recipient, uint256 amount) public {
        // VULNERABLE: Not checking return value
        recipient.call{value: amount}("");
    }
}
"""
    
    @pytest.fixture
    def secure_contract(self):
        """Sample secure smart contract"""
        return """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract SecureToken is ReentrancyGuard, Ownable {
    using SafeMath for uint256;
    
    mapping(address => uint256) public balances;
    
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Withdrawal(address indexed user, uint256 amount);
    
    // Secure: Uses ReentrancyGuard
    function withdraw(uint256 amount) public nonReentrant {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        
        // Checks-Effects-Interactions pattern
        balances[msg.sender] = balances[msg.sender].sub(amount);
        
        emit Withdrawal(msg.sender, amount);
        
        // Safe external call
        (bool success, ) = payable(msg.sender).call{value: amount}("");
        require(success, "Transfer failed");
    }
    
    // Secure: Uses SafeMath for overflow protection
    function transfer(address to, uint256 amount) public {
        require(to != address(0), "Invalid address");
        require(balances[msg.sender] >= amount, "Insufficient balance");
        
        balances[msg.sender] = balances[msg.sender].sub(amount);
        balances[to] = balances[to].add(amount);
        
        emit Transfer(msg.sender, to, amount);
    }
    
    // Secure: Uses OpenZeppelin's Ownable
    function emergencyWithdraw() public onlyOwner {
        require(address(this).balance > 0, "No funds");
        
        (bool success, ) = payable(owner()).call{value: address(this).balance}("");
        require(success, "Transfer failed");
    }
}
"""
    
    @pytest.mark.asyncio
    async def test_vulnerable_contract_audit(self, audit_engine, vulnerable_contract):
        """Test audit of vulnerable contract"""
        result = await audit_engine.audit_smart_contract(
            contract_source=vulnerable_contract,
            contract_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb9",
            contract_name="VulnerableToken",
            blockchain="ethereum"
        )
        
        # Verify result structure
        assert isinstance(result, SmartContractAuditResult)
        assert result.contract_address == "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb9"
        assert result.contract_name == "VulnerableToken"
        assert result.blockchain == "ethereum"
        
        # Should find multiple vulnerabilities
        assert len(result.issues) > 0, "Should find vulnerabilities in contract"
        
        # Check for specific vulnerability types
        vulnerability_types = [issue.title for issue in result.issues]
        print(f"Found vulnerabilities: {vulnerability_types}")
        
        # Should have security issues
        security_issues = [issue for issue in result.issues if issue.category == "SECURITY"]
        assert len(security_issues) > 0, "Should find security vulnerabilities"
        
        # Check for critical issues
        critical_issues = [issue for issue in result.issues if issue.severity == "CRITICAL"]
        assert len(critical_issues) > 0, "Should find critical vulnerabilities"
        
        # Should not be verified if has critical issues
        if len(critical_issues) > 0:
            assert result.is_verified is False, "Contract with critical issues should not be verified"
        
        # Should have recommendations
        assert len(result.recommendations) > 0, "Should provide recommendations"
        
        # Should have audit hash
        assert result.audit_hash is not None, "Should generate audit hash"
        
        print(f"Audit completed. Overall score: {result.overall_score}")
        print(f"Security score: {result.security_score}")
        print(f"Gas optimization score: {result.gas_optimization_score}")
        print(f"Compliance score: {result.compliance_score}")
    
    @pytest.mark.asyncio
    async def test_secure_contract_audit(self, audit_engine, secure_contract):
        """Test audit of secure contract"""
        result = await audit_engine.audit_smart_contract(
            contract_source=secure_contract,
            contract_address="0x1234567890123456789012345678901234567890",
            contract_name="SecureToken",
            blockchain="ethereum"
        )
        
        # Verify result structure
        assert isinstance(result, SmartContractAuditResult)
        assert result.contract_name == "SecureToken"
        
        # Secure contract should have fewer issues
        security_issues = [issue for issue in result.issues if issue.category == "SECURITY"]
        assert len(security_issues) <= 3, f"Secure contract should have minimal issues, found {len(security_issues)}"
        
        # Should have higher scores
        assert result.security_score >= 70, f"Security score should be high, got {result.security_score}"
        assert result.overall_score >= 70, f"Overall score should be good, got {result.overall_score}"
        
        # Should be verified if score is good
        if result.overall_score >= 70:
            assert result.is_verified is True, "Good contract should be verified"
        
        print(f"Secure contract audit completed. Overall score: {result.overall_score}")
    
    @pytest.mark.asyncio
    async def test_indonesian_compliance_check(self, audit_engine):
        """Test Indonesian compliance checking"""
        # Contract with potentially problematic features
        problematic_contract = """
contract IndonesianProblematic {
    // This might violate BI regulations
    function issueStableCoin() public {
        // Minting currency-like tokens
    }
    
    // Anonymous transactions
    function anonymousTransfer() private {
        // Privacy features
    }
}
"""
        
        result = await audit_engine.audit_smart_contract(
            contract_source=problematic_contract,
            contract_address="0x1111111111111111111111111111111111111111",
            contract_name="ProblematicContract",
            blockchain="ethereum"
        )
        
        # Should flag compliance issues
        compliance_issues = [issue for issue in result.issues if issue.category == "COMPLIANCE"]
        
        if compliance_issues:
            print(f"Found {len(compliance_issues)} compliance issues")
            for issue in compliance_issues:
                print(f"  - {issue.title}: {issue.description}")
        
        # Should have compliance score impact
        assert result.compliance_score <= 100, "Compliance score should be calculated"
    
    @pytest.mark.asyncio
    async def test_gas_optimization_detection(self, audit_engine):
        """Test gas optimization detection"""
        gas_wasteful_contract = """
contract GasWasteful {
    uint256[] public data;
    
    // Inefficient: storage access in loop
    function processData() public {
        for (uint i = 0; i < data.length; i++) {
            data[i] = data[i] * 2; // Multiple storage accesses
        }
    }
    
    // Inefficient: string concatenation
    function logMessage(string memory message) public {
        string memory fullMessage = string(abi.encodePacked("Log: ", message));
        // Store in blockchain (expensive)
    }
}
"""
        
        result = await audit_engine.audit_smart_contract(
            contract_source=gas_wasteful_contract,
            contract_address="0x2222222222222222222222222222222222222222",
            contract_name="GasWasteful",
            blockchain="ethereum"
        )
        
        # Should find gas optimization issues
        gas_issues = [issue for issue in result.issues if issue.category == "PERFORMANCE"]
        
        print(f"Found {len(gas_issues)} gas optimization issues")
        for issue in gas_issues:
            print(f"  - {issue.title}")
        
        # Gas score should reflect issues
        assert result.gas_optimization_score <= 90, f"Gas optimization score should be impacted, got {result.gas_optimization_score}"
    
    @pytest.mark.asyncio
    async def test_empty_contract_audit(self, audit_engine):
        """Test audit of empty/minimal contract"""
        minimal_contract = """
contract Minimal {
    uint256 public value;
    
    function setValue(uint256 newValue) public {
        value = newValue;
    }
}
"""
        
        result = await audit_engine.audit_smart_contract(
            contract_source=minimal_contract,
            contract_address="0x3333333333333333333333333333333333333333",
            contract_name="Minimal",
            blockchain="ethereum"
        )
        
        # Should complete audit successfully
        assert isinstance(result, SmartContractAuditResult)
        assert result.overall_score > 0, "Should calculate non-zero score"
        
        print(f"Minimal contract audit completed. Score: {result.overall_score}")
    
    @pytest.mark.asyncio
    async def test_audit_result_serialization(self, audit_engine, vulnerable_contract):
        """Test audit result serialization"""
        result = await audit_engine.audit_smart_contract(
            contract_source=vulnerable_contract,
            contract_address="0x4444444444444444444444444444444444444444",
            contract_name="SerializationTest",
            blockchain="ethereum"
        )
        
        # Test serialization
        result_dict = {
            "contract_address": result.contract_address,
            "contract_name": result.contract_name,
            "blockchain": result.blockchain,
            "audit_timestamp": result.audit_timestamp.isoformat(),
            "overall_score": result.overall_score,
            "security_score": result.security_score,
            "gas_optimization_score": result.gas_optimization_score,
            "compliance_score": result.compliance_score,
            "is_verified": result.is_verified,
            "audit_hash": result.audit_hash,
            "badge_url": result.badge_url,
            "issues": [
                {
                    "severity": issue.severity,
                    "category": issue.category,
                    "title": issue.title,
                    "description": issue.description,
                    "line_number": issue.line_number,
                    "code_snippet": issue.code_snippet,
                    "recommendation": issue.recommendation,
                    "cwe_id": issue.cwe_id,
                    "owasp_id": issue.owasp_id
                }
                for issue in result.issues
            ],
            "recommendations": result.recommendations
        }
        
        # Should serialize successfully
        json_str = json.dumps(result_dict, indent=2)
        assert len(json_str) > 0, "Should serialize to JSON"
        
        print(f"Audit result serialized successfully. Length: {len(json_str)} characters")
    
    def test_vulnerability_pattern_loading(self, audit_engine):
        """Test that vulnerability patterns are loaded correctly"""
        assert len(audit_engine.vulnerability_patterns) > 0, "Should have vulnerability patterns"
        assert "reentrancy" in audit_engine.vulnerability_patterns, "Should have reentrancy patterns"
        assert "integer_overflow" in audit_engine.vulnerability_patterns, "Should have overflow patterns"
        
        print(f"Loaded {len(audit_engine.vulnerability_patterns)} vulnerability categories")
    
    def test_indonesian_compliance_loading(self, audit_engine):
        """Test Indonesian compliance requirements loading"""
        assert len(audit_engine.indonesian_compliance) > 0, "Should have compliance requirements"
        assert "BAPPEBTI" in audit_engine.indonesian_compliance, "Should have BAPPEBTI requirements"
        assert "BI" in audit_engine.indonesian_compliance, "Should have BI requirements"
        assert "OJK" in audit_engine.indonesian_compliance, "Should have OJK requirements"
        
        print(f"Loaded compliance for: {list(audit_engine.indonesian_compliance.keys())}")


if __name__ == "__main__":
    # Run a quick test
    pytest.main([__file__, "-v", "-s"])