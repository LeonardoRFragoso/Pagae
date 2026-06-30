# Risk Analysis — Brazilian BNPL Platform

> **Classification:** Internal — Confidential  
> **Date:** June 2026  
> **Version:** 1.0

---

## 1. Risk Framework Overview

This platform operates at the intersection of financial services, technology, and consumer credit. Risk management is **not a feature — it is the product**. A BNPL platform that cannot manage credit risk profitably will not survive.

Risk domains:

1. **Credit Risk** — consumers who cannot or will not repay
2. **Fraud Risk** — bad actors exploiting the credit system
3. **Operational Risk** — system failures, process failures, people failures
4. **Regulatory Risk** — non-compliance with BCB, LGPD, AML/KYC
5. **Market Risk** — macroeconomic factors affecting portfolio quality
6. **Concentration Risk** — over-exposure to single merchants/verticals/geographies
7. **Liquidity Risk** — funding mismatches in the FIDC structure

---

## 2. Credit Risk

### 2.1 Nature of BNPL Credit Risk

BNPL credit is **micro-duration, high-frequency consumer credit**:
- Typical exposure: R$100–3,000 per transaction
- Duration: 6–168 days (4x biweekly to 12x monthly)
- Volume: thousands of originations per day
- Character: unsecured, no collateral

Unlike a mortgage or auto loan, BNPL has **no collateral recovery path**. The entire business model depends on accurate upfront credit selection.

### 2.2 Credit Risk Taxonomy

| Risk Type | Description | Impact |
|-----------|-------------|--------|
| **Default Risk** | Consumer fails to pay one or more installments | Direct P&L loss |
| **First-Party Fraud** | Consumer never intended to pay | High — structural risk |
| **Early Delinquency** | First installment missed | Predictor of total loss |
| **Rollover Risk** | Consumer approved for more than they can service | Portfolio degradation |
| **Adverse Selection** | Our approval criteria attracts worst-risk consumers | Systemic |
| **Model Risk** | Credit model fails in new market conditions | Systemic |

### 2.3 Brazilian Credit Risk Specifics

**Bureau Landscape:**

| Bureau | Coverage | Data Quality | API |
|--------|----------|-------------|-----|
| Serasa Experian | ~200M CPFs | Excellent | REST |
| SPC Brasil | ~120M CPFs | Very Good | REST |
| Boa Vista SCPC | ~100M CPFs | Good | REST |
| Quod | ~90M CPFs | Good | REST |
| BCB SCR | ~130M CPFs | Excellent | via Bacen |

**Key challenges:**
- ~45M Brazilians have **thin or no bureau file** (invisible to traditional scoring)
- Bureau data can be **stale** — a consumer may have paid off debt that hasn't been updated
- **CPF fraud** (synthetic identity) is structurally high in Brazil
- Informal economy: **self-employed / MEI** have income that doesn't appear on formal records

### 2.4 Credit Risk Strategy

**Layer 1 — Hard Rules (Instant Rejection)**
- CPF with active judicial protest (protesto cartorial)
- CPF in Serasa Negativado with debt > R$500
- CPF with fraud flag in any bureau
- Age < 18 or unverifiable identity
- Phone number associated with fraud reports
- Transaction amount > approved limit

**Layer 2 — Scoring Model**

Inputs for credit scoring model:
```
Bureau features:
  - Score Serasa (0-1000)
  - Score SPC
  - # open debts (value, vintage)
  - Debt-to-income ratio (estimated)
  - Payment history (30/60/90 dpd in 12M)
  - # credit inquiries in 90 days (velocity)

Behavioral features:
  - Time since CPF first appeared in bureaus
  - # successful Pix transactions (via Open Finance)
  - Monthly income proxy (via Open Finance bank statements)
  - Employment indicators

Transaction features:
  - Purchase amount vs. approved limit ratio
  - Merchant category
  - Purchase time / day of week
  - Device age / app install date
  - Session behavioral signals

Network features:
  - Prior purchases on our platform
  - Payment history on our platform
  - # merchants used
  - Referral source
```

**Output:** Probability of Default (PD) score → maps to:
- Approve (PD < threshold_A)
- Manual Review (threshold_A ≤ PD < threshold_B)
- Deny (PD ≥ threshold_B)

**Layer 3 — Limit Setting**
- Not every approval is full limit
- Dynamic limit based on:
  - PD score
  - Income proxy
  - Purchase history on platform
  - Merchant risk tier

### 2.5 Credit Risk Thresholds & Targets

| Metric | Target | Alert | Critical |
|--------|--------|-------|---------|
| **NPL 30+ days** | < 3% | 4% | 5% |
| **NPL 90+ days** | < 1.5% | 2.5% | 3.5% |
| **Charge-off Rate** | < 2% | 3% | 4% |
| **Approval Rate** | 55–70% | < 50% | < 40% |
| **Expected Loss / GMV** | < 1.8% | 2.5% | 3.5% |

### 2.6 Portfolio Monitoring

**Daily monitoring:**
- DPD bucket roll rates (1→30, 30→60, 60→90)
- New approval rates by score band
- Vintage curves (cohort analysis)
- Early payment indicators

**Weekly:**
- Merchant-level NPL
- Geographic concentration
- Score model drift (PSI — Population Stability Index)
- KS statistic (model discrimination)

**Monthly:**
- Full portfolio stress test
- Model recalibration assessment
- Provisioning adequacy review

---

## 3. Fraud Risk

### 3.1 Fraud Taxonomy for BNPL

| Fraud Type | Description | Prevalence | Impact |
|-----------|-------------|-----------|--------|
| **First-Party Fraud** | Real person, no intention to pay | High in Brazil | High — no recovery |
| **Identity Theft** | Stolen CPF / biometric spoofing | Medium-High | High |
| **Synthetic Identity** | Fabricated CPF + data combination | Medium | High |
| **Account Takeover (ATO)** | Hacked account used to make purchases | Medium | Medium-High |
| **Device Spoofing** | Emulators, rooted devices, VPNs | High | Medium |
| **Velocity Abuse** | Multiple applications in short time | High | Medium |
| **Merchant Collusion** | Merchant + consumer conspire | Low | Very High |
| **Card-Not-Present Fraud** | Using intercepted Pix data | Low | Medium |

### 3.2 Brazilian Fraud Environment

**Key facts:**
- Brazil ranks among the **top 5 global markets for digital fraud**
- CPF can be obtained from data leaks (LGPD compliance issues with third parties)
- **130M+ CPFs were exposed** in a 2021 data leak (Ministério da Saúde incident)
- Burner devices and rooted phones are widely used by fraud rings
- Fraud rings operate organized pipelines: stolen CPF + selfie deepfake + VPN

### 3.3 Fraud Prevention Architecture

#### Layer 1 — Device Intelligence
```
Signals collected at SDK initialization:
  - Device fingerprint (hardware + software hash)
  - Root/jailbreak detection
  - Emulator detection
  - VPN/proxy detection
  - App tampering detection
  - GPS coordinates (real vs. GPS spoofing)
  - Screen reader / accessibility service detection
```

#### Layer 2 — Identity Verification (KYC)
```
Step 1: CPF Validation
  - Real-time query to Receita Federal via SERPRO/Datavalid
  - Name + date of birth cross-check
  - CPF status: active, suspended, cancelled

Step 2: Document OCR + Liveness
  - RG or CNH photo capture
  - OCR extraction → compare to CPF data
  - Liveness check (active liveness: smile, blink, turn head)
  - Passive liveness (frame-by-frame deepfake detection)
  - Provider: CAF, Unico, Idwall, or Jumio

Step 3: Facial Biometrics
  - Selfie vs. document photo match
  - Biometric score threshold
  - 3D depth check (anti-spoofing)

Step 4: Database Checks
  - Internal blacklist (own fraud database)
  - Bureau fraud flag queries
  - COAF/government sanctions lists
  - PEP (Politically Exposed Person) check
```

#### Layer 3 — Behavioral Biometrics
```
Session signals:
  - Typing speed and rhythm (CPF entry)
  - Swipe patterns
  - Time on screen
  - Copy-paste detection (no manual typing)
  - Form fill sequence
  - Session duration anomalies
```

#### Layer 4 — Velocity & Network Rules
```
Rules engine (real-time, < 50ms):
  - Same CPF: max 1 approval per 30 days (configurable)
  - Same device: max 3 accounts (configurable)
  - Same phone: max 2 accounts
  - Same IP: max 5 registrations/hour
  - Same bank account: max 1 account
  - Geolocation: IP vs. GPS > 500km → alert
  - Same address: max 3 CPFs (household rule)
```

#### Layer 5 — Transaction-Time Fraud (per purchase)
```
Per-transaction signals:
  - Time since account creation (new account fraud)
  - First purchase on new account → higher scrutiny
  - Merchant risk tier
  - Purchase amount vs. historical spend
  - Delivery address vs. registration address
  - Multiple failed attempts before success
  - Session replay anomalies
```

### 3.4 Fraud Metrics & Targets

| Metric | Target | Alert |
|--------|--------|-------|
| **Fraud Rate (% GMV)** | < 0.3% | 0.5% |
| **False Positive Rate** (legit declined) | < 3% | 5% |
| **ATO Rate** | < 0.01% | 0.05% |
| **KYC Pass Rate** | 75–85% | < 65% |
| **Fraud Review Queue** | < 500 cases/day | > 2,000 |

### 3.5 Fraud Response Playbook

| Trigger | Response |
|---------|----------|
| Fraud confirmed on account | Immediate freeze, block all pending transactions, notify consumer |
| High-confidence fraud signal | Hold transaction for manual review |
| Merchant fraud pattern | Freeze merchant API, alert team, investigate |
| Velocity spike > 3σ | Auto-block, page on-call |
| Bureau fraud flag | Hard deny, log for COAF |

---

## 4. Operational Risk

### 4.1 Technology Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Pix gateway downtime | Medium | Critical | Multi-provider redundancy (Celcoin + FitBank) |
| Database corruption | Low | Critical | Multi-AZ PostgreSQL, point-in-time recovery |
| Redis cache failure | Medium | High | Sentinel/Cluster, graceful degradation |
| Celery worker failure | Medium | Medium | Dead letter queues, retry policies |
| DDoS attack | Medium | High | WAF, rate limiting, CloudFlare |
| API credential leak | Low | Critical | Secret rotation, vault, audit logs |

### 4.2 Process Risks

| Risk | Mitigation |
|------|-----------|
| Manual review backlog | SLA monitoring, auto-escalation at 4h |
| Collection agent errors | Scripted workflows, mandatory checklists |
| Incorrect ledger entries | Double-entry validation, reconciliation jobs |
| Webhook delivery failure | Retry with exponential backoff, dead letter queue |

### 4.3 People Risks

| Risk | Mitigation |
|------|-----------|
| Insider fraud | RBAC, audit logs, segregation of duties |
| Key person dependency | Documentation, pair programming, knowledge transfer |
| Support overwhelm | AI-assisted triage, FAQ deflection |

---

## 5. Market Risk

### 5.1 Selic Rate Impact

Brazil's Selic rate (benchmark interest rate) directly affects:
- **Cost of funds** in FIDC structures (FIDC costs linked to CDI ≈ Selic)
- **Consumer delinquency** — higher rates = lower disposable income = more defaults
- **Merchant demand** — higher rates reduce merchant appetite for BNPL MDR costs

**Stress scenario:** Selic at 15%+ (current range: 10–13%)
- FIDC cost of funds increases ~2–3 percentage points
- Net margin per transaction decreases by ~1.5%
- Delinquency proxy models must be recalibrated

### 5.2 Inflation Risk

High inflation erodes consumer real income, increasing default probability on existing portfolio. Portfolio models must be adjusted with macroeconomic inputs (IPCA forecast, unemployment rate).

### 5.3 FX Risk (if USD-denominated funding)

If capital markets (FIDC senior tranches) are USD-denominated:
- BRL depreciation increases debt service cost
- Hedge through cross-currency swaps or structuring in BRL

---

## 6. Regulatory Risk

*(Full analysis in regulatory-analysis.md — summary here)*

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| BCB mandates interest rate cap on BNPL | Medium | High | Product diversification, lobby engagement |
| BCB requires banking license for BNPL scale | Low | Very High | Early SCD licensing |
| LGPD enforcement action | Medium | High | Privacy-by-design, DPO appointment |
| COAF reporting non-compliance | Low | Very High | Automated STR reporting |
| Pix Parcelado regulation creates new compliance burden | High | Medium | Monitor regulation, early compliance team |

---

## 7. Risk Governance Structure

### 7.1 Risk Committee

- **Chief Risk Officer (CRO)** — owns credit, fraud, and operational risk
- **Chief Compliance Officer (CCO)** — regulatory and LGPD compliance
- **Chief Financial Officer (CFO)** — market risk, liquidity risk
- **CTO** — technology risk

### 7.2 Risk Appetite Statement

> *"We will extend credit to consumers we believe can repay, at terms they can afford, maintaining a portfolio NPL below 3% and a fraud rate below 0.3% of GMV. We will not sacrifice credit quality for volume. We will not approve a transaction we cannot defend to a regulator."*

### 7.3 Model Governance

- All credit models require **validation** before deployment
- **Champion/Challenger** framework: new model challenges champion on 10% of traffic
- **Model Risk Committee** reviews all model changes
- **Backtesting** required: validate model on 6M+ of held-out data
- **Model documentation**: purpose, training data, features, performance, limitations

---

## 8. Risk Provisioning

**IFRS 9 / Local GAAP Provisioning Approach:**

| Days Past Due | Stage | Provision Rate |
|---------------|-------|---------------|
| 0 DPD (not impaired) | Stage 1 | 12-month ECL |
| 1–29 DPD | Stage 1 | 12-month ECL |
| 30–89 DPD | Stage 2 | Lifetime ECL |
| 90+ DPD | Stage 3 | Near-100% ECL |
| Written off | — | 100% |

**ECL = Exposure at Default × Probability of Default × Loss Given Default**

Given BNPL is unsecured: LGD = 85–100% (minimal recovery)

---

*Next: [Regulatory Analysis →](regulatory-analysis.md)*
