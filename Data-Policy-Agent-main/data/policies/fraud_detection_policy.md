# Financial Fraud Detection and Prevention Policy

**Version:** 1.5  
**Effective Date:** January 1, 2026  
**Last Reviewed:** February 21, 2026  
**Policy Owner:** Chief Risk Officer  
**Applicable Standards:** PCI-DSS, SOX, Internal Controls Framework

---

## 1. Purpose

This policy establishes requirements for detecting and preventing fraudulent financial transactions across all payment systems and channels. The organization is committed to protecting customers, stakeholders, and assets from financial fraud.

## 2. Scope

This policy applies to:

- All payment transactions (PAYMENT, TRANSFER, CASH_OUT, CASH_IN, DEBIT)
- All customer accounts and merchant relationships
- All digital and physical payment channels
- Mobile money and electronic payment systems

## 3. Fraud Detection Rules

### 3.1 Transaction Amount Thresholds

**MANDATORY FRAUD CHECKS:**

| Transaction Type | Alert Threshold | Block Threshold |
| ---------------- | --------------- | --------------- |
| TRANSFER         | > $200,000      | > $500,000      |
| CASH_OUT         | > $100,000      | > $250,000      |
| PAYMENT          | > $50,000       | > $150,000      |
| DEBIT            | > $25,000       | > $100,000      |
| CASH_IN          | > $75,000       | > $200,000      |

### 3.2 Balance-Based Fraud Indicators

The following balance conditions MUST trigger fraud alerts:

1. **Zero Balance After Transaction**
   - Any transaction where `newbalanceOrig` equals **0** AND transaction amount > **$1,000** MUST be reviewed
   - Complete account drain in single transaction is HIGH RISK

2. **Negative Balance Prevention**
   - Transactions that would result in negative balance MUST be blocked
   - Any bypass of negative balance controls is a **CRITICAL** violation

3. **Balance Discrepancy**
   - If `oldbalanceOrig - amount ≠ newbalanceOrig` (within tolerance of $0.01), flag as potential fraud
   - Balance manipulation is a **CRITICAL** security incident

### 3.3 Transaction Velocity Rules

**REAL-TIME MONITORING REQUIRED:**

| Metric                               | Threshold      | Action               |
| ------------------------------------ | -------------- | -------------------- |
| Transactions per hour (same account) | > 10           | Flag for review      |
| Transactions per day (same account)  | > 50           | Require verification |
| Total daily amount (same account)    | > $100,000     | Manager approval     |
| Failed transaction attempts          | > 5 in 10 mins | Temporary block      |

### 3.4 Flagged Fraud Handling

When `isFlaggedFraud = 1`:

- Transaction MUST be held for manual review
- Customer contact required within **2 hours**
- Resolution required within **24 hours**
- Unresolved flagged transactions MUST be reported to Risk Committee daily

When `isFraud = 1` (confirmed fraud):

- Transaction MUST be reversed if possible
- Account MUST be suspended immediately
- Law enforcement notification within **24 hours** for amounts > **$10,000**
- Customer reimbursement process initiated within **48 hours**

## 4. Account-Level Fraud Prevention

### 4.1 Account Opening Fraud Prevention

- New accounts MAY NOT process transactions > **$5,000** in first **7 days**
- First transaction from new account requires step-up authentication
- Multiple failed KYC attempts (> 3) MUST block account creation

### 4.2 Account Takeover Prevention

Indicators requiring immediate action:

- Password changes followed by large transaction within **1 hour**
- Device/location change combined with transaction > **$1,000**
- Multiple simultaneous sessions from different locations

### 4.3 Merchant Fraud Prevention

- New merchants limited to **$10,000** daily processing for first **30 days**
- Chargeback rate > **1%** triggers enhanced monitoring
- Chargeback rate > **2%** results in account suspension

## 5. Channel-Specific Controls

### 5.1 Mobile Money Controls

- Single transaction limit: **$10,000**
- Daily transaction limit: **$50,000**
- Required 2FA for transactions > **$500**
- Biometric verification required for transactions > **$5,000**

### 5.2 Online Payment Controls

- 3D Secure required for card transactions > **$100**
- Address Verification Service (AVS) required for all transactions
- CVV verification mandatory (no exceptions)

### 5.3 Wire Transfer Controls

- Dual approval required for amounts > **$25,000**
- Callback verification required for new beneficiaries
- Hold period of **24 hours** for first-time international wires

## 6. Response and Remediation

### 6.1 Incident Classification

| Level    | Description               | Response Time   |
| -------- | ------------------------- | --------------- |
| Critical | Confirmed fraud > $50,000 | Immediate       |
| High     | Suspected fraud > $10,000 | Within 1 hour   |
| Medium   | Anomaly detection alerts  | Within 4 hours  |
| Low      | Pattern deviation         | Within 24 hours |

### 6.2 Escalation Matrix

| Amount             | Level 1       | Level 2   | Level 3     |
| ------------------ | ------------- | --------- | ----------- |
| < $10,000          | Fraud Analyst | Team Lead | -           |
| $10,000 - $50,000  | Team Lead     | Manager   | Director    |
| $50,000 - $250,000 | Manager       | Director  | CRO         |
| > $250,000         | Director      | CRO       | CEO + Board |

## 7. Reporting and Compliance

### 7.1 Daily Reports

The fraud monitoring system MUST generate daily reports including:

- Total flagged transactions
- Fraud confirmation rate
- False positive rate
- Average response time
- Total fraud losses

### 7.2 Regulatory Reporting

- SAR filing required for confirmed fraud > **$5,000**
- Law enforcement notification for confirmed fraud > **$25,000**
- Quarterly fraud statistics to Board of Directors

## 8. Audit and Monitoring Requirements

### 8.1 Transaction Logging

ALL transactions MUST log:

- Unique transaction ID
- Timestamp (UTC)
- Transaction type
- Amount
- Origin account and balance (before/after)
- Destination account and balance (before/after)
- Fraud flags and scores
- Device fingerprint
- IP address and geolocation

### 8.2 Retention Requirements

- Transaction logs: **7 years**
- Fraud investigation records: **10 years**
- Customer dispute records: **5 years**

## 9. System Requirements

### 9.1 Real-Time Processing

The fraud detection system MUST:

- Process transactions within **100ms**
- Apply all rules synchronously
- Generate alerts immediately
- Block suspicious transactions before completion

### 9.2 Machine Learning Integration

- ML fraud scores MUST be logged for all transactions
- Model performance reviewed **monthly**
- Retraining required if precision drops below **95%**

---

## Document Control

| Version | Date       | Changes                  |
| ------- | ---------- | ------------------------ |
| 1.5     | 2026-01-01 | Enhanced ML requirements |
| 1.0     | 2025-06-01 | Initial release          |

---

_This policy is aligned with PaySim transaction monitoring standards and best practices for mobile financial services fraud prevention._
