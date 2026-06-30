# Arquitetura do Pagaê

## Visão geral

O Pagaê é um monolito Django com frontend Vue, projetado para ser executado em um único VPS com Docker. A arquitetura prioriza simplicidade operacional e modularidade de domínio, deixando portas abertas para extrair serviços quando o volume justificar.

## Camadas

```
┌─────────────────────────────────────┐
│           Vue SPA                   │
│   merchant-portal + checkout        │
└──────────────┬──────────────────────┘
               │ HTTP/JSON
┌──────────────▼──────────────────────┐
│      Django REST Framework          │
│  apps: accounts, merchants,         │
│  customers, checkout, payments,     │
│  collections, ledger, settlements,  │
│  webhooks, notifications            │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  PostgreSQL  │  Redis  │  Celery     │
│   (dados)    │ (cache/fila)│ (jobs)  │
└─────────────────────────────────────┘
```

## Apps de domínio

- `accounts` — autenticação JWT e papel do usuário (cliente, lojista, operação).
- `merchants` — cadastro do lojista, chaves de API, dashboard, configuração de webhook.
- `customers` — dados do cliente, limites de crédito, KYC e status de bloqueio.
- `checkout` — `Order` (pedido criado pelo lojista), `CheckoutSession` (sessão pública), `RiskAnalysis` (decisão de risco com motivos).
- `payments` — `Installment` (parcela), `PixCharge` (cobrança Pix) e `PaymentTransaction` (registro genérico de transação por provider).
- `collections` — rotina diária de atrasos, suspensão de limite e reemissão de QR.
- `ledger` — lançamentos contábeis de recebível, MDR e a pagar ao lojista.
- `settlements` — repasses ao lojista. No MVP o repasse é feito manualmente, parcela a parcela.
- `webhooks` — fila de entrega de eventos com retry.
- `notifications` — stubs para e-mail e WhatsApp.

## Padrões de código

- **Repository:** cada app possui `repositories.py` com funções CRUD e queries frequentes.
- **Service:** `services.py` concentra a lógica de negócio, chamando repositories e integrações.
- **Provider:** integrações externas (Pix, e-mail, KYC) implementam uma interface simples, trocável por configuração.
- **Celery:** tarefas em `tasks.py` e agendamento em `config/settings/base.py` (`CELERY_BEAT_SCHEDULE`).

## Fluxo de uma venda parcelada

1. Lojista autentica com API key e chama `POST /api/v1/checkout/` (ou `POST /api/v1/orders/` seguido de checkout).
2. Backend cria um `Order` e uma `CheckoutSession`.
3. Motor de risco (`CreditEngine`) analisa CPF, telefone, limite, histórico de atraso e gera um `RiskAnalysis` com aprovação/reprovação e motivos.
4. Se aprovado, são criadas `Installment` e `PixCharge` (ou `PaymentTransaction` genérica) para cada parcela.
5. O cliente acessa o link público `/checkout/:id`, visualiza o resumo e paga a primeira parcela via Pix (sandbox).
6. O provider notifica via webhook ou a simulação marca a parcela como paga.
7. O `LedgerService` registra o recebível e o MDR.
8. O lojista acompanha tudo no dashboard e recebe o valor líquido conforme as parcelas são pagas.
9. A rotina Celery diária marca parcelas vencidas como `overdue` e suspende o limite do cliente.

## Integrações futuras

- **Pix:** a camada `PaymentProvider` permite trocar `sandbox` por `celcoin`, `asaas`, `mercado_pago`, `efi`, `iugu` ou `openpix` sem alterar o domínio.
- **KYC:** substituir o stub por CAF.io ou similar.
- **Notificações:** conectar Brevo (e-mail) e Z-API (WhatsApp).

## Escalabilidade

- O estado das cobranças Pix é transitório (o provider é a fonte da verdade), então a maior parte do banco é leitura/escrita simples.
- O cache Redis é usado para velocity de risco e sessões.
- Webhooks, notificações e conciliação são executados fora do request via Celery.
