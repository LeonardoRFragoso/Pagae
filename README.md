# Pagaê

SaaS brasileiro de **checkout Pix parcelado** para pequenos e médios lojistas.

O lojista cria um link de pagamento, o cliente informa seus dados, escolhe o número de parcelas e paga a primeira via Pix. As demais parcelas são geradas e acompanhadas automaticamente. No MVP o lojista recebe conforme as parcelas são pagas — sem promessa de antecipação de recebíveis e sem assumir o risco de inadimplência do cliente.

---

## Stack

- **Backend:** Python 3.13, Django 5, Django REST Framework, JWT (`rest-framework-simplejwt`), Celery, pytest
- **Banco de dados:** PostgreSQL 16
- **Cache / fila:** Redis 7
- **Frontend:** Vue 3 + Pinia + Vue Router + Tailwind CSS + Vite
- **Infra local:** Docker + Docker Compose
- **Deploy:** Railway (backend, worker, beat, Postgres, Redis), Vercel (frontend)
- **CI/CD:** GitHub Actions (lint, testes, migrações, build backend e frontend)
- **Pagamentos:** camada abstrata `PaymentProvider` com provider `sandbox` (padrão) e integração de exemplo para Celcoin; pronto para Asaas, Mercado Pago, Efí, Iugu, OpenPix etc.
- **Documentação:** OpenAPI/Swagger em `/api/docs/`

---

## Arquitetura

Monolito Django com apps de domínio isolados:

```
backend/apps/
├── accounts/          # autenticação JWT e usuários
├── merchants/         # perfil do lojista, API keys, dashboard, webhooks
├── customers/         # perfil do cliente, limites e KYC
├── checkout/          # pedidos (Order), sessões de checkout e análise de risco
├── payments/          # parcelas (Installment), cobranças Pix e transações genéricas
├── collections/       # acompanhamento de atrasos e lembretes
├── ledger/            # escrituração contábil simplificada
├── settlements/       # repasses ao lojista (sem antecipação no MVP)
├── webhooks/          # entrega de eventos aos lojistas
└── notifications/     # notificações (e-mail/WhatsApp - stubs)
```

Princípios adotados:

- **Provider-agnostic payments:** toda comunicação com gateways passa pela interface `PaymentProvider`.
- **Repository pattern:** acesso a dados centralizado em `repositories.py` por app.
- **Services:** lógica de negócio desacoplada de views e models.
- **Eventos assíncronos:** webhooks e notificações via Celery.
- **Risco rule-based:** análise de crédito com regras simples, armazenando motivos de aprovação/reprovação.

---

## Como rodar localmente

### Pré-requisitos

- Docker + Docker Compose
- Git

### 1. Clone e suba os serviços

```bash
git clone https://github.com/LeonardoRFragoso/Pagae.git
make setup
```

Ou, manualmente:

```bash
cp backend/.env.example backend/.env
docker compose up -d
```

### 2. Aplique as migrações e crie um superusuário

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

### 3. Acesse

- API REST: http://localhost:8000/api/v1/
- Swagger / OpenAPI: http://localhost:8000/api/docs/
- Portal do lojista: http://localhost:5173
- Admin Django: http://localhost:8000/django-admin/
- Healthcheck: http://localhost:8000/api/v1/health/

### Scripts úteis

Dentro de `backend/`:

```bash
make up              # sobe todos os serviços
make down            # para tudo
make migrate         # roda migrações
make test            # roda pytest
make lint            # ruff
make format          # black
make shell           # Django shell_plus

make prod-build      # build da imagem de produção
make prod-up         # sobe ambiente de produção local
make prod-check      # valida healthcheck e deploy check
make frontend-build  # build do portal Vue
```

---

## Deploy

Veja o passo a passo completo em `docs/DEPLOYMENT.md`, a checklist de lançamento em `docs/STAGING_CHECKLIST.md` e o guia de execução manual em `docs/STAGING_DEPLOY_MANUAL.md`.

---

## Roadmap resumido

1. **MVP (atual):** cadastro de lojista, criação de pedidos, checkout Pix parcelado sandbox, dashboard, webhooks, acompanhamento de atrasos.
2. **Integração real de Pix:** implementar provider Celcoin/Asaas/Efí com credenciais reais.
3. **KYC automatizado:** integração com CAF.io ou similar para validação de identidade.
4. **Antecipação de recebíveis:** parceria financeira para adiantar valores ao lojista (sem assumir risco no MVP).
5. **APIs avançadas:** split, reembolso, ajustes de risco, app mobile.

Veja detalhes em `docs/ROADMAP.md`.

---

## Licença e disclaimer

Este projeto é um protótipo/MVP de software financeiro brasileiro. Não é uma instituição financeira. O Pagaê não assume risco de inadimplência do consumidor nesta fase e não oferece antecipação de recebíveis. Marcas, textos e fluxos são originais e não copiam concorrentes.

---

## Documentação técnica

- `docs/ARCHITECTURE.md`
- `docs/API.md`
- `docs/ROADMAP.md`
- `docs/SECURITY.md`
- `docs/BUSINESS_RULES.md`
- `docs/DEPLOYMENT.md`
- `docs/STAGING_CHECKLIST.md`
