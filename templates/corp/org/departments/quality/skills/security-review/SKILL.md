---
name: security-review
description: Conduct security reviews and audits. Use when reviewing code for security vulnerabilities, assessing security posture, or creating security documentation.
allowed-tools: Read, Grep, Glob
---

# Security Review Skill

## Overview

This skill provides guidance for conducting security reviews within Quality department.

## OWASP Top 10 Checklist

1. **Injection** - SQL, NoSQL, OS, LDAP injection
2. **Broken Authentication** - Session management flaws
3. **Sensitive Data Exposure** - Encryption, key management
4. **XML External Entities (XXE)** - XML parser vulnerabilities
5. **Broken Access Control** - Authorization bypass
6. **Security Misconfiguration** - Default configs, verbose errors
7. **Cross-Site Scripting (XSS)** - Reflected, stored, DOM-based
8. **Insecure Deserialization** - Remote code execution
9. **Using Components with Known Vulnerabilities** - Dependencies
10. **Insufficient Logging & Monitoring** - Detection gaps

## Review Process

1. Identify sensitive data flows
2. Check authentication mechanisms
3. Review authorization controls
4. Scan for known vulnerabilities
5. Verify secure configurations
6. Document findings with severity

## Severity Levels

- **Critical**: Immediate exploitation possible, high impact
- **High**: Exploitation likely, significant impact
- **Medium**: Exploitation possible, moderate impact
- **Low**: Exploitation difficult, limited impact
- **Info**: Best practice recommendations
