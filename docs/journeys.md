# User, Merchant, Credit & Collection Journeys

> **Classification:** Internal — Product & Engineering  
> **Date:** June 2026  
> **Version:** 1.0

---

## 1. Consumer Journeys

### 1.1 Journey A — New Consumer First Purchase (E-commerce)

```
TOUCHPOINT: Merchant checkout page
─────────────────────────────────────────────────────────────────────

STEP 1: Payment Method Selection
  Consumer sees: [Credit Card] [Pix à vista] [Pagaê — 4x sem juros no Pix]
  Consumer selects: Pagaê
  
  System: Merchant's page loads Pagaê checkout SDK

STEP 2: Consumer Identification
  Consumer sees: "Qual é o seu CPF?"
  Consumer enters: CPF
  
  System (< 100ms):
    - Validate CPF format
    - Check if consumer exists in our database
    - If new → begin KYC flow
    - If existing + KYC approved → skip to Step 5

STEP 3: Phone & OTP Verification (New Consumer)
  Consumer sees: "Qual é o seu número de celular?"
  Consumer enters: +55 11 99999-9999
  
  System: Send OTP via SMS (fallback: WhatsApp)
  Consumer enters OTP → verified

STEP 4: KYC Flow (New Consumer, First Time Only)
  
  4a. Basic Data
    Consumer sees: Form with name, date of birth, email
    Consumer fills: Full name, DOB, email
    
    System (background):
      - Query Receita Federal (SERPRO) to validate CPF + name + DOB
      - If mismatch → friendly error: "Verifique seus dados"
      - If validated → proceed
  
  4b. Document Capture
    Consumer sees: "Agora precisamos do seu documento"
    Consumer selects: [RG] [CNH] [Passaporte]
    Consumer photographs: front + back
    
    System (< 3s):
      - OCR document → extract name, DOB, document number
      - Cross-check with CPF registry data
      - Document authenticity check
  
  4c. Selfie + Liveness
    Consumer sees: Camera activation with animated guide
    Consumer performs: Smile (active liveness)
    
    System (< 2s):
      - Liveness detection (anti-spoofing)
      - Facial match: selfie vs. document photo
      - Score threshold check
  
  4d. Address
    Consumer sees: "Qual é o seu endereço?"
    Consumer fills: CEP (auto-fills street/city via ViaCEP), number, complement
  
  System (after KYC complete):
    - KYC result: APPROVED / PENDING / REJECTED
    - If APPROVED → proceed to credit decision (Step 5)
    - If PENDING → email consumer, show "Estamos analisando seu cadastro"
    - If REJECTED → show reason codes without exposing model details

STEP 5: Credit Decision
  Consumer sees: "Processando..." (loading screen, max 3s visible)
  
  System (< 500ms total):
    - Risk engine: device score, velocity check, IP check
    - Credit engine: bureau query, internal model, Open Finance (if available)
    - Policy evaluation
    - Limit assignment
  
  OUTCOME A — APPROVED:
    Consumer sees: 
      "Aprovado! ✅
       Parcelamos R$450,00 em 4x de R$112,50
       Sem juros, sem cartão, só no Pix"
    
    Consumer sees: Payment schedule
      | # | Valor    | Vencimento   |
      |---|----------|--------------|
      | 1 | R$112,50 | 23/06/2026   |  ← today + 0 days (1st pix due now)
      | 2 | R$112,50 | 07/07/2026   |  ← + 14 days
      | 3 | R$112,50 | 21/07/2026   |  ← + 28 days
      | 4 | R$112,50 | 04/08/2026   |  ← + 42 days
    
    Consumer taps: [Confirmar e pagar 1ª parcela]
  
  OUTCOME B — DENIED:
    Consumer sees:
      "Não foi possível aprovar sua compra agora.
       Você pode tentar novamente em 30 dias."
    (No reason details — regulatory requirement for fairness)

STEP 6: First Installment Payment
  Consumer sees: Pix QR Code (dynamic QR, 15-min expiry)
    + Copy-paste Pix code
  
  Consumer opens: Banking app
  Consumer pays: Pix QR code
  
  System (< 3s after payment):
    - Receives Pix webhook from provider
    - Marks installment 1 as PAID
    - Triggers merchant settlement (async)
    - Sends confirmation to consumer: WhatsApp + email
    - Redirects consumer to merchant's success page
  
  Consumer sees (merchant page): Order confirmed ✅

STEP 7: Order Fulfillment
  Merchant: ships product (Pagaê has no role here)
  Consumer: receives product

─────────────────────────────────────────────────────────────────────
TOTAL TIME TO FIRST APPROVAL (new consumer): 3–5 minutes
TOTAL TIME TO FIRST APPROVAL (returning consumer, KYC approved): < 30 seconds
```

---

### 1.2 Journey B — Returning Consumer (Fast Checkout)

```
Consumer at merchant checkout selects Pagaê
  → Enters CPF
  → System recognizes returning consumer with valid KYC + credit limit
  → Instant credit re-evaluation (bureau not re-queried if < 7 days)
  → Shows approval + payment schedule
  → Consumer confirms with OTP or biometric
  → Pix QR code displayed
  → Consumer pays
  → Done in < 30 seconds
```

---

### 1.3 Journey C — Consumer App (Ongoing Management)

**Login:**
```
Consumer opens Pagaê app
  → Enters CPF → OTP → Biometric (Touch/Face ID on repeat logins)
```

**Home Screen:**
```
Dashboard shows:
  - Available limit: R$1,200 (progress bar showing used vs. available)
  - Next payment due: R$112,50 in 3 days
  - Quick pay button for upcoming installment
  - Recent purchases (last 3)
```

**My Installments:**
```
Grouped by purchase:
  Purchase: Tênis Nike Air Max — Magazine Luiza — R$450,00
    [1/4] R$112,50 — Pago ✅ 23/06/2026
    [2/4] R$112,50 — Vence 07/07/2026 [Pagar agora]
    [3/4] R$112,50 — Vence 21/07/2026
    [4/4] R$112,50 — Vence 04/08/2026
```

**Early Repayment:**
```
Consumer taps: "Antecipar parcelas"
  → Sees total due if paid today (with any applicable discount)
  → Confirms → Pix QR code for remaining balance
```

**Statement:**
```
Monthly extract showing:
  - All purchases
  - All installments paid
  - All upcoming installments
  - Download PDF option
```

---

### 1.4 Journey D — Overdue Consumer

```
DAY 1 (due date):
  Celery job at 08:00: installment DPD = 1
  → WhatsApp message: "Oi João! Sua parcela de R$112,50 venceu hoje. 
     Pague agora para manter seu limite: [link com QR code]"

DAY 3 (DPD = 3):
  → Email: "Parcela em atraso — evite negativação"
  → WhatsApp follow-up

DAY 7 (DPD = 7):
  → Credit limit suspended (new purchases blocked)
  → WhatsApp: "Seu limite foi suspenso. Regularize para reativar."
  → Assign to collection agent queue

DAY 15 (DPD = 15):
  → Collection agent calls consumer
  → Offers: payment plan, extension, partial settlement
  → Agent logs outcome in system

DAY 30 (DPD = 30):
  → If not resolved: escalate to external collection partner
  → Bureau negative reporting (Serasa/SPC negativado)

DAY 90 (DPD = 90):
  → Write-off provision (100% ECL)
  → Legal collection possible for amounts > R$500

RESOLUTION (any day):
  → Consumer pays via new Pix QR code
  → Installment marked PAID
  → If all installments paid: limit restored
  → Bureau update: debt settled (within 5 business days)
```

---

## 2. Merchant Journeys

### 2.1 Journey A — Merchant Onboarding

```
CHANNEL: Pagaê website / sales team referral

STEP 1: Interest Registration
  Merchant fills: Company name, CNPJ, website, monthly GMV estimate, contact
  System: Creates lead in CRM, triggers sales/onboarding flow

STEP 2: KYB (Know Your Business) Verification
  Merchant submits:
    - CNPJ (auto-validates via Receita Federal)
    - Contrato Social / última alteração
    - Sócios / QSA (Quadro Societário) — validated against BCB QSA database
    - Bank account (CNPJ-linked)
    - Legal representative documents (CPF + KYC of each partner with > 25% stake)
  
  System:
    - BCB QSA check: validates beneficial ownership
    - PEP check on all partners
    - Fraud history check
    - Financial health check (optional: CNPJ credit bureau — Serasa Empresas)
  
  Result: Approved / Pending Manual Review / Rejected
  Timeline: Automated < 1 hour; manual review < 24 hours

STEP 3: Commercial Agreement
  Merchant reviews: MDR schedule, settlement terms, webhook requirements
  Merchant signs: Digital contract (DocuSign / Clicksign)

STEP 4: Technical Integration
  Merchant receives:
    - API Key (production)
    - API Key (sandbox)
    - Webhook secret
    - Integration guide link
    - Test credentials
  
  Integration options:
    A. Direct API — backend POST requests to /checkout/create
    B. JavaScript SDK — drop-in UI component (iframe)
    C. E-commerce plugins — WooCommerce, Shopify, VTEX, Magento, Nuvemshop
  
  Merchant tests in sandbox:
    - Simulate approved checkout
    - Simulate denied checkout
    - Receive test webhook
    - Confirm settlement simulation

STEP 5: Go-Live
  Merchant: switches to production API key
  Pagaê: monitors first 48h of production traffic
  System: sends welcome email with support contacts
```

---

### 2.2 Journey B — Daily Merchant Operations

**Merchant Portal Dashboard:**
```
Today's Summary:
  GMV processed: R$45,230
  Transactions: 87 (72 approved, 15 denied)
  Approval rate: 82.8%
  Pending settlement: R$38,445.00

Settlement Schedule:
  [Settlement #142] R$38,445.00 — Previsto: 23/06/2026 às 14:00
  [Settlement #141] R$32,100.00 — Pago ✅ 22/06/2026
```

**Transaction Management:**
```
Search transactions by: order_id, CPF last4, date range, status

Transaction detail:
  Order: #ORD-00342
  Customer: João S. (CPF: ***.***.***-34)
  Amount: R$450.00
  Installments: 4x R$112.50
  Status: ACTIVE (2/4 paid)
  Approved at: 22/06/2026 14:32
  Webhook delivered: ✅
  
  [Refund] button (if within refund window)
```

**Webhook Management:**
```
Merchant configures:
  - Webhook URL
  - Events to receive: checkout.completed, checkout.denied, refund.completed
  - Test delivery button
  - Delivery log (last 100 deliveries with response codes)
```

---

### 2.3 Journey C — Refund Process

```
Merchant initiates refund via API or portal:
  POST /api/v1/refunds
  {
    "checkout_id": "chk_01HV...",
    "amount": 45000,  // R$450.00 in centavos — full refund
    "reason": "customer_request"
  }

System validates:
  - Checkout exists and belongs to merchant
  - Refund window: within 90 days (BCB Pix devolution rule)
  - Amount ≤ total checkout amount
  - Not already refunded

System processes refund:
  - Cancel all PENDING installments (future ones not yet due)
  - For PAID installments: initiate Pix devolution to consumer
  - Adjust MDR: merchant pays back proportional MDR if full refund
  - Ledger entries: reverse original journal entries
  - Notify consumer: "Seu reembolso de R$450,00 foi processado"
  - Notify merchant: webhook event refund.completed

Pix devolution timeline: < 1 business day (BCB requirement for devoluções)
```

---

## 3. Credit Journey

### 3.1 Credit Onboarding — Limit Assignment

```
Trigger: Consumer completes KYC for first time

System: CreditEngine.initial_limit_assessment(customer_id)

INPUTS:
  Bureau: Serasa Score, SPC data, open debts, negative history
  Identity: Age, CPF vintage (how long registered)
  Open Finance (if authorized): Income proxy, spending patterns
  Risk: Device score, registration signals

PROCESSING:
  1. Policy: Hard rules (minimum bureau score, age ≥ 18, no active fraud flag)
  2. Score model: ensemble prediction → initial_pd (probability of default)
  3. Limit formula:
       base_limit = f(income_proxy, pd_score, product)
       adjusted_limit = base_limit × risk_multiplier
       final_limit = min(adjusted_limit, MAX_INITIAL_LIMIT)
  
  Where:
    MAX_INITIAL_LIMIT = R$1,000 (configurable per risk appetite)
    risk_multiplier:
      pd < 0.05  → 1.0  (excellent)
      pd < 0.10  → 0.75 (good)
      pd < 0.20  → 0.50 (fair)
      pd ≥ 0.20  → DENY (above appetite)

OUTPUT:
  CreditLimit: approved_limit, available_limit, risk_tier, next_review_date
  
LIMIT STORAGE:
  approved_limit  → maximum credit line
  available_limit → approved_limit - sum(active_installment_balances)
  
EXAMPLE:
  Customer A: Serasa 620, no debts, income R$3,000/month
    → Limit: R$800
  
  Customer B: Serasa 480, one debt R$200, 3 years CPF vintage
    → Deny (below minimum score threshold)
  
  Customer C: No bureau data (thin file), Open Finance shows R$5,000/month income
    → Limit: R$500 (conservative for thin-file)
```

---

### 3.2 Credit Decision — Per Transaction

```
Trigger: Consumer initiates checkout (POST /checkout/create)

INPUT:
  checkout_request: {cpf, amount, merchant_id, device_fingerprint, session_data}

PIPELINE:

[0ms] Request received

[0-30ms] LAYER 1: Hard Rules (synchronous, no I/O)
  - CPF format valid
  - Customer KYC = APPROVED
  - Customer not blocked/frozen
  - Amount > 0 and ≤ customer.available_limit
  - Merchant is active and in good standing
  
  → FAIL: immediate DENY (no scoring needed)
  → PASS: proceed

[30-80ms] LAYER 2: Risk Score (parallel I/O)
  - Device fingerprint check vs. blacklist
  - Velocity check (Redis: how many applications in last 1h, 24h, 7d)
  - IP reputation check
  
  → HIGH RISK: DENY or MANUAL REVIEW
  → LOW RISK: proceed

[80-450ms] LAYER 3: Credit Score (parallel I/O)
  Parallel queries:
    - Serasa Score API (< 200ms SLA)
    - Internal model: fetch customer features from DB
    - Open Finance: read cached analysis (if authorized, cached 24h)
  
  Merge: weighted ensemble of scores
  Apply: credit policy rules
  
[450-480ms] LAYER 4: Decision & Limit Calculation
  - If approved: calculate exact installment options
    4x biweekly: amount/4 per installment
    12x monthly: amount/12 + interest (if applicable)
  - Reserve credit (subtract from available_limit atomically)
  - Create CheckoutSession (status=APPROVED)
  - Generate payment schedule (4 or 12 PixCharges)
  - Record CreditDecision (all inputs + output + reasoning)

[480-500ms] Response returned to merchant/consumer

DECISION RECORD (immutable, for audit):
{
  "decision_id": "dec_01HV...",
  "customer_id": "cus_01HV...",
  "checkout_id": "chk_01HV...",
  "decision": "APPROVED",
  "approved_amount": 45000,
  "model_version": "credit_v2.3.1",
  "scores": {
    "serasa": 680,
    "internal": 720,
    "risk": 850
  },
  "rules_triggered": [],
  "created_at": "2026-06-16T18:00:00Z"
}
```

---

### 3.3 Credit Limit Review — Lifecycle

```
TRIGGER: Scheduled monthly review OR manual trigger

CASES:

CASE A — Good Payer (automatic upgrade):
  Condition: 3+ purchases, 0 DPD in 6 months, no fraud
  Action: Increase limit by 20-30% (up to max)
  Notification: "Seu limite foi aumentado para R$1,200! 🎉"

CASE B — Deteriorating Signal:
  Condition: New negative in bureau OR first DPD in last 30 days
  Action: Reduce available limit by 50%
  Block: New approvals until review resolved
  
CASE C — Open Finance Update:
  Condition: Consumer re-authorizes Open Finance with new institution
  Action: Re-run income analysis → adjust limit if significant change

CASE D — Forced Review (manual):
  Trigger: Fraud suspicion, large transaction, merchant complaint
  Action: Freeze account → ops team manual review queue
  SLA: 4 hours for review decision
```

---

## 4. Collection Journey

### 4.1 Collection Workflow — Full Lifecycle

```
                    INSTALLMENT DUE DATE
                           │
                    ┌──────▼──────┐
                    │  DPD = 0    │ ← paid on time → done ✅
                    └──────┬──────┘
                   (not paid)
                           │
    ┌──────────────────────▼──────────────────────┐
    │                  DPD 1-3                     │
    │  CHANNEL: WhatsApp (primary) + push notif    │
    │                                              │
    │  Message: "Oi [Nome]! Sua parcela de         │
    │  R$112,50 do seu pedido na [Merchant]         │
    │  venceu. Pague agora e mantenha seu           │
    │  limite ativo: [link QR code]"               │
    │                                              │
    │  System: Generate new payment link (24h TTL) │
    └──────────────────────┬──────────────────────┘
                   (still not paid)
                           │
    ┌──────────────────────▼──────────────────────┐
    │                  DPD 4-7                     │
    │  CHANNEL: Email + WhatsApp (sequence)        │
    │                                              │
    │  Day 4: Email with payment options           │
    │  Day 6: WhatsApp + offer: "Pague hoje e      │
    │          evite cobranças adicionais"          │
    │                                              │
    │  System: Suspend new purchase approvals      │
    └──────────────────────┬──────────────────────┘
                   (still not paid)
                           │
    ┌──────────────────────▼──────────────────────┐
    │                 DPD 8-14                     │
    │  CHANNEL: Assign to collection agent         │
    │                                              │
    │  Agent sees in queue:                        │
    │    Customer: João Silva                      │
    │    Amount owed: R$337.50 (3 installments)    │
    │    Contact: +55 11 99999-9999               │
    │    Priority: Medium                          │
    │                                              │
    │  Agent actions:                              │
    │    - Phone call (scripted workflow)          │
    │    - Offer payment plan extension            │
    │    - Record outcome: paid/promise/refused    │
    └──────────────────────┬──────────────────────┘
                   (still not paid)
                           │
    ┌──────────────────────▼──────────────────────┐
    │                DPD 15-29                     │
    │  CHANNEL: Escalated agent + legal warning    │
    │                                              │
    │  Actions:                                    │
    │    - Second agent attempt                    │
    │    - Offer settlement discount (if approved  │
    │      by risk team): e.g., pay 80% to settle  │
    │    - Send formal "notificação extrajudicial" │
    │    - Freeze ALL pending installments         │
    └──────────────────────┬──────────────────────┘
                   (still not paid)
                           │
    ┌──────────────────────▼──────────────────────┐
    │                 DPD 30-89                    │
    │  CHANNEL: External collection partner        │
    │                                              │
    │  Actions:                                    │
    │    - Assign to external agency via API       │
    │    - Bureau negative reporting:              │
    │      Serasa/SPC negativado                   │
    │    - Customer limit: permanently blocked     │
    │      until full repayment + 6 months         │
    └──────────────────────┬──────────────────────┘
                   (still not paid)
                           │
    ┌──────────────────────▼──────────────────────┐
    │                  DPD 90+                     │
    │  STATUS: Write-off                           │
    │                                              │
    │  Actions:                                    │
    │    - 100% ECL provision recorded             │
    │    - Charge-off booked in ledger             │
    │    - Consider legal action (> R$500)         │
    │    - Sale to debt purchaser (if applicable)  │
    └─────────────────────────────────────────────┘

RESOLUTION AT ANY STAGE:
    Customer pays → all pending installments cleared
    → Credit limit consideration: reinstated after 60 days clean
    → Bureau: update "dívida quitada" within 5 business days
    → Notification: "Parabéns! Sua dívida foi quitada ✅"
```

---

### 4.2 Collection Metrics Dashboard (Internal)

```
Daily operations view:

  DPD Bucket Summary:
    DPD 1-3:   R$45,000 (230 installments) — 78% self-cure expected
    DPD 4-7:   R$28,000 (142 installments) — 55% self-cure expected
    DPD 8-14:  R$18,000 (91 installments)  — In agent queue
    DPD 15-29: R$12,000 (60 installments)  — Escalated
    DPD 30-89: R$8,000  (40 installments)  — External
    DPD 90+:   R$5,000  (25 installments)  — Write-off

  Agent Performance:
    Agent A: 12 cases / 8 resolved / R$4,200 collected
    Agent B: 15 cases / 11 resolved / R$5,800 collected

  Self-Cure Rate (last 30 days):
    DPD 1-3: 82% (target: 75%) ✅
    DPD 4-7: 58% (target: 50%) ✅
    DPD 8-14: 35% (target: 40%) ⚠️

  Collection Effectiveness:
    Total portfolio NPL: 2.1% (target: < 3%) ✅
```

---

### 4.3 Escalation Rules Engine

```python
# Collection rules configuration (stored in DB, configurable without deploy)

COLLECTION_RULES = [
    {
        "name": "first_reminder",
        "trigger": {"dpd_gte": 1, "dpd_lte": 1},
        "action": "send_whatsapp",
        "template": "overdue_day_1",
        "priority": 1
    },
    {
        "name": "suspend_limit",
        "trigger": {"dpd_gte": 7},
        "action": "suspend_credit_limit",
        "reversible": True,
        "priority": 5
    },
    {
        "name": "assign_agent",
        "trigger": {"dpd_gte": 8, "dpd_lte": 14, "amount_gte": 10000},
        "action": "create_collection_case",
        "priority": 10
    },
    {
        "name": "bureau_negative",
        "trigger": {"dpd_gte": 30},
        "action": "report_to_bureau",
        "priority": 20
    },
    {
        "name": "write_off",
        "trigger": {"dpd_gte": 90},
        "action": "write_off_installment",
        "requires_approval": True,
        "priority": 100
    }
]
```

---

## 5. Internal Operations Journey

### 5.1 Manual Credit Review

```
TRIGGER: Credit decision = MANUAL_REVIEW

Queue item visible to: ops_supervisor, risk_analyst

Agent sees:
  Customer: João Silva
  CPF: ***.***.***-34
  Requested: R$800.00 (4x R$200)
  Merchant: Nike Store
  
  Signals (why manual):
    - Serasa score: 512 (borderline)
    - 1 open debt: R$180 (12 months old)
    - Device: new device + VPN detected
    - First time at this merchant
  
  KYC: APPROVED
  Bureau data: [expanded view with consent]
  
  Decision options:
    [Approve R$800] [Approve R$400] [Deny] [Request more info]
  
  Agent clicks: [Approve R$400] + types reason
  System: CreditDecision updated, consumer notified, checkout proceeds

SLA: < 4 hours (business hours), < 8 hours (nights/weekends)
```

---

### 5.2 Merchant Settlement Journey

```
TRIGGER: Celery Beat — daily at 14:00 BRT

SettlementService.process_pending()

  For each merchant:
    1. Query all CONFIRMED checkouts from yesterday
       (checkout where first installment paid = yesterday)
    2. Calculate settlement amount:
       settlement = sum(checkout_amounts) - sum(MDR_fees)
    3. Initiate Pix transfer to merchant's bank account
       via PaymentProvider.transfer(amount, merchant_bank_account)
    4. Create Settlement record
    5. Create Ledger entries:
       Dr  2010  Merchant Payable    R$X
         Cr  1010  Cash (Pix)           R$X
    6. Send Settlement notification to merchant
       Email: "Seu pagamento de R$X foi enviado"
       Portal: Settlement report downloadable as CSV/PDF

SETTLEMENT SLA: T+1 business day (day after checkout)
  (can be T+0 for premium merchant tier — future product)
```

---

*End of Phase 0 Discovery Documents*  
*Awaiting approval to proceed to Phase 1 — System Architecture & Implementation*
