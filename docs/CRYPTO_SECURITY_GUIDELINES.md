# SANGKURIANG Cryptographic Security Guidelines

## Overview

This document outlines the security guidelines and requirements for cryptographic projects submitted to the SANGKURIANG platform. All projects must adhere to these guidelines to ensure the highest standards of cryptographic security.

## Cryptographic Algorithm Standards

### Approved Algorithms

#### Symmetric Encryption
- **AES (Advanced Encryption Standard)**
  - Key sizes: 128, 192, 256 bits
  - Modes: GCM, CBC, CTR, OFB
  - Requirements: Must use secure random IV/nonce

- **ChaCha20-Poly1305**
  - Authenticated encryption with associated data (AEAD)
  - Recommended for mobile and resource-constrained environments

#### Asymmetric Encryption
- **RSA**
  - Minimum key size: 2048 bits (recommended: 3072 bits)
  - Padding: OAEP (Optimal Asymmetric Encryption Padding)
  - Deprecated: PKCS#1 v1.5 padding

- **Elliptic Curve Cryptography (ECC)**
  - Curves: NIST P-256, P-384, P-521
  - Alternative: Curve25519, Curve448
  - Key exchange: ECDH
  - Digital signatures: ECDSA, EdDSA

#### Hash Functions
- **SHA-2 Family**
  - SHA-256, SHA-384, SHA-512
  - Secure for all applications

- **SHA-3 Family**
  - SHA3-256, SHA3-384, SHA3-512
  - Recommended for new implementations

- **BLAKE2/BLAKE3**
  - High-performance alternative
  - Suitable for resource-constrained environments

#### Key Derivation Functions
- **PBKDF2**
  - Minimum iterations: 100,000
  - Salt length: Minimum 128 bits

- **Argon2**
  - Winner of Password Hashing Competition
  - Recommended for password hashing

- **scrypt**
  - Memory-hard function
  - Suitable for password-based key derivation

### Deprecated/Prohibited Algorithms

#### Never Use
- **DES/3DES**: Weak encryption, vulnerable to attacks
- **RC4**: Broken stream cipher
- **MD5**: Cryptographically broken hash function
- **SHA-1**: Deprecated hash function
- **RSA with PKCS#1 v1.5**: Vulnerable to padding oracle attacks

## Implementation Requirements

### Random Number Generation
- Use cryptographically secure random number generators (CSPRNG)
- Approved sources:
  - `/dev/urandom` on Unix systems
  - `CryptGenRandom` on Windows
  - Hardware security modules (HSMs) where available
- Never use `Math.random()` or similar weak PRNGs

### Key Management
- **Key Generation**
  - Use approved algorithms for key generation
  - Ensure sufficient entropy (minimum 256 bits)
  - Test keys for weakness before use

- **Key Storage**
  - Encrypt keys at rest using master encryption keys
  - Use hardware security modules (HSMs) for high-value keys
  - Implement key rotation policies
  - Never hardcode keys in source code

- **Key Exchange**
  - Use established key exchange protocols (ECDH, RSA-OAEP)
  - Implement perfect forward secrecy where possible
  - Validate public keys before use

### Secure Coding Practices

#### Input Validation
- Validate all cryptographic inputs (keys, IVs, ciphertext)
- Check for valid key lengths and formats
- Implement bounds checking for all operations
- Use constant-time comparisons for sensitive data

#### Side-Channel Attack Prevention
- Implement constant-time algorithms where applicable
- Avoid branching on secret data
- Use blinding techniques for RSA operations
- Implement proper memory clearing for sensitive data

#### Error Handling
- Never expose sensitive information in error messages
- Use generic error messages for cryptographic failures
- Implement proper logging without revealing secrets
- Handle edge cases gracefully

## Quantum-Resistant Considerations

### Post-Quantum Cryptography (PQC)
- Monitor NIST PQC standardization process
- Prepare for migration to quantum-resistant algorithms
- Consider hybrid approaches during transition period

### Recommended PQC Algorithms (Experimental)
- **Lattice-based**: Kyber (KEM), Dilithium (signatures)
- **Hash-based**: SPHINCS+ (signatures)
- **Code-based**: Classic McEliece (KEM)

## Security Testing Requirements

### Static Analysis
- Use cryptographic linters and analyzers
- Check for hardcoded keys and weak algorithms
- Verify proper use of cryptographic APIs
- Scan for common vulnerabilities (CWE-327, CWE-780)

### Dynamic Testing
- Test with known test vectors
- Implement fuzzing for cryptographic inputs
- Test error handling and edge cases
- Verify constant-time implementations

### Penetration Testing
- Engage third-party security auditors
- Test for side-channel vulnerabilities
- Verify key management procedures
- Assess overall system security

## Platform-Specific Guidelines

### Mobile Applications
- Use platform-provided cryptographic APIs (iOS Keychain, Android Keystore)
- Implement certificate pinning for network communications
- Protect against jailbreak/root detection bypass
- Use secure storage for sensitive data

### Web Applications
- Implement Content Security Policy (CSP)
- Use HTTPS with strong TLS configuration
- Implement proper session management
- Protect against XSS and CSRF attacks

### IoT and Embedded Systems
- Consider resource constraints in algorithm selection
- Implement secure boot and firmware update mechanisms
- Use hardware security features when available
- Implement secure key storage in constrained environments

## Audit and Certification Process

### Submission Requirements
1. **Source Code Review**
   - Complete source code access
   - Documentation of cryptographic implementations
   - Security architecture documentation
   - Threat model and risk assessment

2. **Testing Results**
   - Unit test coverage reports
   - Security testing results
   - Performance benchmarks
   - Compatibility test results

3. **Compliance Documentation**
   - Algorithm usage justification
   - Key management procedures
   - Security policy documentation
   - Incident response procedures

### Audit Process
1. **Automated Scanning**
   - Static code analysis
   - Dependency vulnerability scanning
   - Configuration security assessment

2. **Manual Review**
   - Cryptographic implementation review
   - Security architecture assessment
   - Code quality evaluation
   - Documentation completeness check

3. **Certification Levels**
   - **Bronze**: Basic security compliance
   - **Silver**: Enhanced security with additional testing
   - **Gold**: Comprehensive security with third-party audit
   - **Platinum**: Enterprise-grade security with formal verification

## Incident Response

### Security Incident Categories
- **Critical**: Key compromise, algorithm weakness discovered
- **High**: Implementation vulnerability, side-channel attack
- **Medium**: Configuration weakness, documentation issue
- **Low**: Best practice violation, minor security concern

### Response Procedures
1. **Immediate Actions**
   - Isolate affected systems
   - Assess impact and scope
   - Notify stakeholders
   - Document incident details

2. **Investigation**
   - Root cause analysis
   - Impact assessment
   - Solution development
   - Testing and validation

3. **Recovery**
   - Implement fixes and patches
   - Verify system integrity
   - Update security measures
   - Monitor for recurrence

## Best Practices Summary

### Do's
- ✅ Use approved cryptographic algorithms
- ✅ Implement proper key management
- ✅ Use cryptographically secure random number generators
- ✅ Validate all inputs and outputs
- ✅ Implement defense in depth
- ✅ Keep cryptographic libraries updated
- ✅ Follow principle of least privilege
- ✅ Implement proper logging and monitoring

### Don'ts
- ❌ Use deprecated or weak algorithms
- ❌ Hardcode cryptographic keys
- ❌ Use weak random number generators
- ❌ Ignore side-channel attack vectors
- ❌ Expose sensitive information in errors
- ❌ Skip security testing and review
- ❌ Use outdated cryptographic libraries
- ❌ Ignore regulatory compliance requirements

## Resources and References

### Standards and Guidelines
- NIST Special Publication 800-57 (Key Management)
- NIST Special Publication 800-53 (Security Controls)
- OWASP Cryptographic Storage Cheat Sheet
- IETF RFCs for specific protocols

### Tools and Libraries
- **Libraries**: libsodium, Bouncy Castle, OpenSSL
- **Testing**: Cryptofuzz, NIST test vectors
- **Analysis**: Cryptol, ProVerif, Tamarin

### Training and Education
- Cryptography engineering courses
- Security certification programs
- Industry conference participation
- Regular security awareness training

---

**Document Version**: 1.0  
**Last Updated**: January 2025  
**Next Review**: March 2025  
**Document Owner**: Security Engineering Team

For questions or clarifications, contact: security@sangkuriang.id