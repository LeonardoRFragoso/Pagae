# Deploy do Pagaê

## Visão geral

- **Backend:** Django + Gunicorn, conteinerizado no Docker e hospedado no **Railway**.
- **Frontend:** Vue 3/Vite, hospedado no **Vercel**.
- **Banco de dados:** PostgreSQL (Railway).
- **Cache/fila:** Redis (Railway).
- **Workers assíncronos:** Celery worker e Celery beat (Railway).
- **CI/CD:** GitHub Actions (`.github/workflows/ci.yml`).

## Variáveis de ambiente obrigatórias

As variáveis devem ser configuradas no painel do Railway (backend) e Vercel (frontend).

### Backend

| Variável | Descrição | Exemplo staging |
|----------|-----------|-----------------|
| `DJANGO_SETTINGS_MODULE` | Módulo de settings | `config.settings.staging` |
| `SECRET_KEY` | Chave secreta longa e aleatória | `gerar 50+ caracteres` |
| `DEBUG` | `False` em staging/prod | `False` |
| `ALLOWED_HOSTS` | Domínios do backend | `api-staging.pagae.com.br` |
| `VERSION` | Versão da API | `1.0.0` |
| `DATABASE_URL` | PostgreSQL | `postgres://...` |
| `REDIS_URL` | Redis | `redis://...` |
| `CELERY_BROKER_URL` | Redis broker | `redis://.../1` |
| `CELERY_RESULT_BACKEND` | Redis result | `redis://.../2` |
| `CORS_ALLOWED_ORIGINS` | Origens do frontend | `https://staging.pagae.com.br` |
| `CSRF_TRUSTED_ORIGINS` | Mesmas origens do frontend | `https://staging.pagae.com.br` |
| `FRONTEND_URL` | URL pública do frontend | `https://staging.pagae.com.br` |
| `BACKEND_URL` | URL pública do backend | `https://api-staging.pagae.com.br` |
| `PAYMENT_PROVIDER` | `sandbox` por padrão | `sandbox` |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | Tempo do access token | `15` |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Tempo do refresh token | `7` |
| `DEFAULT_FROM_EMAIL` | Remetente de e-mails | `noreply@pagae.com.br` |
| `USE_X_FORWARDED_SSL` | `True` no Railway/Vercel | `True` |
| `SECURE_SSL_REDIRECT` | `True` em produção, `False` em staging se necessário | `False` |
| `SECURE_HSTS_SECONDS` | `0` em staging, `31536000` em produção | `0` |
| `SESSION_COOKIE_SECURE` | `True` em produção | `True` |
| `CSRF_COOKIE_SECURE` | `True` em produção | `True` |

### Frontend

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `VITE_API_BASE_URL` | URL pública do backend | `https://api-staging.pagae.com.br` |

## Railway — serviços

Crie quatro serviços no Railway usando o mesmo repositório:

1. **web** — Dockerfile `backend/Dockerfile`
   - Start command: `/app/docker/start.sh`
   - Healthcheck: `/api/v1/health/`
   - Porta: `$PORT`
2. **worker** — Dockerfile `backend/Dockerfile`
   - Start command: `celery -A config.celery worker --loglevel=info`
3. **beat** — Dockerfile `backend/Dockerfile`
   - Start command: `celery -A config.celery beat --loglevel=info`
4. **PostgreSQL** — provisionar pelo Railway.
5. **Redis** — provisionar pelo Railway.

Lembre-se de adicionar as variáveis de ambiente em cada serviço (ou no escopo compartilhado do Railway).

## Vercel — frontend

1. Importe o repositório.
2. Configure **Root Directory**: `frontend/merchant-portal`.
3. Configure **Build Command**: `npm run build`.
4. Configure **Output Directory**: `dist`.
5. Defina a variável `VITE_API_BASE_URL`.
6. O arquivo `vercel.json` já está no diretório do frontend.

## Local com ambiente de produção

Build e teste da imagem de produção:

```bash
make prod-build
make prod-up
make prod-check
```

Para parar:

```bash
make prod-down
```

## Pipeline CI/CD

O `.github/workflows/ci.yml` executa em cada push/PR para `main`:

1. Lint do backend (`ruff`).
2. `python manage.py check`.
3. Verificação de migrações pendentes.
4. Migrations e testes (`pytest`).
5. Build da imagem Docker do backend.
6. Build do frontend.

## Antes de liberar produção

Siga `docs/STAGING_CHECKLIST.md`.

## Notas de segurança

- `PAYMENT_PROVIDER=celcoin` só é permitido quando `CELCOIN_CLIENT_ID`,
  `CELCOIN_CLIENT_SECRET` e `CELCOIN_BASE_URL` estão preenchidos.
- Nunca faça deploy com `DEBUG=True` ou `SECRET_KEY` curto.
- Configure sempre `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` e `CSRF_TRUSTED_ORIGINS`.
- Habilite `SECURE_SSL_REDIRECT` e HSTS apenas quando o HTTPS estiver 100% funcional.
