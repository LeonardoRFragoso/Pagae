# Regulatory Analysis — Brazilian BNPL Platform

> **Classification:** Internal — Legal & Compliance  
> **Date:** June 2026  
> **Version:** 1.0

> **Disclaimer:** This document is for internal planning purposes only and does not constitute legal advice. All regulatory interpretations must be validated by qualified Brazilian legal counsel and compliance specialists.

---

## 1. Regulatory Overview

Operating a BNPL platform in Brazil requires navigating a complex, multi-layered regulatory framework. Unlike unregulated BNPL markets (some EU countries pre-2023), **Brazil has a well-established financial regulation regime** with the Banco Central do Brasil (BCB) at its center.

### 1.1 Primary Regulators

| Regulator | Scope | Relevance to BNPL |
|-----------|-------|-------------------|
| **Banco Central do Brasil (BCB)** | Banking, payments, credit, Pix | Highest — licenses BNPL credit operations |
| **CVM** (Comissão de Valores Mobiliários) | Capital markets, securities | Relevant if FIDC is used for funding |
| **COAF** | Financial intelligence, AML | Mandatory SAR reporting |
| **ANPD** (Autoridade Nacional de Proteção de Dados) | Data protection (LGPD) | Mandatory — consumer data handling |
| **Receita Federal** | Tax, CPF registry | CPF validation, tax reporting |
| **SUSEP** (in some credit insurance contexts) | Insurance | If credit insurance is embedded |

---

## 2. Licensing Framework

### 2.1 Available Legal Entities for BNPL

**Option A: SCD — Sociedade de Crédito Direto (Recommended)**

Established by **Resolution CMN 4.656/2018**, the SCD is a financial institution specifically created for digital credit operations:

| Attribute | Detail |
|-----------|--------|
| Legal basis | Resolution CMN 4.656/2018, now CMN 5.058/2023 |
| Minimum capital | R$1 million |
| Permitted activities | Credit grants, purchase of credit rights, guarantees |
| Funding | May use own capital + FIDC (cannot take public deposits) |
| Credit assignment | Can sell credits to FIDCs and other financial institutions |
| Regulatory authority | BCB |

**Why SCD is the right choice for our platform:**
- Allows direct credit grant to consumers — BNPL's core operation
- Can integrate with FIDC for capital markets funding
- Partners with payment institutions for Pix collection
- Pagaleve operates as SCD — proven path

**Option B: Correspondente Bancário (Banking Correspondent)**
- Operates under a licensed bank's umbrella
- Lower compliance burden, faster to market
- **Trade-off:** revenue share with bank partner, less control over credit decisions
- Suitable for pre-license phase / pilot

**Option C: Partnership Model (Non-licensed)**
- Work with a licensed SCD or bank as the credit underwriter
- Platform operates as a technology/distribution layer
- Fastest path to market, but limits product ownership
- Use as interim strategy while SCD license is pending

### 2.2 Licensing Timeline (SCD)

```
Month 0:   Engage specialized banking law firm
Month 1-2: Corporate structure preparation, shareholders documentation
Month 2-3: Submit SCD application to BCB
Month 3-9: BCB review process (typically 6-12 months)
Month 9-12: BCB approval + operational authorization
Month 12+: Full SCD operations
```

**Recommendation:** Launch via banking correspondent / partner SCD in months 1–9 while SCD license is pending.

---

## 3. Pix Regulatory Framework

### 3.1 Pix Regulation Overview

Pix is regulated by **BCB Resolution 1/2020** and subsequent normative instructions. Key rules for BNPL:

- Only **Payment Institutions (IPs)** and **financial institutions** can hold Pix keys
- To send/receive Pix programmatically, entity must be a **Direct Pix Participant** or use an **Indirect Participant** (banking partner)
- **Pix collection** (receiving payments): accessible through indirect participation via banking partner (Celcoin, Dock, FitBank, etc.)
- **Pix QR Code generation**: standardized by BCB, requires certified implementation

### 3.2 Pix Parcelado (Pix in Installments)

As of June 2026, **Pix Parcelado** is still being regulated by BCB:
- BCB announced regulatory framework delayed beyond December 2025
- The modality already exists commercially (Pagaleve, banks) under existing credit law
- Pix Parcelado = a credit product where repayment is made via Pix (not a new Pix feature)
- When BCB finalizes rules, expect: standardized disclosure, rate caps for consumer-facing products, mandatory consent flows

**Our approach:** Build the credit product (BNPL) on existing legal basis (SCD credit grant), use Pix as the collection rail, and remain ready to comply with Pix Parcelado rules when published.

### 3.3 Pix API Integration Compliance

- Must use **EMVCo QR Code standard** for static and dynamic QR codes
- Dynamic Pix QR Codes (QRDN) must comply with BCB Resolution 87/2021
- **Immediate payment webhook**: BCB requires real-time payment notification
- QR Code expiry: BCB mandates maximum validity periods
- **Devolution rules**: BCB Resolution 59/2022 — mandatory refund within 90 days via Pix

---

## 4. Credit Regulation

### 4.1 Consumer Credit Law

- **Lei 8.078/1990 (Código de Defesa do Consumidor - CDC)**: All consumer-facing credit contracts subject to consumer protection rules
- **Lei 10.406/2002 (Código Civil)**: General contract law governs credit agreements
- **Lei 12.865/2013 + Resolution CMN 4.656/2018**: Framework for payment institutions and credit fintechs
- **Resolução CMN 4.292/2013**: Credit card installment rules (reference for "parcelado" regulation)

### 4.2 Mandatory Credit Contract Disclosures (CDC + BCB)

Every credit contract must include:
- Total amount of credit
- Total amount to be paid (CET — Custo Efetivo Total)
- **CET (Custo Efetivo Total)**: effective annual cost including all fees and interest — **mandatory disclosure** per BCB Resolution 3.517/2007
- Payment schedule (all installment amounts and due dates)
- Penalty for late payment (maximum: 2% of installment + 1% per month interest per CDC)
- Early repayment right (consumers can prepay — proportional interest reduction mandatory)
- 7-day cancellation right (CDC right of regret for remote contracts)

### 4.3 Interest Rate Regulation

- No legal usury cap in Brazil for credit operations (unlike consumer credit in some countries)
- **Exception:** Microfinance (Resolução CMN 3.422/2006) has caps
- BNPL at market rates is permitted, but CET must be clearly disclosed
- BCB monitors and publishes market interest rate benchmarks
- Political risk: legislative proposals to cap consumer credit rates exist but have not passed

### 4.4 SCR (Sistema de Informações de Crédito do Banco Central)

- All SCDs must report credit operations to BCB's SCR monthly
- SCR threshold: operations ≥ R$200 must be reported
- Consumers have the right to consult their own SCR data
- Non-compliance: BCB sanctions

---

## 5. KYC / AML Regulation

### 5.1 Legal Basis

| Regulation | Content |
|-----------|---------|
| **Lei 9.613/1998** (AML Law) | Core AML law — criminalizes money laundering, establishes reporting obligations |
| **BCB Circular 3.978/2020** (now Resolution BCB 119/2021) | BCB's operationalization of AML Law for financial institutions |
| **COAF Resolution 36/2021** | COAF reporting requirements |
| **BCB Resolution 55/2020** | Digital onboarding for financial institutions |

### 5.2 KYC Obligations

**Mandatory data collection for individuals (CPF holders):**

```
Required fields:
  - Full legal name (exactly as in CPF registry)
  - CPF number
  - Date of birth
  - Nationality
  - Full address (with proof)
  - Phone number
  - Email
  - Occupation / income source
  - Politically Exposed Person (PEP) status

Optional but strongly recommended:
  - Monthly income (self-declared + verified via Open Finance)
  - Bank account data
  - Employment status
```

**Document verification requirements:**
- Identity document (RG, CNH, or Passaporte)
- Proof of address (utility bill or bank statement < 90 days)
- Liveness check for digital onboarding (BCB Resolution 55/2020 permits biometric digital KYC)

### 5.3 Risk-Based Due Diligence (RBDD)

BCB Circular 3.978/2020 mandates a **risk-based approach**:

| Risk Level | Profile | Enhanced Due Diligence Required |
|-----------|---------|--------------------------------|
| Low | Standard consumer, low ticket | Standard KYC |
| Medium | Higher income, self-employed | Income verification |
| High | PEP, foreign national, high ticket | Enhanced — source of funds |
| Very High | Sanctions list, fraud flag | Deny or escalate |

### 5.4 Ongoing Monitoring Obligations

- Monitor transactions for suspicious patterns
- Update customer data when material changes occur
- **24-hour SAR filing to COAF** when suspicious activity detected
- Annual zero-activity report if no SAR filed

### 5.5 CPF Validation Process

```
Technical flow:
1. Consumer enters CPF at onboarding
2. Platform queries SERPRO/Datavalid API in real-time
3. Cross-checks: name, date of birth, CPF status
4. If CPF is suspended, cancelled, or name mismatch → reject
5. If valid → proceed to document OCR + liveness
6. Store validation result with timestamp (audit trail)
```

**Data providers:**
- **SERPRO/Datavalid** — direct government data (most authoritative)
- **Serasa Identity** — bureau-based CPF validation
- **CAF (Caf.io)** — full KYC suite including CPF + document + biometrics

---

## 6. LGPD (Lei Geral de Proteção de Dados)

**Law 13.709/2018** — Brazil's data protection law, effective September 2020.

### 6.1 Key LGPD Principles for BNPL

| Principle | Implication for BNPL |
|-----------|---------------------|
| **Finality** | Data collected for credit scoring cannot be repurposed for marketing without new consent |
| **Data Minimization** | Collect only what is necessary for the stated purpose |
| **Transparency** | Clear disclosure of what data is collected, how used, who shares |
| **Security** | Appropriate technical/organizational measures to protect data |
| **Non-Discrimination** | Credit decisions cannot use data that constitutes discrimination |
| **Accountability** | Must demonstrate compliance proactively |

### 6.2 Legal Bases for Data Processing in BNPL

| Processing Activity | Legal Basis |
|--------------------|-------------|
| KYC / identity verification | **Legitimate interest** + **Contract necessity** |
| Credit scoring | **Legitimate interest** (Art. 7, IX) + **Contract** (Art. 7, V) |
| Bureau data queries | **Legitimate interest** (credit assessment) |
| Marketing / offers | **Consent** (Art. 7, I) — separate, explicit |
| Fraud prevention | **Legitimate interest** (Art. 7, IX) |
| COAF reporting | **Legal obligation** (Art. 7, II) |
| Open Finance data | **Consent** (must be explicit, per-use) |

### 6.3 Mandatory LGPD Compliance Requirements

1. **Privacy Policy**: Clear, plain-language policy accessible before data collection
2. **DPO (Encarregado)**: Appoint a Data Protection Officer — mandatory for financial institutions
3. **Data Mapping (ROPA)**: Register of Processing Activities — document all data flows
4. **Data Subject Rights Portal**: Consumers can access, correct, delete, or port their data
5. **Data Breach Notification**: Notify ANPD and affected individuals within 72 hours if breach likely causes risk
6. **Impact Assessment (DPIA)**: Required for high-risk processing (credit scoring qualifies)
7. **Third-Party DPA**: Data Processing Agreements with all vendors who handle personal data
8. **Retention Policy**: Data must be deleted after purpose is fulfilled (except legal hold)

### 6.4 Sensitive Data

LGPD treats as "sensitive": biometric data, health data, political opinions, etc. For BNPL:
- **Biometric data** (facial recognition for KYC) requires **explicit consent**
- Store biometric templates encrypted, minimal retention period
- Do not use biometric data beyond KYC/anti-fraud purpose without new consent

### 6.5 Credit Scoring and LGPD

BCB Resolution 4.571/2017 (Credit Scoring) + LGPD:
- Consumers have the right to know their credit score
- They can request an explanation of automated credit decisions
- Cannot use race, religion, political opinion, gender as scoring inputs

### 6.6 Penalties

ANPD enforcement:
- Warnings
- Fines up to **R$50M per violation** or 2% of Brazil revenue (whichever is higher)
- Mandatory publication of the infraction (reputational damage)
- Prohibition on processing data

---

## 7. Open Finance (Open Banking)

BCB's Open Finance regulation (Resolutions 32–35/2020, Phase 4 ongoing):

### 7.1 What It Enables for BNPL

- **Phase 2+**: Institutions can, with consumer consent, access bank transaction data from other institutions
- Real income verification: 12 months of bank statements → income proxy without payslips
- Behavioral credit signals: spending patterns, savings rate, regular income deposits
- **Dramatically improves credit model quality for thin-file consumers**

### 7.2 Compliance Requirements

- Must be a **regulated entity** (SCD qualifies) to participate
- Consumer must give **explicit, informed consent** per transaction/purpose
- Consent can be revoked at any time
- Data must be used only for the consented purpose
- Access tokens expire (typically 12 months)

---

## 8. FIDC (Fundo de Investimento em Direitos Creditórios)

### 8.1 What Is a FIDC

A FIDC is a Brazilian investment fund that acquires credit rights (receivables). For BNPL, the platform originates credit → sells receivables to FIDC → FIDC provides capital.

### 8.2 FIDC Structure for BNPL

```
Platform (SCD) → originates BNPL credit → assigns receivables to FIDC
FIDC: 
  Senior tranches → sold to institutional investors (Verde Capital, etc.)
  Subordinated tranches → retained by SCD (credit risk retention ≥ 20% typically)
Investors receive FIDC senior quota returns (CDI + spread)
SCD uses FIDC capital to fund new originations
```

### 8.3 CVM Regulation

FIDCs are regulated by **CVM Resolução 175/2022** (replaces ICVM 356/2001):
- Must have a FIDC administrator (Administradora qualificada)
- Must have an independent custodian
- Must have independent auditor (if open to non-qualified investors)
- Regular reporting to CVM
- Eligibility criteria for credit rights must be defined in fund prospectus

### 8.4 SCD-FIDC Integration

Resolution 4.656/2018 explicitly allows SCD to:
- Sell credit rights to FIDCs
- Retain subordinated FIDC quotas
- Use FIDC resources for new originations

**Tax treatment:** FIDC income typically has favorable withholding tax rates for institutional investors.

---

## 9. Consumer Protection — PROCON & SENACON

- **PROCON** (state) and **SENACON** (federal) handle consumer complaints
- Respond to complaints within mandated timeframes (typically 5 business days)
- Failure to respond → escalation, potential fines, negative publicity
- High PROCON complaint volume → regulatory attention
- **Nota Minha** (BCB's complaint ranking): financial institutions ranked by complaint volume/quality of resolution

**Build from day 1:** customer support workflows that resolve complaints before PROCON escalation.

---

## 10. Compliance Roadmap

### Phase 1 — Launch (via partner SCD / banking correspondent)
- [x] LGPD compliance: privacy policy, consent management, DPO
- [x] KYC/AML: BCB Circular 3.978 — customer identification
- [x] COAF registration and SAR reporting capability
- [x] CDC: credit contract templates with mandatory disclosures
- [x] CET calculation and disclosure in all offers

### Phase 2 — Growth (SCD license pending)
- [ ] SCR reporting setup with BCB
- [ ] Open Finance participation (consume data)
- [ ] FIDC establishment with qualified administrator
- [ ] Audit trail and regulatory reporting infrastructure

### Phase 3 — Scale (Post-SCD license)
- [ ] Full BCB regulatory reporting (COSIF)
- [ ] Open Finance — offer data (full participation)
- [ ] Capital adequacy monitoring
- [ ] Stress testing per BCB requirements

---

## 11. Key Regulatory Contacts & Resources

| Resource | URL |
|----------|-----|
| BCB Fintech Ecosystem | bcb.gov.br/en/financialstability/fintechs_en |
| BCB Regulatory Sandbox | bcb.gov.br/sandbox |
| BCB Resolution 4.656/2018 | bcb.gov.br (CMN Resolution 4.656) |
| ANPD | gov.br/anpd |
| COAF | gov.br/coaf |
| Open Finance Brasil | openfinancebrasil.org.br |
| SERPRO/Datavalid | datavalid.estaleiro.serpro.gov.br |

---

*Next: [Architecture Proposal →](architecture-proposal.md)*
