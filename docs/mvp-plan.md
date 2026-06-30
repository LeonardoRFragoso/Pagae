# MVP Plan — Bootstrap BNPL Platform

> **Mode:** Solo Founder / Bootstrap  
> **Budget:** ≤ R$50.000  
> **Timeline:** 90 days to launch  
> **Date:** June 2026

---

## Reality Check First

Without SCD + FIDC, you cannot be the credit principal from day one.
The model shifts: **you are the technology + distribution layer; a licensed partner SCD is the credit principal.**

This is legal, proven, and used by dozens of Brazilian fintechs today (correspondente bancário model under Resolution CMN 4.656/2018).

Revenue impact: you keep ~3–4% MDR, partner SCD keeps ~3–4%. Total MDR to merchant stays 7%.
Upside: zero capital required for receivables. You build the tech, they fund the credit.

When you reach R$500k+ GMV/month, raise a seed round, get your own SCD license and FIDC, and capture the full MDR. That's Phase 2.

---

## 1. MVP Architecture

### 1.1 Deployment Topology

```
                  Internet
                     │
             ┌───────▼────────┐
             │  Cloudflare     │  ← CDN + WAF (free tier)
             │  (DNS + proxy)  │
             └───────┬────────┘
                     │
             ┌───────▼────────┐
             │   VPS Ubuntu   │  ← DigitalOcean Droplet $48/mo
             │   4 vCPU 8GB   │  (or AWS EC2 t3.medium)
             │                │
             │  ┌──────────┐  │
             │  │  Nginx   │  │  ← Reverse proxy + SSL (Let's Encrypt)
             │  └────┬─────┘  │
             │       │        │
             │  ┌────▼─────┐  │
             │  │  Gunicorn │  │  ← Django WSGI (4 workers)
             │  │  (Django) │  │
             │  └────┬─────┘  │
             │       │        │
             │  ┌────▼─────┐  │
             │  │  Celery  │  │  ← Async tasks (collections, notifs)
             │  │  Worker  │  │
             │  └──────────┘  │
             └───────┬────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
 ┌──────▼───┐ ┌──────▼───┐ ┌─────▼────┐
 │PostgreSQL│ │  Redis   │ │   S3     │
 │(managed) │ │(managed) │ │(documents│
 │ DO $15/mo│ │ DO $7/mo │ │  free*) │
 └──────────┘ └──────────┘ └──────────┘

External APIs:
  Celcoin  → Pix QR code + payment webhook
  CAF.io   → CPF validation + document OCR + liveness
  Serasa   → Credit score + negativado check
  Brevo    → Email (free up to 300/day)
  Z-API    → WhatsApp Business (R$69/month)
```

### 1.2 Application Architecture

Single Django monolith. No microservices. No Kubernetes.

```
pagae/
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
├── apps/
│   ├── accounts/       # Auth, JWT, users
│   ├── customers/      # Consumer profile, KYC, limit
│   ├── merchants/      # Merchant profile, API keys, webhooks
│   ├── checkout/       # Purchase flow + credit decision
│   ├── payments/       # Pix + installments + settlement
│   └── collections/    # Overdue + reminders
├── integrations/
│   ├── celcoin.py      # Pix QR, payment webhook
│   ├── serasa.py       # Score + negativado
│   └── caf.py          # KYC (CPF + document + selfie)
├── frontend/
│   ├── merchant/       # Merchant portal (Vue 3)
│   └── customer/       # Consumer portal (Vue 3)
└── templates/
    └── admin/          # Extended Django admin
```

### 1.3 Credit Model (Rule-Based, No ML)

```python
# checkout/credit.py — the entire credit engine in ~60 lines

LIMITS_BY_SCORE = [
    (700, 50000),   # score >= 700 → R$500 limit
    (600, 30000),   # score >= 600 → R$300
    (500, 15000),   # score >= 500 → R$150
    (  0,     0),   # below 500   → DENY
]

def decide(cpf: str, amount_cents: int) -> CreditDecision:
    # 1. Internal blacklist (our own fraud/default history)
    if Blacklist.objects.filter(cpf=cpf).exists():
        return CreditDecision(result="DENY", reason="blacklist")

    # 2. Velocity — Redis
    key = f"credit:velocity:{cpf}"
    applications_today = redis.incr(key)
    redis.expire(key, 86400)
    if applications_today > 2:
        return CreditDecision(result="DENY", reason="velocity")

    # 3. Serasa negativado (active debt)
    bureau = SerasaClient().check(cpf)
    if bureau.has_active_negative:
        return CreditDecision(result="DENY", reason="negativado")

    # 4. Score-based limit
    approved_limit = next(
        (limit for score, limit in LIMITS_BY_SCORE if bureau.score >= score), 0
    )
    if approved_limit == 0:
        return CreditDecision(result="DENY", reason="low_score")

    # 5. Amount check
    if amount_cents > approved_limit:
        return CreditDecision(result="DENY", reason="exceeds_limit")

    return CreditDecision(
        result="APPROVE",
        approved_amount=amount_cents,
        installment_plan=build_schedule(amount_cents)
    )
```

### 1.4 Pix + Payment Flow

```
Merchant → POST /api/v1/checkout/create
               │
               ├── Credit decision (< 500ms)
               │
               ├── [APPROVED] → Celcoin.create_qr_code(installment_1)
               │
               └── Return: { status, qr_code, pix_code, schedule }

Consumer pays QR code in any bank app
               │
               ▼
Celcoin sends webhook → POST /api/v1/webhooks/celcoin/pix
               │
               ├── Validate webhook signature
               ├── Mark installment as PAID
               ├── If installment_1 → trigger merchant settlement
               ├── Create ledger entry
               └── Send WhatsApp confirmation to consumer
```

---

## 2. Database Schema

12 tables. No over-engineering.

```sql
-- ─────────────────────────────────────────
-- USERS & AUTH
-- ─────────────────────────────────────────

CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) UNIQUE NOT NULL,
    phone       VARCHAR(20),
    password    VARCHAR(255) NOT NULL,
    role        VARCHAR(30) NOT NULL DEFAULT 'customer',
                -- customer | merchant_owner | ops | admin
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- CUSTOMERS (Consumers)
-- ─────────────────────────────────────────

CREATE TABLE customers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    cpf             VARCHAR(14) UNIQUE NOT NULL,  -- stored encrypted
    full_name       VARCHAR(255) NOT NULL,
    birth_date      DATE NOT NULL,
    phone           VARCHAR(20) NOT NULL,
    email           VARCHAR(255) NOT NULL,

    -- Address
    cep             VARCHAR(9),
    street          VARCHAR(255),
    number          VARCHAR(20),
    complement      VARCHAR(100),
    neighborhood    VARCHAR(100),
    city            VARCHAR(100),
    state           CHAR(2),

    -- KYC
    kyc_status      VARCHAR(20) DEFAULT 'pending',
                    -- pending | approved | rejected | manual_review
    kyc_provider_id VARCHAR(100),  -- CAF reference ID
    kyc_approved_at TIMESTAMPTZ,

    -- Credit
    serasa_score    SMALLINT,
    risk_tier       VARCHAR(10) DEFAULT 'new',
                    -- new | low | medium | high
    approved_limit  INTEGER DEFAULT 0,   -- centavos
    used_limit      INTEGER DEFAULT 0,   -- centavos
    is_blocked      BOOLEAN DEFAULT FALSE,
    blocked_reason  VARCHAR(100),

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_customers_cpf ON customers(cpf);

-- ─────────────────────────────────────────
-- MERCHANTS
-- ─────────────────────────────────────────

CREATE TABLE merchants (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    legal_name      VARCHAR(255) NOT NULL,
    trade_name      VARCHAR(255),
    cnpj            VARCHAR(18) UNIQUE NOT NULL,
    email           VARCHAR(255) NOT NULL,
    phone           VARCHAR(20),
    website         VARCHAR(255),

    -- Bank account for settlement
    bank_code       VARCHAR(10),
    bank_agency     VARCHAR(10),
    bank_account    VARCHAR(20),
    bank_account_type VARCHAR(10),  -- checking | savings
    pix_key         VARCHAR(255),   -- preferred settlement via Pix key

    -- Commercial
    mdr_rate        NUMERIC(5,4) DEFAULT 0.0700,  -- 7%
    settlement_days SMALLINT DEFAULT 1,            -- D+1

    -- Status
    status          VARCHAR(20) DEFAULT 'pending',
                    -- pending | active | suspended | terminated
    approved_at     TIMESTAMPTZ,

    -- Webhook
    webhook_url     VARCHAR(500),
    webhook_secret  VARCHAR(64),

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE merchant_api_keys (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id UUID REFERENCES merchants(id),
    key_prefix  VARCHAR(8) NOT NULL,   -- shown in UI: "pk_live_abc1"
    key_hash    VARCHAR(255) NOT NULL, -- bcrypt hash of full key
    name        VARCHAR(100),
    environment VARCHAR(10) DEFAULT 'production',  -- sandbox | production
    is_active   BOOLEAN DEFAULT TRUE,
    last_used   TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- CHECKOUT SESSIONS
-- ─────────────────────────────────────────

CREATE TABLE checkout_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id     UUID REFERENCES merchants(id),
    customer_id     UUID REFERENCES customers(id),
    merchant_order_id VARCHAR(255),         -- merchant's own order ID

    -- Amounts (all in centavos)
    total_amount    INTEGER NOT NULL,
    mdr_amount      INTEGER NOT NULL,       -- total MDR charged
    net_amount      INTEGER NOT NULL,       -- total_amount - mdr_amount

    -- Product
    installment_count SMALLINT NOT NULL,   -- 4 or 12
    installment_amount INTEGER NOT NULL,   -- per installment value

    -- Status
    status          VARCHAR(30) DEFAULT 'pending',
                    -- pending | approved | denied | expired |
                    -- active | completed | refunded | cancelled

    -- Credit decision
    decision        VARCHAR(10),            -- approve | deny
    denial_reason   VARCHAR(50),
    serasa_score_at_decision SMALLINT,

    -- Settlement
    settlement_id   UUID,
    settled_at      TIMESTAMPTZ,

    expires_at      TIMESTAMPTZ,            -- checkout session expiry (30min)
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_checkout_merchant ON checkout_sessions(merchant_id, created_at DESC);
CREATE INDEX idx_checkout_customer ON checkout_sessions(customer_id, created_at DESC);
CREATE INDEX idx_checkout_merchant_order ON checkout_sessions(merchant_id, merchant_order_id);

-- ─────────────────────────────────────────
-- INSTALLMENTS
-- ─────────────────────────────────────────

CREATE TABLE installments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    checkout_id     UUID REFERENCES checkout_sessions(id),
    customer_id     UUID REFERENCES customers(id),

    number          SMALLINT NOT NULL,      -- 1, 2, 3, 4 (or 1..12)
    amount          INTEGER NOT NULL,       -- centavos
    due_date        DATE NOT NULL,

    status          VARCHAR(20) DEFAULT 'pending',
                    -- pending | paid | overdue | cancelled | refunded

    paid_at         TIMESTAMPTZ,
    days_past_due   SMALLINT DEFAULT 0,     -- updated daily by Celery

    -- Collection tracking
    reminder_count  SMALLINT DEFAULT 0,
    last_reminder   TIMESTAMPTZ,
    collection_note TEXT,

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_installments_checkout ON installments(checkout_id);
CREATE INDEX idx_installments_customer ON installments(customer_id);
CREATE INDEX idx_installments_due ON installments(due_date, status)
    WHERE status = 'pending';  -- partial index for overdue queries

-- ─────────────────────────────────────────
-- PIX CHARGES
-- ─────────────────────────────────────────

CREATE TABLE pix_charges (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    installment_id  UUID REFERENCES installments(id),

    -- Celcoin identifiers
    celcoin_id      VARCHAR(100) UNIQUE,
    txid            VARCHAR(35) UNIQUE,     -- Pix txid (35 chars, BCB standard)

    amount          INTEGER NOT NULL,       -- centavos
    qr_code         TEXT,                   -- EMV payload (copy-paste)
    qr_code_image   TEXT,                   -- base64 PNG or S3 URL

    status          VARCHAR(20) DEFAULT 'active',
                    -- active | paid | expired | cancelled

    expires_at      TIMESTAMPTZ NOT NULL,
    paid_at         TIMESTAMPTZ,
    payer_name      VARCHAR(255),
    payer_cpf       VARCHAR(14),

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- SETTLEMENTS (Merchant payouts)
-- ─────────────────────────────────────────

CREATE TABLE settlements (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id     UUID REFERENCES merchants(id),

    amount          INTEGER NOT NULL,       -- centavos
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,

    status          VARCHAR(20) DEFAULT 'pending',
                    -- pending | processing | completed | failed

    pix_e2e_id      VARCHAR(100),           -- Celcoin e2e ID for the transfer
    paid_at         TIMESTAMPTZ,
    failure_reason  VARCHAR(255),

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- LEDGER (Simple double-entry)
-- ─────────────────────────────────────────

CREATE TABLE ledger_entries (
    id              BIGSERIAL PRIMARY KEY,  -- sequential for ordering
    reference_id    UUID NOT NULL,          -- checkout_id, installment_id, etc.
    reference_type  VARCHAR(50) NOT NULL,   -- checkout | installment | settlement | refund

    account         VARCHAR(50) NOT NULL,
                    -- receivable | merchant_payable | mdr_revenue
                    -- cash | credit_loss | late_fee
    direction       CHAR(2) NOT NULL,       -- dr | cr
    amount          INTEGER NOT NULL,       -- centavos, always positive
    description     VARCHAR(255),

    created_at      TIMESTAMPTZ DEFAULT NOW()
    -- NEVER update this table. Append-only.
);

CREATE INDEX idx_ledger_reference ON ledger_entries(reference_id, reference_type);
CREATE INDEX idx_ledger_account ON ledger_entries(account, created_at DESC);

-- ─────────────────────────────────────────
-- NOTIFICATIONS LOG
-- ─────────────────────────────────────────

CREATE TABLE notifications (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id),
    channel     VARCHAR(20) NOT NULL,   -- whatsapp | email | sms
    event_type  VARCHAR(50) NOT NULL,   -- checkout_approved | installment_due | etc.
    status      VARCHAR(20) DEFAULT 'pending',
                -- pending | sent | delivered | failed
    provider_id VARCHAR(100),           -- provider's message ID
    sent_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- WEBHOOK DELIVERIES LOG
-- ─────────────────────────────────────────

CREATE TABLE webhook_deliveries (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id UUID REFERENCES merchants(id),
    event_type  VARCHAR(50) NOT NULL,
    payload     JSONB NOT NULL,
    status      VARCHAR(20) DEFAULT 'pending',
                -- pending | delivered | failed | exhausted
    http_status SMALLINT,
    attempts    SMALLINT DEFAULT 0,
    next_retry  TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.1 Entity Relationship Summary

```
users 1──< customers (one user can be a customer)
users 1──< merchants (one user can own a merchant)

merchants 1──< merchant_api_keys
merchants 1──< checkout_sessions
merchants 1──< settlements
merchants 1──< webhook_deliveries

customers 1──< checkout_sessions
customers 1──< installments
customers 1──< notifications

checkout_sessions 1──< installments
installments      1──< pix_charges (one active charge per installment)

checkout_sessions, installments, settlements → ledger_entries (via reference_id)
```

---

## 3. Module Roadmap

Priority order. Build exactly this, nothing more.

```
MUST HAVE (MVP launch):
  [1] accounts          Auth, JWT, OTP via phone, user management
  [2] customers         Registration, KYC (CAF), credit limit
  [3] merchants         Onboarding, API keys, webhook config
  [4] checkout          Create session, credit decision, QR code
  [5] payments          Pix webhook, installment status, settlement
  [6] admin (basic)     Django admin: view customers, transactions

SHOULD HAVE (week 10–12):
  [7] collections       Celery tasks: overdue detection, reminders
  [8] notifications     WhatsApp (Z-API) + email (Brevo)
  [9] merchant portal   Vue 3: dashboard, transactions, settlements

NICE TO HAVE (post-launch):
  [10] customer portal  Vue 3: my purchases, upcoming payments
  [11] reporting        CSV exports, basic charts
  [12] refunds          Full + partial refund flow
```

---

## 4. Development Phases

### Phase 1 — Foundation (Days 1–30)

**Goal:** Backend running locally with real Pix working end-to-end.

```
Week 1 (Days 1–7): Project Setup
  Day 1:  Django project scaffold + Docker Compose (Postgres + Redis)
  Day 2:  Settings (base/dev/prod) + Celery + logging
  Day 3:  accounts app — User model, JWT auth, OTP generation (Redis-based)
  Day 4:  customers app — Customer model + registration endpoint
  Day 5:  merchants app — Merchant model + API key generation/validation
  Day 6:  Core middleware: API key auth, rate limiting, request logging
  Day 7:  Tests for auth flows + code review

Week 2 (Days 8–14): KYC + Credit
  Day 8:  CAF integration — CPF validation endpoint
  Day 9:  CAF integration — document OCR + liveness check
  Day 10: KYC flow: collect → submit to CAF → webhook → update status
  Day 11: Serasa integration — score + negativado query
  Day 12: Credit engine (rule-based, the ~60 lines above)
  Day 13: Customer limit management — approved vs used limit
  Day 14: Tests for KYC + credit engine

Week 3 (Days 15–21): Checkout Core
  Day 15: checkout app — CheckoutSession model + create endpoint
  Day 16: Celcoin integration — generate Pix dynamic QR code (QRDN)
  Day 17: pix_charges model + link to installments
  Day 18: Installment scheduler — build 4x biweekly schedule
  Day 19: Celcoin webhook receiver — validate signature, process payment
  Day 20: Mark installment PAID + release next QR code
  Day 21: Integration test: full checkout → pay → confirm

Week 4 (Days 22–30): Ledger + Settlement + Admin
  Day 22: Ledger entries — double-entry on checkout approval
  Day 23: Ledger entries — on installment payment
  Day 24: Settlement model + manual trigger endpoint
  Day 25: Celcoin outbound Pix — pay merchant (D+1 settlement)
  Day 26: Django admin — customers, merchants, checkouts, installments
  Day 27: Error handling + retry logic for Celcoin calls
  Day 28: Webhook delivery to merchants (async via Celery)
  Day 29: Environment setup on DigitalOcean (staging)
  Day 30: End-to-end staging test with real Celcoin sandbox
```

### Phase 2 — Operations (Days 31–60)

**Goal:** Collections working. Merchant portal live.

```
Week 5 (Days 31–37): Collections
  Day 31: Celery Beat: daily overdue check (run at 08:00 BRT)
  Day 32: Update days_past_due on all pending installments
  Day 33: DPD rule engine — trigger actions by DPD bucket
  Day 34: Z-API WhatsApp integration — send reminder messages
  Day 35: Brevo email integration — overdue notification templates
  Day 36: New Pix QR code generation for overdue installments
  Day 37: Customer limit suspension at DPD 7

Week 6 (Days 38–44): Merchant Portal (Vue 3)
  Day 38: Vue 3 + Vite + Tailwind project setup (merchant-portal/)
  Day 39: Login page + JWT handling + axios interceptors
  Day 40: Dashboard: GMV today/week/month + approval rate
  Day 41: Transactions table: list, search by date, filter by status
  Day 42: Transaction detail modal: installment breakdown
  Day 43: Settlement list + expected dates
  Day 44: Webhook config page (URL + secret + test button)

Week 7 (Days 45–51): API Polish + Security
  Day 45: Idempotency keys on all POST endpoints
  Day 46: Rate limiting per API key (Redis-backed)
  Day 47: Input validation hardening (all serializers)
  Day 48: CORS config + security headers (HSTS, CSP)
  Day 49: Audit log for sensitive operations
  Day 50: API docs (drf-spectacular → Swagger UI)
  Day 51: Penetration test checklist review

Week 8 (Days 52–60): Consumer Portal (Vue 3)
  Day 52: Customer portal project setup (customer-portal/)
  Day 53: Login via OTP (phone → SMS → JWT)
  Day 54: Home: available limit + upcoming payments summary
  Day 55: My purchases list
  Day 56: Purchase detail: installment timeline + payment status
  Day 57: Pay now button → new QR code for overdue installments
  Day 58: Notification preferences page
  Day 59: Profile page (view only for MVP)
  Day 60: Mobile responsive polish (Tailwind breakpoints)
```

### Phase 3 — Launch (Days 61–90)

**Goal:** Production live. First 3 merchants. First real transactions.

```
Week 9 (Days 61–67): Production Infrastructure
  Day 61: DigitalOcean production Droplet + managed Postgres + Redis
  Day 62: Nginx config + Let's Encrypt SSL + Gunicorn service
  Day 63: Celery worker + Celery Beat as systemd services
  Day 64: CI/CD: GitHub Actions → build → SSH deploy → migrations
  Day 65: Cloudflare DNS + proxy + WAF rules
  Day 66: Backup: automated daily Postgres backups to S3
  Day 67: Monitoring: Sentry (free) + UptimeRobot (free)

Week 10 (Days 68–74): Merchant Integration Support
  Day 68: Write integration guide (Markdown + Postman collection)
  Day 69: Sandbox environment for merchant testing
  Day 70: WooCommerce plugin (simple PHP, calls our API)
  Day 71: Nuvemshop app submission
  Day 72: First merchant: manual integration support
  Day 73: Second merchant: integration support
  Day 74: Bug fixes from real merchant testing

Week 11 (Days 75–81): Hardening
  Day 75: Load test: 50 concurrent checkouts (locust)
  Day 76: Database: add missing indexes, query optimization
  Day 77: Redis: tune TTLs, connection pooling
  Day 78: Celery: configure concurrency + retry policies
  Day 79: Runbook: on-call procedures, common incidents
  Day 80: Collections: test full DPD flow end-to-end
  Day 81: Merchant portal: final QA across browsers

Week 12 (Days 82–90): Go-Live
  Day 82: Third merchant integration
  Day 83: Soft launch: 3 merchants, invite-only
  Day 84: Monitor first real transactions (on-call)
  Day 85: Fix any production bugs (hotfix protocol)
  Day 86: First settlement run (D+1 payout to merchant)
  Day 87: First collection reminder test (overdue simulation)
  Day 88: Analytics: first GMV, approval rate, DPD report
  Day 89: Retrospective: what's broken, what's missing
  Day 90: 🚀 Public launch announcement (LinkedIn, Twitter)
```

---

## 5. Estimated Monthly Costs

All prices in BRL. Using DigitalOcean for infra (predictable pricing, Pix available).

### Infrastructure

| Service | Plan | Monthly |
|---------|------|---------|
| **DigitalOcean Droplet** | 4 vCPU / 8GB RAM / 160GB SSD | R$250 |
| **Managed PostgreSQL** | 1 vCPU / 1GB (Basic) | R$80 |
| **Managed Redis** | 1GB (Basic) | R$40 |
| **Spaces (S3-compatible)** | 250GB (KYC docs) | R$25 |
| **Cloudflare** | Free (WAF + CDN + SSL) | R$0 |
| **Domain (.com.br)** | Annual ÷ 12 | R$8 |
| **Subtotal infra** | | **R$403** |

### APIs & Third-Party

| Service | Unit Cost | Monthly Est. (low volume) |
|---------|-----------|--------------------------|
| **Celcoin Pix** | ~R$0.40/QR + 0.10/webhook | R$200 (500 QRs/month) |
| **CAF.io KYC** | ~R$3.00/complete KYC | R$300 (100 new customers) |
| **Serasa Score** | ~R$1.50/consultation | R$250 (consultations + re-checks) |
| **Z-API WhatsApp** | R$69/month flat | R$69 |
| **Brevo Email** | Free (300/day) | R$0 |
| **Sentry** | Free tier (5k errors/month) | R$0 |
| **UptimeRobot** | Free tier (50 monitors) | R$0 |
| **Subtotal APIs** | | **R$819** |

### Fixed Monthly

| Service | Monthly |
|---------|---------|
| **Contador (accounting)** | R$400 |
| **Subtotal fixed** | **R$400** |

### Total Monthly Operating Cost

| Phase | GMV | Monthly Cost |
|-------|-----|-------------|
| Pre-launch / dev | R$0 | ~R$800 (infra + APIs) |
| Early (100 customers) | R$20k | ~R$1,622 |
| Growing (500 customers) | R$100k | ~R$2,500 (API costs scale) |
| Scale (1,000 customers) | R$200k | ~R$4,000 |

> **Key insight:** Costs are mostly fixed until R$100k+ GMV/month. API costs scale roughly linearly with volume but remain a small % of revenue.

---

## 6. Estimated Legal Costs

### One-Time Setup (Year 1)

| Item | Cost | Notes |
|------|------|-------|
| **LTDA registration** (Junta Comercial) | R$800 | DIY via Portal do Empreendedor or with contador |
| **CNPJ registration** | R$0 | Free, done with LTDA registration |
| **Correspondente bancário agreement** | R$4,000–8,000 | Lawyer drafts + negotiates with SCD partner |
| **Merchant agreement template** | R$2,000–3,000 | Standard T&C + MDR agreement |
| **Consumer T&C + Privacy Policy** | R$1,500–2,500 | LGPD-compliant, by lawyer |
| **LGPD: DPO appointment + ROPA** | R$1,000–2,000 | Can appoint founder as DPO initially |
| **COAF registration** | R$0 | Online, self-service |
| **Subtotal one-time legal** | **R$9,300–16,300** | Budget R$12,000 |

### Recurring Legal

| Item | Monthly |
|------|---------|
| **Contador** (accounting + taxes) | R$400 |
| **Legal retainer** (optional) | R$500–1,000 |
| **Total legal recurring** | **R$400–1,400** |

### Credit Partner (SCD) Costs

Finding an SCD partner requires:
- **Negotiation time:** 1–3 months to find and close
- **Revenue share:** they keep 3–4% MDR, you keep 3–4%
- **Setup fee (if any):** R$0–5,000 (varies by partner)
- **Candidates:** QI Tech, BMP Money Plus, Giro.Tech, Celcoin (check their BaaS credit products)

---

## 7. Capital Requirements

### Budget Breakdown (R$50,000)

| Category | Amount | Notes |
|----------|--------|-------|
| **Legal setup** | R$12,000 | One-time (conservative estimate) |
| **Infrastructure (6 months)** | R$5,000 | R$800/month × 6 months pre-revenue |
| **API setup & testing** | R$2,000 | Sandbox costs, dev testing |
| **Development tools** | R$500 | GitHub, misc subscriptions |
| **Working capital buffer** | R$10,000 | Emergency reserve |
| **Marketing / launch** | R$3,000 | LinkedIn ads, landing page, events |
| **Accounting (6 months)** | R$2,400 | R$400/month × 6 |
| **Miscellaneous** | R$2,000 | Notary, travel, etc. |
| **TOTAL SPENT** | **R$36,900** | |
| **Reserve** | **R$13,100** | Remaining buffer |

> **The good news:** Because you're using a credit partner SCD, you do NOT need working capital for the loan portfolio. The SCD funds the credit; you just build and distribute.

### Without Credit Partner (Self-Funded Model)

If you prefer to fund your own credit (higher margin, no partner needed, but capital-constrained):

| Credit Capital | Avg Portfolio Outstanding | Monthly GMV Capacity | Monthly MDR Revenue |
|---------------|--------------------------|---------------------|---------------------|
| R$10,000 | R$10,000 | ~R$7,000/month | ~R$490 |
| R$20,000 | R$20,000 | ~R$14,000/month | ~R$980 |
| R$30,000 | R$30,000 | ~R$21,000/month | ~R$1,470 |

At R$30k credit capital → ~R$1,470/month gross MDR → not enough to survive.
**Recommendation: Use credit partner SCD for MVP stage.**

---

## 8. Merchant Onboarding Strategy

### The Fundamental Insight

Don't go to consumers. Go to merchants. Consumers come through merchant checkouts.
One merchant with 200 orders/month = 200 potential BNPL users, zero consumer marketing spend.

### Target Profile — First 10 Merchants

Ideal first merchant:
- E-commerce, 100–500 orders/month
- Average ticket R$150–500
- Currently losing sales due to payment friction
- Accepts credit card but wants to offer alternative (or reduce credit card fees)
- Small enough that the owner makes the decision in one call
- Niches: fashion, supplements/health, electronics accessories, pet products

Where to find them:
- **LinkedIn:** Search "e-commerce" + your city, DM founders directly
- **Instagram:** Brands with product pages but limited payment options
- **Nuvemshop / WooCommerce communities:** Facebook groups
- **Your own network:** Who do you know that runs an online store?

### Onboarding Offer (MVP)

```
First 3 months:
  - 0% setup fee
  - 0% monthly fee
  - 5% MDR (below market to get traction)
  - Same-day onboarding support
  - Free WooCommerce/Nuvemshop plugin
  - 1:1 integration support via WhatsApp

After Month 4:
  - Standard MDR: 7%
```

### Pitch Script (3 sentences)

> *"Você sabe que perde vendas porque o cliente não tem cartão de crédito ou não quer usar o limite? A Pagaê parcela a compra em 4x sem juros no Pix — o cliente paga quinzenal, você recebe 100% na hora. Não tem mensalidade, não tem setup — você só paga 5% quando vende."*

### Onboarding Process (Solo Founder, Manual)

```
Day 0: Prospect agrees to try → send integration guide + sandbox credentials
Day 1: 1:1 WhatsApp call to help integrate (screen share)
Day 2: Merchant tests in sandbox → approves 2-3 test transactions
Day 3: Flip to production API key → go live
Day 4: Check first real transaction together
Day 7: Follow up → any issues? conversion rate?
Day 30: First settlement paid → relationship solidified
```

### 90-Day Merchant Acquisition Target

```
Month 1: 3 merchants onboarded (founder does everything manually)
Month 2: 5 more merchants (word-of-mouth + LinkedIn outreach)
Month 3: 5 more merchants (plugins attracting inbound)
Total at launch: ~13 active merchants
```

---

## 9. First 100 Customers Acquisition Plan

### The Math

If 13 merchants each have 50 BNPL transactions in Month 3:
- 13 × 50 = 650 consumer registrations (many repeat)
- Unique customers: ~300–400
- Active customers (made purchase in last 30 days): ~150–200

You hit 100 active customers by Month 2, just through merchant checkout flow. **No consumer marketing needed at MVP stage.**

### Consumer Acquisition: Pull Model

```
Merchant launches Pagaê →
  Consumer sees Pagaê at checkout →
  Consumer registers (CPF + phone + selfie) →
  Consumer makes first purchase →
  Consumer gets WhatsApp confirmation →
  Consumer remembers Pagaê for next purchase
```

### Retention: Reminders Drive Repeat Usage

The installment reminders are free retention marketing:
- Day before due date: WhatsApp reminder → consumer sees brand again
- Payment confirmed: WhatsApp receipt → positive brand touchpoint
- Upcoming due: push notification → keeps app/brand top-of-mind

### Consumer Funnel (Realistic)

```
100 consumers visit merchant checkout page that has Pagaê
  ↓ 30 click on "Parcele em 4x no Pix" (30% CTR)
  ↓ 20 complete registration (67% completion)
  ↓ 14 get approved (70% approval rate — conservative rules)
  ↓ 12 complete first payment (86% completion of approved)

Conversion: 12 customers per 100 checkout impressions
```

### What Gets You to 100 Active Customers Faster

1. **Merchant with high traffic** — one merchant with 1,000 monthly orders beats 10 merchants with 100 each
2. **Niche with repeat purchase** — supplements, pet food, coffee: customers buy monthly → repeat BNPL
3. **Referral incentive** — "Indique um amigo, ganhe R$20 de limite" (cheap: only if friend makes a purchase)
4. **Seamless UX** — if KYC takes 4 minutes, not 10, completion rates double
5. **WhatsApp-first** — reach consumers where they are; don't build app, use WhatsApp as the interface

### Month-by-Month Customer Growth

| Month | New Customers | Active Customers | Key Driver |
|-------|--------------|-----------------|------------|
| 1 | 40 | 35 | 3 merchant launches |
| 2 | 80 | 95 | 5 more merchants + repeat |
| 3 | 60 | 140 | Repeat purchases dominant |
| 4 | 80 | 190 | Word of mouth |
| 5 | 120 | 280 | Plugin installs driving inbound |
| 6 | 150 | 400 | Growth flywheel |

---

## 10. Revenue Projections

### Assumptions

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Average ticket | R$250 | Fashion + health niche |
| MDR (you keep) | 3.5% | Credit partner keeps 3.5%, you keep 3.5% |
| Purchases/customer/month | 1.5 | Repeat purchase + new merchants |
| Credit loss | 3% of GMV | Conservative rule-based scoring |
| KYC cost/new customer | R$3.00 | CAF pricing |
| Serasa cost/transaction | R$1.50 | Per credit check |
| Monthly infra + APIs | R$1,622 | From section 5 |

### Revenue at 100 Active Customers

```
Monthly GMV:          100 × 1.5 × R$250   = R$37,500
MDR Revenue (3.5%):   R$37,500 × 3.5%     = R$1,313
Credit Loss (3%):     R$37,500 × 3%       = (R$1,125)
KYC Costs:            ~20 new users × R$3 = (R$60)
Serasa Costs:         ~150 queries × R$1.5= (R$225)
Infra + APIs:                               (R$1,622)
                                           ─────────
Net Monthly:                               = (R$1,719)  ← still burning
```

**At 100 customers you are NOT profitable. This is expected — prove the model, not the P&L.**

### Revenue at 500 Active Customers

```
Monthly GMV:          500 × 1.5 × R$250   = R$187,500
MDR Revenue (3.5%):   R$187,500 × 3.5%    = R$6,563
Credit Loss (2.5%):   R$187,500 × 2.5%    = (R$4,688)  ← improving with data
KYC Costs:            ~60 new users × R$3 = (R$180)
Serasa Costs:         ~750 queries × R$1.5= (R$1,125)
Infra + APIs:                               (R$2,500)   ← scaled slightly
Accounting:                                 (R$400)
                                           ─────────
Net Monthly:                               = (R$2,330)  ← still burning, but less
```

**At 500 customers you need your credit partner to take the default risk, otherwise this burns fast.**

### Revenue at 1,000 Active Customers

```
Monthly GMV:          1,000 × 1.5 × R$250  = R$375,000
MDR Revenue (3.5%):   R$375,000 × 3.5%     = R$13,125
Credit Loss (2%):     R$375,000 × 2%       = (R$7,500)  ← credit partner absorbs this
KYC Costs:            ~80 new users × R$3  = (R$240)
Serasa Costs:         ~1,500 queries × R$1.5=(R$2,250)
Infra + APIs:                                (R$4,000)
Accounting + legal:                          (R$800)
                                            ─────────
Net Monthly:                                = (R$1,665) ← still negative?
```

Wait — at this point the credit loss should hit the SCD partner's P&L (since they own the credit). If credit partner absorbs defaults:

```
Monthly GMV:          R$375,000
MDR Revenue (3.5%):                          R$13,125
KYC + Serasa:                               (R$2,490)
Infra + APIs:                               (R$4,000)
Accounting:                                 (R$800)
                                           ─────────
Net Monthly (partner model):               = R$5,835  ← PROFITABLE ✅
```

**Breakeven in partner model: ~700–800 active customers (~Month 8–10)**

### Summary Table

| Metric | 100 customers | 500 customers | 1,000 customers |
|--------|--------------|--------------|-----------------|
| Monthly GMV | R$37,500 | R$187,500 | R$375,000 |
| Gross MDR (yours) | R$1,313 | R$6,563 | R$13,125 |
| Operating Costs | R$1,622 | R$2,500 | R$4,800 |
| Net (partner model) | **(R$309)** | **R$4,063** | **R$8,325** |
| Annualized Revenue | — | R$48,750 | R$99,900 |

> **Breakeven:** ~650 active customers ≈ Month 7–8 if growth is linear.  
> **At 1,000 customers:** ~R$8–10k/month net — a real business, fundable for next round.

---

## Appendix A — Tech Stack Decision Rationale

| Decision | Why |
|----------|-----|
| **Single VPS (not EKS)** | Simpler, cheaper, debuggable. 1 server handles 50k req/day easily. |
| **Django Admin as ops panel** | Don't build custom admin. Extend Django admin. Saves 3 weeks. |
| **Vue 3 (not React)** | Smaller bundle, simpler for merchant/consumer portals. No Next.js overhead. |
| **Celery Beat for collections** | One daily Celery job replaces entire collection microservice. |
| **Z-API for WhatsApp** | R$69/month flat, unofficial API but works. Upgrade to official Meta API at scale. |
| **Celcoin** | Best API for Brazilian fintechs, competitive pricing, good support. |
| **CAF.io** | Startup-friendly KYC pricing, good SDK, Brazilian company. |
| **Brevo email** | 300 free emails/day covers you until 2,000+ customers. |
| **Cloudflare free tier** | DDoS protection + WAF + CDN + free SSL. No reason not to use. |

---

## Appendix B — Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| SCD partner can't be found | Medium | Start with 2-3 partners in parallel; Celcoin, QI Tech, BMP |
| Celcoin outage | Low | Build provider interface; add FitBank as backup Day 60 |
| Credit loss exceeds 5% | Medium | Cut approvals to score ≥ 700 only; reduce limits to R$150 |
| CAF KYC costs too high | Low | Negotiate volume discount at 1k KYCs; fallback to manual |
| First merchant churns | Medium | Have 3 merchants before relying on any single one |
| Regulatory surprise | Low | Correspondente model is proven; monitor BCB bulletins monthly |
| Founder burnout at Day 60 | Medium | Hire 1 part-time developer at Day 30 if capital allows |

---

*Phase 0 complete. This MVP plan supersedes the enterprise architecture for the bootstrap stage.*  
*Approval to begin Phase 1 implementation: Django project scaffold + database.*
