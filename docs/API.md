# API do Pagaê

Base URL: `http://localhost:8000/api/v1/`

Documentação interativa: `http://localhost:8000/api/docs/` (Swagger/OpenAPI).

## Healthcheck

`GET /api/v1/health/`

Endpoint público para load balancers e monitoramento. Retorna:

```json
{
  "status": "ok",
  "database": "ok",
  "redis": "ok",
  "payment_provider": "sandbox",
  "version": "1.0.0"
}
```

Retorna HTTP 503 caso PostgreSQL ou Redis estejam indisponíveis.

## Autenticação

### JWT (portal do lojista)

- `POST /api/v1/auth/register/` — cria usuário.
- `POST /api/v1/auth/login/` — retorna `access` e `refresh`.
- `POST /api/v1/auth/refresh/` — renova access token.
- `POST /api/v1/auth/logout/` — invalida refresh token.
- `GET /api/v1/auth/me/` — dados do usuário logado.

Envie `Authorization: Bearer <access>` em todas as requisições autenticadas.

### API Key (integração servidor-a-servidor)

Crie uma chave em `POST /api/v1/merchants/api-keys/`. Use:

```bash
curl -X POST http://localhost:8000/api/v1/checkout/ \
  -H "Authorization: Bearer pk_test_..." \
  -H "Content-Type: application/json" \
  -d '{...}'
```

## Lojista

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/merchants/` | Cria perfil do lojista |
| GET | `/api/v1/merchants/me/` | Perfil do lojista logado |
| GET | `/api/v1/merchants/dashboard/` | Métricas de vendas e parcelas |
| GET | `/api/v1/merchants/transactions/` | Lista de pedidos/checkouts |
| GET | `/api/v1/merchants/transactions/<id>/` | Detalhes de um pedido com parcelas |
| GET | `/api/v1/merchants/settlements/` | Repasses ao lojista |
| GET/POST | `/api/v1/merchants/api-keys/` | Gerencia chaves de API |
| GET/POST | `/api/v1/merchants/webhook/` | Configura e testa webhook |

## Cliente

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/customers/` | Cria perfil de cliente (autenticado) |
| GET | `/api/v1/customers/me/` | Dados do cliente logado |

## Pedidos (Order)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/orders/` | Cria um pedido (API key) |
| GET | `/api/v1/orders/list/` | Lista pedidos do lojista (JWT) |
| GET | `/api/v1/orders/<id>/` | Detalhes de um pedido |

Payload de criação:

```json
{
  "customer": {"cpf": "12345678909"},
  "total_amount": 15000,
  "installment_count": 3,
  "merchant_order_id": "PEDIDO-123"
}
```

## Checkout

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/checkout/` | Cria sessão de checkout a partir de pedido ou dados completos |
| GET | `/api/v1/checkout/<id>/` | Resumo público do checkout |

Exemplo de resposta de `POST /api/v1/checkout/`:

```json
{
  "id": "uuid",
  "status": "approved",
  "decision": "approve",
  "denial_reason": "",
  "total_amount": 15000,
  "installment_count": 3,
  "installment_amount": 5000,
  "schedule": [
    {"number": 1, "amount": 5000, "due_date": "2026-07-15", "status": "pending"}
  ],
  "txid": "abc123",
  "qr_code": "000201...",
  "pix_code": "pix:abc123",
  "expires_at": "2026-06-30T03:12:00Z"
}
```

## Pagamentos (sandbox)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/payments/simulate/` | Simula o pagamento de uma cobrança Pix |
| POST | `/api/v1/webhooks/sandbox/` | Recebe webhook fake de pagamento |

Payload de simulação:

```json
{"txid": "abc123", "paid_at": "2026-06-30T12:00:00Z"}
```

## Webhooks enviados aos lojistas

Eventos entregues em `POST <webhook_url>` configurado pelo lojista:

- `checkout.approved`
- `installment.paid`
- `installment.overdue`
- `webhook.test`

Cada payload contém `event_type`, `timestamp` e `data`.

## Códigos de erro

A API usa um handler padronizado:

```json
{
  "error": {
    "code": "customer_not_found",
    "message": "Customer not found."
  }
}
```

Códigos comuns: `customer_not_found`, `invalid_api_key`, `merchant_not_active`, `amount_exceeds_limit`, `transaction_not_found`, `forbidden`.
