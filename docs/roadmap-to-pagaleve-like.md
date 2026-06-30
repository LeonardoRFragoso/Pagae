# Roadmap: do Fundo Atual ao Produto Mínimo PagaLeve-like

> **Status atual:** Fase 1 (Foundation) finalizada. Backend roda localmente, migrations criadas, 51 testes passando, cobertura 85%.
> **Objetivo do documento:** mapear o caminho curto do estado atual até um produto mínimo funcionalmente comparável ao PagaLeve.

---

## O que já existe (Fase 1 — Foundation)

- `accounts` — registro, login JWT, refresh, logout, perfil.
- `customers` — perfil de consumidor, CPF, endereço, limites (stub), KYC stub.
- `merchants` — perfil de lojista, CNPJ, API keys, autenticação por API key.
- Infra local: Docker Compose, PostgreSQL, Redis, Celery, Django, DRF.
- Testes automatizados com cobertura ≥ 80%.

---

## Fase 2 — Motor BNPL (mínimo para parecer com PagaLeve)

**Meta:** um checkout funcional do início ao fim: lojista cria sessão, consumidor aprova, paga a 1ª parcela via Pix e o lojista recebe.

### 2.1 `checkout` app

- Modelo `CheckoutSession`.
- Endpoint: `POST /api/v1/checkout/create` (autenticado por API key do lojista).
- Payload: `merchant_order_id`, `customer` (cpf/email/phone), `total_amount`, `installment_count` (4 ou 12).
- Resposta: `status`, `schedule`, `qr_code` da 1ª parcela, `expires_at`.

### 2.2 `payments` app — Pix + parcelas

- Modelo `Installment` (cronograma de vencimentos).
- Modelo `PixCharge` (QR code da Celcoin vinculado a uma parcela).
- Integração **Celcoin**: gerar QR code dinâmico (QRDN) e receber webhook de pagamento.
- Webhook receiver: validar assinatura, marcar parcela como `paid`, liberar próximo QR code.

### 2.3 `credit` engine (pode viver dentro de `checkout`)

- Regra baseada em score Serasa (stub até contrato real).
- Velocity check no Redis (máx. 2 pedidos/dia por CPF).
- Denylist interna.
- Aprovação/rejeição em < 500ms.
- Atualização de `approved_limit` e `used_limit` do `Customer`.

### 2.4 `ledger` app

- Modelo `LedgerEntry` (append-only, partida dobrada simples).
- Lançamentos na aprovação do checkout e no pagamento da parcela.
- Contas: `receivable`, `merchant_payable`, `mdr_revenue`, `cash`.

### 2.5 `settlements` app

- Modelo `Settlement` (repasse ao lojista D+1).
- Endpoint de acionamento manual (mais tarde vira Celery Beat).
- Integração Celcoin: Pix saque para a chave Pix do lojista.

### 2.6 `webhooks` app

- Modelo `WebhookDelivery`.
- Entrega assíncrona de eventos para o lojista via Celery.
- Eventos mínimos: `checkout.approved`, `installment.paid`, `settlement.completed`.

### 2.7 `admin` melhorado

- Lista/edição de `CheckoutSession`, `Installment`, `PixCharge`, `Settlement`, `LedgerEntry`.
- Ações: reenviar webhook, reprocessar pagamento, suspender cliente.

**Entregável da Fase 2:** API completa de checkout → Pix → parcelamento → repasse. Sem frontend, sem cobrança automática de atraso.

---

## Fase 3 — Ops e canais de comunicação

**Meta:** o produto opera sozinho por dias sem intervenção manual.

### 3.1 `collections` app

- Celery Beat: job diário para calcular `days_past_due`.
- Regras por faixa de atraso (DPD 1, 3, 7, 15, 30).
- Suspensão automática de limite em DPD 7.
- Geração de novo QR code para parcelas atrasadas (juros no MVP: stub).

### 3.2 `notifications` app

- Modelo `Notification`.
- Integração **Brevo** para e-mail (templates básicos).
- Integração **Z-API** para WhatsApp (lembretes de vencimento).

### 3.3 KYC real

- Integração **CAF.io**: OCR de documento + liveness + validação de CPF.
- Webhook CAF para aprovar/rejeitar KYC.
- Armazenar imagens em S3 (MinIO local / Spaces prod).

---

## Fase 4 — Frontends mínimos

**Meta:** lojista e consumidor conseguem usar sem chamar a API manualmente.

### 4.1 Merchant Portal (Vue 3 + Vite + Tailwind)

- Login com JWT.
- Dashboard: GMV, taxa de aprovação, parcelas pendentes.
- Tabela de transações e detalhe da transação.
- Tabela de repasses.
- Configuração de webhook URL + secret.
- Tela de API keys.

### 4.2 Customer Portal (Vue 3)

- Login via OTP no celular (ou e-mail/senha no MVP).
- Home: limite disponível, próximos pagamentos.
- Lista de compras e detalhe de parcelas.
- Botão "pagar agora" para parcelas pendentes/atrasadas.

### 4.3 Checkout embarcável (javascript snippet)

- Script que o lojista coloca no checkout do e-commerce.
- Abre modal do Pagaê para escolher parcelamento e pagar via Pix.

---

## Fase 5 — Produção e integrações comerciais

**Meta:** primeiro lojista real processando vendas.

- Deploy na DigitalOcean (VPS + managed Postgres + managed Redis).
- Nginx + Let's Encrypt + Gunicorn + Celery worker + Celery Beat.
- CI/CD com GitHub Actions.
- Cloudflare (DNS + proxy + WAF).
- Backups diários do Postgres para S3.
- Sentry + UptimeRobot.
- Guia de integração + Postman collection.
- Plugin WooCommerce simples (PHP).
- App Nuvemshop (ou instruções de integração via API).

---

## Ordem de prioridade para começar amanhã

Se quiser um produto mínimo PagaLeve-like, comece na seguinte ordem:

1. **`checkout` app** — sem isso não existe produto.
2. **`payments` + Celcoin Pix** — sem pagamento não fecha o loop.
3. **`credit` engine + Serasa stub** — sem crédito não é BNPL.
4. **`ledger` + `settlements`** — sem repasse o lojista não tem motivo para usar.
5. **`webhooks`** — para o lojista reagir a eventos em tempo real.
6. **Merchant Portal** — para o lojista acompanhar sem Postman.
7. **Customer Portal / checkout embarcável** — para o consumidor final.
8. **Cobrança + notificações** — para operar sem manual.
9. **KYC real + produção** — para ficar regulado e escalável.

---

## Estimativa de esforço (revisada)

| Fase | Escopo | Estimativa |
|------|--------|------------|
| Fase 1 | Foundation | ✅ Concluída |
| Fase 2 | Motor BNPL + Pix + ledger + settlement | 3–4 semanas |
| Fase 3 | Cobrança + notificações + KYC real | 2–3 semanas |
| Fase 4 | Merchant Portal + Customer Portal + checkout embarcável | 4–6 semanas |
| Fase 5 | Produção + plugins + integrações comerciais | 2–3 semanas |
| **Total** | Produto mínimo PagaLeve-like | **11–16 semanas** (1 desenvolvedor solo) |

---

## O que NÃO deve entrar no MVP mínimo

Para não alongar o prazo:

- App nativo iOS/Android.
- Cartão de crédito como meio de pagamento.
- Modelo próprio de SCD/FIDC (usar parceiro SCD).
- ML de scoring (manter regras simples).
- Anti-fraude terceirizado (usar velocity + denylist interna).
- Marketplace de lojistas.
- Cashback/rewards.
- Conciliação bancária automática avançada.

---

## Próximo passo sugerido

Implementar a **Fase 2** começando pelo app `checkout` e pela integração com Celcoin em sandbox. Isso já permite fazer uma venda de ponta a ponta (checkout → Pix → confirmação → repasse stub).
