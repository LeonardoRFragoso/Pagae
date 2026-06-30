# Checklist de Staging — Pagaê

Use este checklist antes de promover o staging para produção.

## Infraestrutura

- [ ] Serviço `web` no Railway criado com Dockerfile `backend/Dockerfile`.
- [ ] Serviço `worker` no Railway criado com o mesmo Dockerfile.
- [ ] Serviço `beat` no Railway criado com o mesmo Dockerfile.
- [ ] PostgreSQL provisionado no Railway e `DATABASE_URL` configurada.
- [ ] Redis provisionado no Railway e `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` configuradas.
- [ ] Frontend importado no Vercel com root directory `frontend/merchant-portal`.
- [ ] Variável `VITE_API_BASE_URL` aponta para o backend de staging.

## Variáveis de ambiente

- [ ] `DJANGO_SETTINGS_MODULE=config.settings.staging` (ou `production`).
- [ ] `SECRET_KEY` gerado com 50+ caracteres aleatórios.
- [ ] `DEBUG=False`.
- [ ] `ALLOWED_HOSTS` preenchido com o domínio do backend.
- [ ] `CORS_ALLOWED_ORIGINS` preenchido com o domínio do frontend.
- [ ] `CSRF_TRUSTED_ORIGINS` preenchido com o domínio do frontend.
- [ ] `FRONTEND_URL` e `BACKEND_URL` configurados.
- [ ] `PAYMENT_PROVIDER=sandbox` (ou `celcoin` com credenciais completas).

## Segurança

- [ ] `SECURE_SSL_REDIRECT` configurado conforme necessidade (cuidado com loops de redirect).
- [ ] `USE_X_FORWARDED_SSL=True` no Railway/Vercel.
- [ ] `SECURE_HSTS_SECONDS` configurado: `0` em staging, `31536000` em produção.
- [ ] `SESSION_COOKIE_SECURE=True` e `CSRF_COOKIE_SECURE=True` em produção.
- [ ] `X_FRAME_OPTIONS=DENY`.
- [ ] `ALLOWED_HOSTS` não contém `*` ou `localhost`.
- [ ] CORS/CSRF não usa `CORS_ALLOW_ALL_ORIGINS=True`.

## Validação funcional

- [ ] `GET /api/v1/health/` retorna HTTP 200 e `status: ok`.
- [ ] `python manage.py check --deploy` não apresenta erros críticos.
- [ ] Registro de lojista (`POST /api/v1/auth/register/`) funciona.
- [ ] Login de lojista (`POST /api/v1/auth/login/`) funciona.
- [ ] Criação de API key funciona.
- [ ] Criação de pedido (`POST /api/v1/orders/`) funciona com API key.
- [ ] Criação de checkout (`POST /api/v1/checkout/`) funciona.
- [ ] Acesso público ao checkout (`GET /api/v1/checkout/<id>/`) funciona.
- [ ] Simulação de pagamento (`POST /api/v1/payments/simulate/`) atualiza o dashboard.
- [ ] Webhook sandbox (`POST /api/v1/webhooks/sandbox/`) funciona.
- [ ] Frontend builda sem erros (`make frontend-build`).
- [ ] Frontend consegue fazer login e acessar o dashboard.

## CI/CD

- [ ] Build do backend passa no GitHub Actions.
- [ ] Build do frontend passa no GitHub Actions.
- [ ] Testes do backend passam no CI.
- [ ] Lint do backend passa no CI.

## Go-live

- [ ] Banco de dados de staging não contém dados de produção reais.
- [ ] Domínios configurados e DNS apontando para Railway/Vercel.
- [ ] Certificados SSL ativos (Railway/Vercel gerenciam).
- [ ] Sentry configurado opcionalmente (`SENTRY_DSN`).
- [ ] AWS S3 configurado opcionalmente para arquivos de mídia (`AWS_STORAGE_BUCKET_NAME`, etc.).
- [ ] Documento de incident response e contatos de emergência definidos.

## Após o deploy

- [ ] Verificar logs de startup do serviço `web`.
- [ ] Confirmar que `worker` e `beat` estão conectados ao Redis.
- [ ] Testar o fluxo completo de pagamento no ambiente de staging.
- [ ] Revisar alertas de segurança e rate limiting em endpoints sensíveis.
