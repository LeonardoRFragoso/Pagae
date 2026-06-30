# Architecture Proposal — Brazilian BNPL Platform

> **Classification:** Internal — Engineering  
> **Date:** June 2026  
> **Version:** 1.0

---

## 1. Architecture Philosophy

### 1.1 Core Principles

1. **Correctness over performance** — financial systems must be correct first. No race conditions, no double-spends, no lost transactions.
2. **Auditability by design** — every financial movement, every decision, every state change must be logged and reconstructible.
3. **Defense in depth** — security at every layer; assume breach.
4. **Progressive complexity** — start as modular monolith, extract microservices as bounded contexts prove independence.
5. **Fail safely** — checkout flows degrade gracefully; credit denials > system errors.
6. **Idempotency everywhere** — all financial operations must be idempotent (safe to retry).

### 1.2 Architectural Pattern: Modular Monolith → Microservices

We start as a **modular monolith** — a single deployable Django application with strict internal module boundaries — designed to allow future **microservice extraction** without re-architecture.

Why not microservices from day 1?
- Team is small at launch; distributed systems complexity kills velocity
- Modular monolith is faster to ship, cheaper to operate, easier to debug
- Domain boundaries are not yet proven; premature extraction causes wrong cuts
- When a bounded context proves stable and has clear interface contracts, extract it

**Extraction order (planned):**
1. `risk` + `credit` → highest compute intensity, ML workloads
2. `payments` → most critical SLA, needs independent scaling
3. `notifications` → async, natural microservice candidate
4. `analytics` → read-heavy, separate read path

---

## 2. Bounded Contexts

```
┌─────────────────────────────────────────────────────────────────┐
│                     PAGAÊ PLATFORM                               │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ accounts │  │customers │  │merchants │  │ checkout │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  credit  │  │   risk   │  │payments  │  │installmts│        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │collections│  │  ledger  │  │  notifs  │  │analytics │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.1 Bounded Context Responsibilities

| Context | Responsibility | Key Entities |
|---------|---------------|-------------|
| **accounts** | Authentication, authorization, sessions, RBAC | User, Role, Permission, Session, APIKey |
| **customers** | Consumer profile, KYC, limits, status | Customer, KYCDocument, KYCResult, CreditLimit |
| **merchants** | Merchant onboarding, credentials, webhooks | Merchant, APICredential, Webhook, Settlement |
| **checkout** | Purchase initiation, session, status | CheckoutSession, CheckoutItem, CheckoutStatus |
| **credit** | Credit decisions, scoring, limits | CreditDecision, CreditScore, CreditRule |
| **risk** | Fraud detection, device, velocity | FraudSignal, DeviceFingerprint, RiskScore |
| **payments** | Pix collection, payment provider abstraction | Payment, PixCharge, PaymentProvider |
| **installments** | Payment schedules, due dates, retries | Installment, PaymentSchedule, InstallmentStatus |
| **collections** | Overdue management, workflow, escalation | CollectionCase, CollectionAction, CollectionAgent |
| **ledger** | Double-entry accounting, balances | Account, JournalEntry, Ledger, Transaction |
| **notifications** | Email, SMS, WhatsApp, push | Notification, NotificationTemplate, Channel |
| **analytics** | Reporting, metrics, dashboards | Report, Metric, Cohort |

---

## 3. Technology Stack

### 3.1 Backend

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| Language | Python | 3.13 | Async support, ML ecosystem, team velocity |
| Framework | Django | 5.x | ORM, admin, migrations, mature ecosystem |
| API | Django REST Framework | 3.15+ | Serializers, viewsets, auth integration |
| Task Queue | Celery | 5.x | Distributed task processing |
| Message Broker | Redis | 7.x | Celery broker + cache + rate limiting |
| Database | PostgreSQL | 16 | ACID, JSON support, mature, BCB-compliant |
| Search | — | — | Phase 2: OpenSearch for analytics |
| Object Storage | AWS S3 | — | KYC documents, statements |

**Django App Structure:**
```
pagae/
├── manage.py
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── testing.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/
│   ├── customers/
│   ├── merchants/
│   ├── checkout/
│   ├── credit/
│   ├── risk/
│   ├── payments/
│   ├── installments/
│   ├── collections/
│   ├── ledger/
│   ├── notifications/
│   └── analytics/
├── core/
│   ├── models.py        # BaseModel with id, created_at, updated_at
│   ├── exceptions.py    # Domain exceptions
│   ├── events.py        # Domain events
│   ├── middleware.py    # Request logging, correlation IDs
│   └── utils/
├── infrastructure/
│   ├── pix/             # Pix provider adapters
│   ├── bureau/          # Credit bureau adapters
│   ├── kyc/             # KYC provider adapters
│   ├── messaging/       # WhatsApp, SMS adapters
│   └── storage/         # S3 adapter
└── tests/
```

### 3.2 Frontend

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| Framework | Vue 3 | 3.4+ | Composition API, TypeScript-first |
| Language | TypeScript | 5.x | Type safety, IDE support |
| State | Pinia | 2.x | Lightweight, TypeScript-native |
| Router | Vue Router | 4.x | Official, SSR-compatible |
| UI | Tailwind CSS | 3.x | Utility-first, design system |
| Components | Headless UI | 1.x | Accessible, unstyled primitives |
| Icons | Heroicons / Lucide | — | MIT licensed |
| Charts | Chart.js / ApexCharts | — | Analytics dashboard |
| HTTP | Axios | 1.x | Interceptors, retry logic |
| Forms | VeeValidate + Zod | — | Schema validation |
| i18n | vue-i18n | — | PT-BR primary |
| Build | Vite | 5.x | Fast HMR, ESM |

**Frontend Apps:**
```
frontend/
├── customer-app/      # Mobile-first consumer PWA
├── merchant-portal/   # Merchant dashboard
└── admin-panel/       # Internal operations console
```

### 3.3 Infrastructure

| Component | Technology | Notes |
|-----------|-----------|-------|
| Container | Docker | All services containerized |
| Orchestration | Kubernetes | AWS EKS for production |
| CI/CD | GitHub Actions | Build, test, deploy |
| Cloud | AWS | Primary cloud provider |
| DNS / CDN | CloudFront + Route 53 | Global CDN |
| Load Balancer | AWS ALB | Layer 7, SSL termination |
| Secrets | AWS Secrets Manager | No secrets in env vars |
| Monitoring | Prometheus + Grafana | Metrics |
| Logging | Structured JSON → CloudWatch / OpenSearch | Centralized logs |
| APM | Sentry + OpenTelemetry | Error tracking + tracing |
| Database | AWS RDS (PostgreSQL) | Multi-AZ |
| Cache | AWS ElastiCache (Redis) | Cluster mode |
| Storage | AWS S3 | KYC documents, encrypted |
| Queue | AWS SQS (optional) | DLQ for failed tasks |

---

## 4. Data Architecture

### 4.1 Database Design Principles

1. **UUID primary keys** — never expose sequential IDs in public APIs
2. **Soft deletes** — `is_deleted` + `deleted_at` instead of hard DELETE
3. **Audit columns** — every table has `created_at`, `updated_at`, `created_by`
4. **Immutable financial records** — ledger entries are never updated, only inserted
5. **Enum values stored as strings** — not integers (readability + migration safety)
6. **Currency stored as integers** — amounts in centavos (R$100.00 = 10000), never floats
7. **All Pix/payment amounts** — in centavos, separate currency field

### 4.2 Core Entity Relationships

```
Customer (CPF) ──< CreditDecision
Customer ──< Installment (via CheckoutSession)
Customer ──< KYCDocument

Merchant ──< CheckoutSession
Merchant ──< APICredential
Merchant ──< Webhook

CheckoutSession ──< Installment
CheckoutSession >── CreditDecision
CheckoutSession >── Payment (first payment = merchant settlement)

Installment ──< Payment (each installment = one Pix charge)
Installment ──< CollectionCase (when overdue)

Payment >── PixCharge
Payment → LedgerTransaction (via double-entry)

LedgerTransaction ──< JournalEntry (min 2 per transaction)
```

### 4.3 Financial Data Model — Double-Entry Ledger

**Core accounts (chart of accounts):**

```
ASSET ACCOUNTS:
  1010  Cash (Pix received)
  1020  Receivables - BNPL portfolio
  1030  Receivables - Overdue (90+ DPD)
  1040  Allowance for Credit Losses (contra-asset)

LIABILITY ACCOUNTS:
  2010  Merchant payables (settlement due)
  2020  Consumer refunds payable

REVENUE ACCOUNTS:
  4010  MDR Revenue
  4020  Interest Income (12x product)
  4030  Late Fee Income

EXPENSE ACCOUNTS:
  5010  Credit Loss Expense (provisions)
  5020  Pix transaction costs
  5030  Bureau query costs
```

**Example journal entry — checkout approval:**
```
Dr  1020  Receivables (BNPL)      R$1,000.00  (4 installments × R$250)
    Cr  2010  Merchant Payable           R$950.00   (net of MDR 5%)
    Cr  4010  MDR Revenue                R$50.00
```

**Installment payment received:**
```
Dr  1010  Cash (Pix)              R$250.00
    Cr  1020  Receivables              R$250.00
```

**Overdue provisioning:**
```
Dr  5010  Credit Loss Expense      R$250.00
    Cr  1040  Allowance for Losses      R$250.00
```

---

## 5. API Design

### 5.1 API Standards

- **REST** for all public/merchant-facing APIs
- **Versioned** — `/api/v1/`, `/api/v2/`
- **JSON:API** inspired but simplified
- **JWT** authentication (access + refresh tokens)
- **API Key** authentication for merchant server-to-server
- **HTTPS only** — no HTTP
- **Rate limiting** — per API key and per IP
- **Idempotency keys** — all POST endpoints accept `Idempotency-Key` header

### 5.2 Core API Contracts

**Merchant Checkout API:**
```
POST   /api/v1/checkout/simulate      # Calculate installment options
POST   /api/v1/checkout/create        # Initiate checkout session
GET    /api/v1/checkout/{id}/status   # Poll checkout status
POST   /api/v1/checkout/{id}/cancel   # Cancel checkout
POST   /api/v1/refunds                # Refund request
POST   /api/v1/webhooks/test          # Test webhook delivery
GET    /api/v1/transactions           # Transaction listing
GET    /api/v1/transactions/{id}      # Transaction detail
GET    /api/v1/settlements            # Settlement reports
```

**Customer App API:**
```
POST   /api/v1/auth/register          # Customer registration
POST   /api/v1/auth/token             # Login (phone + OTP)
POST   /api/v1/auth/refresh           # Refresh token
POST   /api/v1/kyc/documents          # Submit KYC documents
GET    /api/v1/kyc/status             # KYC status
GET    /api/v1/customers/me           # Profile
PUT    /api/v1/customers/me           # Update profile
GET    /api/v1/customers/me/limit     # Credit limit status
GET    /api/v1/installments           # My installments
GET    /api/v1/installments/{id}      # Installment detail
GET    /api/v1/purchases              # Purchase history
GET    /api/v1/statements             # Statement / extract
```

**Internal Admin API:**
```
GET/PUT  /api/v1/admin/customers/{id}         # Customer management
GET/PUT  /api/v1/admin/merchants/{id}         # Merchant management
GET      /api/v1/admin/transactions           # All transactions
GET/PUT  /api/v1/admin/credit-decisions/{id}  # Credit decisions
GET/PUT  /api/v1/admin/collections/{id}       # Collection cases
GET      /api/v1/admin/reports/portfolio      # Portfolio metrics
GET      /api/v1/admin/reports/risk           # Risk dashboard
```

### 5.3 Webhook Event Schema

All webhooks follow a consistent schema:
```json
{
  "event": "checkout.completed",
  "event_id": "evt_01HV...",
  "created_at": "2026-06-16T18:00:00Z",
  "api_version": "2026-06-01",
  "data": {
    "checkout_id": "chk_01HV...",
    "status": "APPROVED",
    "customer": { "name": "João Silva", "cpf_last4": "1234" },
    "amount": 100000,
    "currency": "BRL",
    "installments": 4
  }
}
```

Merchant must return HTTP 200 within 10 seconds. Failed deliveries retried with exponential backoff: 1m → 5m → 30m → 2h → 12h → 24h.

---

## 6. Credit Engine Architecture

### 6.1 Decision Pipeline

```
Checkout Request
      │
      ▼
┌─────────────┐
│  Hard Rules  │ ← instant rejection (fraud flag, OFAC, etc.)
└─────────────┘
      │ pass
      ▼
┌─────────────┐
│  Risk Score  │ ← device, velocity, behavioral signals
└─────────────┘
      │
      ▼
┌─────────────┐
│ Credit Score │ ← bureau data, Open Finance, internal history
└─────────────┘
      │
      ▼
┌─────────────┐
│  Policy     │ ← configurable rules: score thresholds, limits
└─────────────┘
      │
      ▼
┌──────────────────────────────┐
│ APPROVE / DENY / MANUAL      │
│ + Limit + Installment options│
└──────────────────────────────┘
```

**SLA target:** complete pipeline in **< 500ms** (p99)

### 6.2 Pluggable Scoring Providers

```python
# Abstract interface — all scoring providers implement this
class ScoringProvider(ABC):
    @abstractmethod
    def score(self, request: CreditRequest) -> CreditScore:
        ...

# Implementations
class SerasaProvider(ScoringProvider): ...
class SPCProvider(ScoringProvider): ...
class InternalMLProvider(ScoringProvider): ...
class OpenFinanceProvider(ScoringProvider): ...
class MockProvider(ScoringProvider): ...  # Testing
```

Providers are **orchestrated** by the Credit Engine:
- Multiple providers queried in parallel
- Results merged and weighted
- Provider failure triggers fallback (not hard reject unless all fail)

### 6.3 Rule Engine

Configurable rules stored in database, evaluated by rules engine:
```
Rule: "deny_if_serasa_score_below"
  condition: serasa_score < 400
  action: DENY
  priority: 100

Rule: "limit_new_customer"
  condition: customer.total_purchases == 0
  action: SET_LIMIT(500_00)  # R$500
  priority: 200

Rule: "approve_if_excellent_history"
  condition: internal_score >= 900 AND dpd_90 == 0
  action: APPROVE
  priority: 50
```

Rules are versioned, testable, and auditable. No code deployment needed to tune risk parameters.

---

## 7. Payment Architecture

### 7.1 Payment Provider Abstraction

```python
class PaymentProvider(ABC):
    @abstractmethod
    def create_charge(self, charge: ChargeRequest) -> Charge: ...
    
    @abstractmethod
    def get_charge(self, charge_id: str) -> Charge: ...
    
    @abstractmethod
    def cancel_charge(self, charge_id: str) -> bool: ...
    
    @abstractmethod
    def refund(self, charge_id: str, amount: int) -> Refund: ...
    
    @abstractmethod
    def process_webhook(self, payload: dict) -> PaymentEvent: ...

class CelcoinProvider(PaymentProvider): ...
class DockProvider(PaymentProvider): ...
class FitBankProvider(PaymentProvider): ...
class QITechProvider(PaymentProvider): ...
```

### 7.2 Payment State Machine

```
PENDING → WAITING_PAYMENT → PAID
        ↘ EXPIRED
        ↘ CANCELLED
        ↘ FAILED
PAID    → REFUNDED (partial or full)
```

### 7.3 Idempotency

All payment operations use idempotency keys:
- Key = `{installment_id}:{attempt_number}`
- Stored in Redis for 24h
- Duplicate requests return cached response without re-processing

---

## 8. Security Architecture

### 8.1 Authentication & Authorization

```
Consumers:     OTP (SMS/WhatsApp) → JWT access (15min) + refresh (7 days)
Merchants:     API Key (server-to-server) + JWT for dashboard
Internal:      SSO (Google Workspace) + JWT + MFA mandatory
Admin:         SSO + JWT + MFA + RBAC strict roles
```

**RBAC Roles:**
```
customer         — read own data, initiate checkout
merchant_basic   — create checkout, view own transactions
merchant_admin   — + manage webhooks, view settlements
ops_agent        — view customers, merchants, transactions (read-only)
ops_supervisor   — + approve manual reviews, manage collections
risk_analyst     — + view risk signals, adjust rules (read)
risk_admin       — + modify risk rules, approve model changes
finance          — + view ledger, settlements, reconciliation
engineering      — + system config (not financial data)
super_admin      — full access + audit logs
```

### 8.2 Data Security

- **Encryption at rest**: RDS encrypted with AWS KMS, S3 SSE-KMS
- **Encryption in transit**: TLS 1.3 everywhere, HSTS headers
- **CPF storage**: encrypted in database (AES-256), only last 4 digits shown in UI
- **API keys**: stored as bcrypt hashes (never plaintext), prefix visible only
- **Secrets**: AWS Secrets Manager + rotation
- **Audit logs**: immutable append-only log (separate table or CloudWatch)
- **PII masking**: logs never contain full CPF, card numbers, or tokens

### 8.3 Rate Limiting

```
Public API (unauthenticated):  10 req/min per IP
Customer API:                  60 req/min per token
Merchant API:                  300 req/min per API key
Checkout endpoint:             10 req/min per merchant (configurable)
Auth endpoints:                5 req/min per IP (OTP generation)
```

---

## 9. Observability Architecture

### 9.1 Structured Logging

All logs are structured JSON:
```json
{
  "timestamp": "2026-06-16T18:00:00.123Z",
  "level": "INFO",
  "service": "checkout",
  "trace_id": "abc123",
  "span_id": "def456",
  "customer_id": "cus_01HV...",
  "event": "checkout.credit_decision",
  "decision": "APPROVED",
  "duration_ms": 342,
  "provider": "serasa"
}
```

No PII in logs. Replace with masked identifiers.

### 9.2 Metrics (Prometheus)

**Business metrics:**
- `checkout_requests_total{status}` — approvals, denials, errors
- `checkout_decision_duration_seconds` — credit decision latency histogram
- `installment_dpd_total{bucket}` — overdue by DPD bucket
- `payment_success_rate{provider}` — Pix collection success by provider
- `fraud_events_total{type}` — fraud detection counts

**Technical metrics:**
- Standard Django/Celery/PostgreSQL metrics via exporters
- Per-endpoint latency (p50, p95, p99)
- Queue depth and worker saturation

### 9.3 Alerts

| Alert | Threshold | Action |
|-------|-----------|--------|
| Checkout error rate | > 1% | Page on-call |
| Credit decision p99 | > 2s | Page on-call |
| Payment success rate | < 95% | Page on-call |
| NPL 30-day spike | > +0.5% daily | Slack alert |
| Queue depth | > 10,000 | Slack alert |
| Database connections | > 80% pool | Slack alert |

---

## 10. Infrastructure Topology

### 10.1 AWS Architecture

```
                    Internet
                       │
               ┌───────▼────────┐
               │  CloudFront CDN │
               │  + WAF + Shield │
               └───────┬────────┘
                       │
               ┌───────▼────────┐
               │  ALB (HTTPS)    │
               └───────┬────────┘
                       │
               ┌───────▼────────┐
               │   EKS Cluster   │
               │ ┌─────────────┐ │
               │ │  API Pods   │ │
               │ │  Worker Pods│ │
               │ │  Celery Beat│ │
               │ └─────────────┘ │
               └───────┬────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──┐   ┌───────▼──┐  ┌───────▼──┐
│   RDS    │   │ElastiCache│  │    S3    │
│Postgres  │   │  Redis    │  │Documents │
│Multi-AZ  │   │ Cluster   │  │KMS-enc   │
└──────────┘   └──────────┘  └──────────┘
```

### 10.2 Kubernetes Resources

Each service has:
- `Deployment` with `PodDisruptionBudget`
- `HorizontalPodAutoscaler` (CPU + custom metrics)
- `Service` + `Ingress`
- `ConfigMap` for non-sensitive config
- `ExternalSecret` (AWS Secrets Manager integration)
- Resource requests/limits defined
- Liveness + readiness probes

### 10.3 Environments

| Environment | Purpose | Database |
|-------------|---------|---------|
| `dev` | Local development | Docker Compose |
| `staging` | Integration testing | RDS (separate instance) |
| `production` | Live traffic | RDS Multi-AZ |

---

## 11. Domain Sequence Diagrams

### 11.1 Checkout Flow

```
Consumer → MerchantSite → Pagaê API
                │
                │ POST /checkout/create
                ▼
          CheckoutService
                │
                ├── RiskEngine.score(device, session)    [<50ms]
                ├── CreditEngine.decide(cpf, amount)     [<400ms]
                │     ├── BureauProvider.score(cpf)
                │     ├── OpenFinanceProvider.analyze(cpf)
                │     └── InternalMLProvider.predict(features)
                │
                ├── [APPROVED] LedgerService.record(checkout_journal)
                ├── [APPROVED] PaymentService.create_settlement(merchant)
                ├── [APPROVED] InstallmentService.schedule(installments)
                ├── [APPROVED] NotificationService.send_confirmation(consumer)
                │
                └── [DENIED] NotificationService.send_denial(consumer)
                
          return CheckoutSession{status, qr_codes[]}
                │
                ▼
        Consumer pays installment 1 via Pix QR Code
                │
          PixWebhook (provider → Pagaê)
                │
          PaymentService.process_payment(pix_event)
                │
                ├── InstallmentService.mark_paid(installment_1)
                ├── LedgerService.record(payment_journal)
                └── NotificationService.send_receipt(consumer)
```

### 11.2 Collections Flow

```
Celery Beat (daily 8:00 BRT)
      │
      ▼
CollectionService.check_overdue()
      │
      ├── Query installments where due_date < today AND status = PENDING
      │
      ├── For each overdue installment:
      │     ├── DPD 1-3:   Send WhatsApp reminder
      │     ├── DPD 4-7:   Send email + WhatsApp
      │     ├── DPD 8-14:  Assign to collection agent
      │     ├── DPD 15-29: Escalate + suspend customer limit
      │     ├── DPD 30-89: Send to external collection partner
      │     └── DPD 90+:   Write-off provision, credit bureau negative
      │
      └── Retry payment:
            └── PaymentService.retry_pix(installment)
                  ├── Generate new QR code
                  └── NotificationService.send_pix_qr(consumer)
```

---

## 12. Technology Decisions — ADRs

### ADR-001: Modular Monolith First
**Decision:** Start as Django monolith with internal module boundaries.  
**Rationale:** Team velocity, domain discovery, operational simplicity.  
**Consequences:** Extraction effort when a domain becomes independently scalable.

### ADR-002: UUID Primary Keys
**Decision:** All database primary keys are UUIDs (v4).  
**Rationale:** No sequential ID exposure in APIs, safe for distributed environments.  
**Consequences:** Slightly larger index size vs. bigint.

### ADR-003: Centavos for Currency
**Decision:** All monetary amounts stored as integers (centavos).  
**Rationale:** Eliminates floating-point precision errors in financial calculations.  
**Consequences:** All API inputs/outputs express amounts in centavos (documented).

### ADR-004: Double-Entry Ledger — Append Only
**Decision:** Financial state derived from append-only journal entries.  
**Rationale:** Full auditability, regulatory compliance, reconstructible state.  
**Consequences:** Queries require aggregation; balance views cached in Redis.

### ADR-005: Multi-Provider Payment Abstraction
**Decision:** Abstract all payment providers behind a single interface.  
**Rationale:** No provider lock-in, failover capability, cost optimization.  
**Consequences:** Provider-specific features require interface extension.

### ADR-006: Celery for Async Work
**Decision:** All async work (collections, notifications, reconciliation) via Celery + Redis.  
**Rationale:** Native Django integration, monitoring support, retry semantics.  
**Consequences:** Redis single point of failure — mitigated by Redis Sentinel/Cluster.

---

*Next: [User Journeys →](journeys.md)*
