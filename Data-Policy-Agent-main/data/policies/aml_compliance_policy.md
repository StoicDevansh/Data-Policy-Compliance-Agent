# Anti-Money Laundering (AML) Compliance Policy

**Version:** 2.0  
**Effective Date:** January 1, 2026  
**Last Reviewed:** February 21, 2026  
**Policy Owner:** Chief Compliance Officer  
**Applicable Regulations:** Bank Secrecy Act (BSA), USA PATRIOT Act, FATF Recommendations

---

## 1. Purpose

This policy establishes the requirements and procedures for detecting, preventing, and reporting money laundering activities. All financial transactions processed by the organization must comply with applicable anti-money laundering laws and regulations.

## 2. Scope

This policy applies to:

- All financial transactions processed through our systems
- All employees, contractors, and third parties with transaction access
- All customer accounts and business relationships
- All domestic and international transfers

## 3. Transaction Monitoring Requirements

### 3.1 Large Transaction Reporting

**MANDATORY:** All transactions exceeding **$10,000** (or equivalent in foreign currency) MUST be reported to the Financial Crimes Enforcement Network (FinCEN) within **15 days**.

- Individual cash transactions over $10,000 require CTR filing
- Aggregated transactions from same customer totaling over $10,000 within a single business day require reporting
- Wire transfers over $3,000 require enhanced record-keeping

### 3.2 Suspicious Activity Detection

The following patterns MUST be flagged for immediate review:

1. **Structuring (Smurfing)**
   - Multiple transactions just below $10,000 threshold
   - Specifically, transactions between **$9,000 and $9,999** require enhanced scrutiny
   - More than **3 transactions** in this range within **7 days** from same account triggers mandatory review

2. **Velocity Monitoring**
   - More than **5 transfers** to the same beneficiary within **24 hours** MUST be flagged
   - More than **10 transactions** from a single account within **1 hour** requires review
   - Daily aggregate transfers exceeding **$50,000** require supervisor approval

3. **Round Number Detection**
   - Transactions in exact round amounts (e.g., $10,000, $25,000, $50,000, $100,000) require additional verification

### 3.3 High-Risk Transaction Types

The following transaction types require enhanced due diligence:

| Transaction Type    | Threshold | Action Required          |
| ------------------- | --------- | ------------------------ |
| International Wire  | > $5,000  | Enhanced review          |
| Cryptocurrency      | > $3,000  | Full documentation       |
| Cash Deposit        | > $5,000  | Source verification      |
| Third-Party Payment | > $2,500  | Beneficiary verification |

## 4. Account Monitoring Requirements

### 4.1 New Account Monitoring

All new accounts SHALL be monitored for a period of **90 days** with enhanced scrutiny:

- First transaction from new account requires verification
- Large first transaction (> $5,000) requires manager approval
- Multiple accounts opened by same customer within 30 days require investigation

### 4.2 Dormant Account Reactivation

Accounts inactive for more than **180 days** that suddenly show activity:

- MUST trigger automatic review if transaction exceeds **$1,000**
- Require customer verification for transactions over **$5,000**

## 5. Cross-Border Transaction Rules

### 5.1 Geographic Restrictions

Transactions involving high-risk jurisdictions as defined by FATF SHALL:

- Be flagged automatically regardless of amount
- Require compliance officer approval for transactions over **$1,000**
- Be prohibited entirely for OFAC-sanctioned countries

### 5.2 International Transfer Reporting

All international transfers MUST include:

- Full originator name and account number
- Full beneficiary name and account number
- Purpose of transfer
- Originating and receiving bank information

## 6. Audit Trail Requirements

### 6.1 Transaction Logging

All transactions MUST be logged with:

- Timestamp (UTC)
- Transaction ID
- Originator account
- Beneficiary account
- Amount and currency
- Transaction type
- User/system that initiated the transaction

### 6.2 Retention Period

Transaction records MUST be retained for a minimum of **7 years** from the date of transaction.

Log access records MUST be maintained for **5 years**.

## 7. Reporting Requirements

### 7.1 Suspicious Activity Reports (SARs)

SARs MUST be filed within **30 days** of detection for:

- Any transaction flagged by automated systems
- Any transaction violating policies in this document
- Any customer behavior indicating potential money laundering

### 7.2 Internal Escalation

| Severity | Escalation Required | Timeframe       |
| -------- | ------------------- | --------------- |
| Critical | CCO + Legal         | Immediately     |
| High     | Compliance Manager  | Within 2 hours  |
| Medium   | Team Lead           | Within 24 hours |
| Low      | Document only       | Within 48 hours |

## 8. Compliance Violations

### 8.1 Violation Categories

- **Critical:** Transactions flagged as laundering that were not reported
- **High:** Missing SAR filing for flagged transactions
- **Medium:** Incomplete documentation
- **Low:** Minor procedural deviations

### 8.2 Remediation Requirements

All violations MUST be:

- Documented within **24 hours** of detection
- Assigned remediation owner
- Resolved within **30 days** (critical/high) or **90 days** (medium/low)

## 9. Technology Controls

### 9.1 Automated Monitoring

The compliance monitoring system MUST:

- Scan all transactions in real-time
- Apply all rules defined in this policy
- Generate alerts for violations
- Maintain audit trail of all scans

### 9.2 Alert Response SLA

| Alert Type | Response Time | Resolution Time |
| ---------- | ------------- | --------------- |
| Critical   | 15 minutes    | 4 hours         |
| High       | 1 hour        | 24 hours        |
| Medium     | 4 hours       | 72 hours        |
| Low        | 24 hours      | 7 days          |

---

## Document Control

| Version | Date       | Author     | Changes         |
| ------- | ---------- | ---------- | --------------- |
| 2.0     | 2026-01-01 | Compliance | Annual update   |
| 1.0     | 2025-01-01 | Compliance | Initial release |

---

_This policy is reviewed annually and updated as needed to reflect changes in regulations and best practices._
