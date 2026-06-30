# Phase 1 Implementation — Foundation

## Quick Start

```bash
cd backend
cp .env.example .env          # review and edit if needed
make setup                    # starts Docker, runs migrations
make logs                     # tail all service logs
```

Access:
- API: http://localhost:8000/api/v1/
- Docs: http://localhost:8000/api/docs/
- Admin: http://localhost:8000/django-admin/

---

## Project Structure

```
backend/
├── config/
│   ├── __init__.py           # Celery app wired here
│   ├── celery.py             # Celery configuration
│   ├── urls.py               # Root URL dispatcher
│   ├── wsgi.py
│   ├── asgi.py
│   └── settings/
│       ├── base.py           # Shared settings
│       ├── development.py    # DEBUG=True, console email, CORS open
│       ├── production.py     # SSL, S3, Sentry
│       └── testing.py        # In-memory cache, eager Celery, fast hasher
│
├── core/
│   ├── models.py             # BaseModel (UUID pk, created_at, updated_at)
│   ├── middleware.py         # CorrelationIdMiddleware, RequestLoggingMiddleware
│   ├── exceptions.py         # PagaeException hierarchy + custom DRF handler
│   ├── pagination.py         # StandardResultsPagination (enveloped response)
│   ├── logging.py            # JsonFormatter for structured logs
│   └── responses.py          # success(), created(), no_content() helpers
│
├── apps/
│   ├── accounts/             # Auth, User model, JWT
│   ├── customers/            # Consumer profile, KYC interface
│   └── merchants/            # Merchant profile, API keys, ApiKey auth
│
├── integrations/             # External API clients (Celcoin, Serasa, CAF) — Phase 2
├── tests/
│   ├── conftest.py           # Fixtures (api_client, users, customer, merchant)
│   ├── factories.py          # factory_boy factories for all models
│   ├── accounts/test_auth.py
│   ├── customers/test_customers.py
│   └── merchants/test_merchants.py
│
├── docker/
│   ├── Dockerfile            # Production image
│   ├── Dockerfile.dev        # Development image (runserver)
│   └── entrypoint.sh         # Wait-for-postgres + migrate
│
├── requirements/
│   ├── base.txt              # Django 5, DRF, SimpleJWT, psycopg2, Celery, Redis
│   ├── development.txt       # pytest, ruff, black, factory-boy, mypy
│   └── production.txt        # gunicorn, sentry-sdk, boto3, django-storages
│
├── docker-compose.yml        # web + celery + celery-beat + postgres + redis
├── Makefile                  # make up/down/migrate/test/lint/format
├── pyproject.toml            # ruff + black + pytest + mypy config
└── .pre-commit-config.yaml   # ruff + black + pre-commit-hooks
```

---

## Models

### User (`apps/accounts/models.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key, auto-generated |
| `email` | EmailField | Unique, used as USERNAME_FIELD |
| `phone` | CharField | Optional |
| `password` | (hashed) | Django default (PBKDF2) |
| `role` | CharField | `customer` \| `merchant_owner` \| `ops` \| `admin` |
| `is_active` | Boolean | Soft-disable |
| `is_staff` | Boolean | Django admin access |
| `created_at` | DateTime | Auto |
| `updated_at` | DateTime | Auto |

### Customer (`apps/customers/models.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `user` | FK → User | OneToOne |
| `cpf` | CharField(14) | Unique, indexed. **TODO: encrypt at rest pre-prod** |
| `full_name` | CharField | |
| `birth_date` | Date | Min age 18 enforced at serializer |
| `phone` | CharField | |
| `email` | EmailField | |
| `cep…state` | CharField | Address fields |
| `kyc_status` | CharField | `pending` \| `approved` \| `rejected` \| `manual_review` |
| `kyc_provider_id` | CharField | Reference ID from CAF |
| `serasa_score` | SmallInt | Populated at credit decision time |
| `risk_tier` | CharField | `new` \| `low` \| `medium` \| `high` |
| `approved_limit` | Integer | **Centavos** |
| `used_limit` | Integer | **Centavos** |
| `is_blocked` | Boolean | |
| `available_limit` | property | `approved_limit - used_limit` |

### Merchant (`apps/merchants/models.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `user` | FK → User | OneToOne |
| `cnpj` | CharField(14) | Unique, indexed. **TODO: encrypt at rest pre-prod** |
| `legal_name` | CharField | |
| `trade_name` | CharField | |
| `email`, `phone`, `website` | | |
| `pix_key` | CharField | For D+1 settlement |
| `mdr_rate` | Decimal(5,4) | Default 0.0700 (7%) |
| `settlement_days` | SmallInt | Default 1 (D+1) |
| `status` | CharField | `pending` \| `active` \| `suspended` \| `terminated` |
| `webhook_url`, `webhook_secret` | | |

### MerchantApiKey (`apps/merchants/models.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `merchant` | FK → Merchant | |
| `key_prefix` | CharField(20) | First 16 chars of key, stored plaintext for lookup |
| `key_hash` | CharField(255) | SHA-256 of full key. Full key is **never stored** |
| `name` | CharField | Human label |
| `environment` | CharField | `sandbox` \| `production` |
| `is_active` | Boolean | |
| `last_used` | DateTime | Updated on each successful auth |

---

## API Endpoints

Base URL: `/api/v1/`

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register/` | None | Register user (customer or merchant_owner) |
| POST | `/auth/login/` | None | Obtain access + refresh tokens |
| POST | `/auth/refresh/` | None | Rotate access token |
| POST | `/auth/logout/` | JWT | Blacklist refresh token |
| GET | `/auth/me/` | JWT | Current user info |

**Register response:**
```json
{
  "data": {
    "user": { "id": "uuid", "email": "...", "role": "customer" },
    "tokens": { "access": "...", "refresh": "..." }
  }
}
```

### Customers

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/customers/` | JWT (customer role) | Create customer profile |
| GET | `/customers/me/` | JWT | Get my profile |
| PUT | `/customers/me/` | JWT | Update address/contact |

**Immutable fields:** `cpf`, `full_name`, `birth_date`, `kyc_status`, `approved_limit`

### Merchants

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/merchants/` | JWT (merchant_owner role) | Register merchant |
| GET | `/merchants/me/` | JWT or API Key | Get my profile |
| POST | `/merchants/api-keys/` | JWT | Generate new API key |
| GET | `/merchants/api-keys/` | JWT | List active API keys |

**API key format:** `pk_live_<48 hex chars>` (production) / `pk_test_<48 hex chars>` (sandbox)  
**Important:** Full key shown only once at creation. Store it securely.

---

## Authentication Flows

### JWT (Consumers, Internal Users)

```
POST /auth/login   { email, password }
→ { access (15min), refresh (7 days) }

Header: Authorization: Bearer <access_token>

POST /auth/refresh { refresh }
→ { access }  (refresh is rotated + old is blacklisted)
```

### API Key (Merchants)

```
Header: Authorization: Bearer pk_live_<key>

Authenticated as: merchant user
auth token: MerchantApiKey instance (available as request.auth)
```

---

## Architecture Decisions

### ADR-01: Service Layer Pattern
All business logic lives in `services.py`. Views are thin — they validate input (serializer) and delegate to the service. Services are unit-testable without HTTP.

### ADR-02: Repository Pattern
All database queries are in `repositories.py`. Services never call ORM directly. This enables future swapping of data sources and easy mocking in tests.

### ADR-03: UUID Primary Keys
All models use UUID PKs. Prevents ID enumeration attacks and allows future distributed ID generation without collisions.

### ADR-04: Amounts in Centavos
All monetary values (`approved_limit`, `used_limit`, `mdr_amount`, etc.) are stored as integers (centavos). Zero floating-point arithmetic in financial logic.

### ADR-05: API Key Hashing
Full API keys are SHA-256 hashed before storage. The prefix (first 16 chars) is stored plaintext for O(1) prefix lookup before hash comparison. Keys are never logged.

### ADR-06: Settings Split
`base → development/production/testing` pyramid. `python-decouple` reads `.env`. `testing.py` uses in-memory cache, fast password hasher, and eager Celery to speed up tests.

### ADR-07: Custom Exception Hierarchy
`PagaeException` → `ValidationError | NotFoundError | ConflictError | ForbiddenError | ServiceUnavailableError`. The custom DRF exception handler in `core/exceptions.py` converts all exceptions to a consistent `{"error": {"code": "...", "message": "..."}}` envelope.

### ADR-08: Structured JSON Logging
`JsonFormatter` emits every log record as a single JSON line with `timestamp`, `level`, `logger`, `message`, plus contextual fields (`user_id`, `correlation_id`, `duration_ms`). Ready for Loki / CloudWatch ingestion.

### ADR-09: Correlation ID Middleware
Every request gets a `X-Correlation-ID` header (client-provided or auto-generated). The ID is attached to the request object, included in response headers, and can be injected into log records for request tracing.

---

## Running Tests

```bash
# via Docker (recommended)
make test

# with coverage HTML report
make test-cov

# specific test file
make test args="tests/accounts/test_auth.py -v"

# specific test class
make test args="tests/merchants/test_merchants.py::TestApiKeyGeneration -v"
```

Target: **≥ 80% coverage** on `apps/` and `core/`.

---

## Code Quality

```bash
make lint          # ruff check
make lint-fix      # ruff check --fix
make format        # black .
make format-check  # black --check .
make install       # install pre-commit hooks
```

Pre-commit hooks run `ruff` + `black` on every `git commit`.

---

## Environment Variables Reference

See `.env.example` for all variables. Critical ones for Phase 1:

| Variable | Default | Required |
|----------|---------|---------|
| `SECRET_KEY` | — | ✅ Production |
| `DB_HOST` | `localhost` | ✅ Docker overrides to `postgres` |
| `DB_NAME` | `pagae` | |
| `DB_USER` | `pagae` | |
| `DB_PASSWORD` | `pagae` | ✅ Production change |
| `REDIS_URL` | `redis://localhost:6379/0` | |
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | `15` | |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | `7` | |

---

## Phase 2 Readiness

The following interfaces are defined and stubbed, ready for Phase 2 implementation:

| Interface | Location | Phase 2 Implementation |
|-----------|----------|------------------------|
| `KYCProvider` | `apps/customers/kyc.py` | `CAFProvider` (CAF.io SDK) |
| `StubKYCProvider` | `apps/customers/kyc.py` | Active in dev/testing |
| `integrations/` package | `integrations/__init__.py` | `celcoin.py`, `serasa.py`, `caf.py` |
| `CELCOIN_*` settings | `config/settings/base.py` | Celcoin client in Phase 2 |
| `SERASA_*` settings | `config/settings/base.py` | Serasa client in Phase 2 |

---

## What's Next — Phase 2

1. Celcoin integration (`integrations/celcoin.py`) — Pix QR code generation
2. Serasa integration (`integrations/serasa.py`) — Score + negativado
3. CAF integration (`integrations/caf.py`) — Full KYC flow
4. `apps/checkout/` — Checkout session + credit decision engine
5. `apps/payments/` — Installments + Pix webhook handler
6. `apps/collections/` — Celery Beat overdue workflow
