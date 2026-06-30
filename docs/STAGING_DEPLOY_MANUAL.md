# Guia de Deploy Manual de Staging — Pagaê

> Este guia deve ser executado por quem tem acesso às contas do Railway e Vercel.
> O assistente não tem acesso direto a essas plataformas, portanto o deploy real deve
> ser feito manualmente seguindo os passos abaixo.

## 1. Pré-requisitos

- Conta no Railway (https://railway.app) com acesso ao GitHub `LeonardoRFragoso/Pagae`.
- Conta na Vercel (https://vercel.com) com acesso ao mesmo repositório.
- Repositório local na branch `main` e commit `654af20` (ou superior).
- GitHub Actions passando no último push.

## 2. Criar banco e fila no Railway

1. No projeto Railway, clique em **New** → **Database** → **Add PostgreSQL**.
   - Anote a variável `DATABASE_URL` que o Railway gera.
2. Clique em **New** → **Database** → **Add Redis**.
   - Anote a variável `REDIS_URL`.

## 3. Gerar SECRET_KEY

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

Anote o valor.

## 4. Criar serviço backend web

1. No Railway, **New** → **GitHub Repo** → selecione `LeonardoRFragoso/Pagae`.
2. Configure:
   - **Root Directory:** `backend`
   - **Builder:** Docker (ou `railway.json` será detectado)
   - **Dockerfile:** `backend/Dockerfile`
   - **Start Command:** `/app/docker/start.sh`
   - **Healthcheck Path:** `/api/v1/health/`
   - **Port:** `$PORT` (Railway define automaticamente)
3. Vá em **Variables** e adicione todas as variáveis do próximo passo.
4. Depois de provisionado, Railway gera uma URL pública (ex: `https://pagae-backend-web.up.railway.app`).
   Anote como `BACKEND_URL` e use no `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, etc.

## 5. Variáveis de ambiente do backend

Adicione no Railway (escopo do serviço `web`, e depois replique para `worker` e `beat`):

```text
DJANGO_SETTINGS_MODULE=config.settings.staging
SECRET_KEY=<valor gerado no passo 3>
DEBUG=False
VERSION=1.0.0

DATABASE_URL=<valor do PostgreSQL Railway>
REDIS_URL=<valor do Redis Railway>
CELERY_BROKER_URL=<REDIS_URL>/1
CELERY_RESULT_BACKEND=<REDIS_URL>/2

PAYMENT_PROVIDER=sandbox

ALLOWED_HOSTS=<domínio Railway, ex: pagae-backend-web.up.railway.app>
CORS_ALLOWED_ORIGINS=<URL Vercel, ex: https://pagae-frontend.vercel.app>
CSRF_TRUSTED_ORIGINS=<URL Vercel, ex: https://pagae-frontend.vercel.app>
FRONTEND_URL=<URL Vercel>
BACKEND_URL=<URL Railway>

USE_X_FORWARDED_HOST=True
USE_X_FORWARDED_SSL=True
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=False

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

## 6. Criar serviços Celery worker e beat

1. **New** → **GitHub Repo** → mesmo repositório.
2. **Root Directory:** `backend`
3. **Dockerfile:** `backend/Dockerfile`
4. **Start Command:**
   - worker: `celery -A config.celery worker --loglevel=info`
   - beat: `celery -A config.celery beat --loglevel=info`
5. Copie as mesmas variáveis de ambiente do serviço `web` (exceto `PORT`).
6. Não expõem portas públicas.

## 7. Criar superusuário de staging

No Railway, abra o console do serviço `web` e execute:

```bash
python manage.py createsuperuser
```

Preencha username/e-mail e senha. **Não compartilhe a senha.**

## 8. Criar projeto Vercel

1. Importe `LeonardoRFragoso/Pagae`.
2. **Root Directory:** `frontend/merchant-portal`
3. **Framework Preset:** Vite
4. **Build Command:** `npm run build`
5. **Output Directory:** `dist`
6. Em **Environment Variables**, adicione:

```text
VITE_API_BASE_URL=<URL Railway do backend>
```

7. Deploy.

## 9. Validar backend online

```bash
export BACKEND_URL="https://<seu-backend>.up.railway.app"

curl -sf "${BACKEND_URL}/api/v1/health/"
```

Resultado esperado:

```json
{
  "status": "ok",
  "database": "ok",
  "redis": "ok",
  "payment_provider": "sandbox",
  "version": "1.0.0"
}
```

## 10. Validar endpoints principais

```bash
export BACKEND_URL="https://<seu-backend>.up.railway.app"

# 1. Registro
register=$(curl -sf -X POST "${BACKEND_URL}/api/v1/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{"email":"lojista-staging@pagae.local","password":"SenhaForte123!","role":"merchant_owner","first_name":"Loja","last_name":"Demo"}')

echo "register: $register"

# 2. Login
login=$(curl -sf -X POST "${BACKEND_URL}/api/v1/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"email":"lojista-staging@pagae.local","password":"SenhaForte123!"}')
ACCESS=$(echo "$login" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access'])")

echo "login ok"

# 3. Perfil do lojista
curl -sf "${BACKEND_URL}/api/v1/merchants/me/" -H "Authorization: Bearer ${ACCESS}"

# 4. Criar API key
key_response=$(curl -sf -X POST "${BACKEND_URL}/api/v1/merchants/api-keys/" \
  -H "Authorization: Bearer ${ACCESS}" \
  -H "Content-Type: application/json" \
  -d '{"environment":"sandbox"}')
API_KEY=$(echo "$key_response" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['full_key'])")

echo "api key criada"

# 5. Criar cliente
CUST=$(curl -sf -X POST "${BACKEND_URL}/api/v1/customers/" \
  -H "Authorization: Bearer ${ACCESS}" \
  -H "Content-Type: application/json" \
  -d '{"cpf":"12345678909","full_name":"Cliente Teste Staging","email":"cliente-staging@pagae.local","phone":"11999999999","monthly_income":500000}')

echo "customer: $CUST"

# 6. Criar pedido
order=$(curl -sf -X POST "${BACKEND_URL}/api/v1/orders/" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"customer":{"cpf":"12345678909"},"total_amount":30000,"installment_count":3,"merchant_order_id":"PEDIDO-STAGING-001","description":"Pedido sandbox staging Pagaê"}')

echo "order: $order"

# 7. Criar checkout
order_id=$(echo "$order" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")
checkout=$(curl -sf -X POST "${BACKEND_URL}/api/v1/checkout/" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"order_id\":\"${order_id}\"}")

checkout_id=$(echo "$checkout" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")
txid=$(echo "$checkout" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['txid'])")

echo "checkout_id: $checkout_id"
echo "txid: $txid"

# 8. Checkout público
curl -sf "${BACKEND_URL}/api/v1/checkout/${checkout_id}/"

# 9. Simular pagamento
curl -sf -X POST "${BACKEND_URL}/api/v1/payments/simulate/" \
  -H "Content-Type: application/json" \
  -d "{\"txid\":\"${txid}\"}"

# 10. Dashboard
curl -sf "${BACKEND_URL}/api/v1/merchants/dashboard/" -H "Authorization: Bearer ${ACCESS}"
```

> Não inclua os tokens reais no relatório final.

## 11. Validar frontend

1. Abra a URL Vercel.
2. Faça login com o lojista criado.
3. Verifique se o dashboard carrega.
4. Confirme que as chamadas de API usam `VITE_API_BASE_URL` (aba Network do DevTools).

## 12. Validar segurança

- `DEBUG=False` no painel Railway.
- `ALLOWED_HOSTS` contém apenas o domínio Railway.
- `CORS_ALLOWED_ORIGINS` e `CSRF_TRUSTED_ORIGINS` contêm apenas o domínio Vercel.
- `PAYMENT_PROVIDER=sandbox`.
- `SESSION_COOKIE_SECURE=True` e `CSRF_COOKIE_SECURE=True`.
- Logs do Railway não mostram SECRET_KEY, DATABASE_URL, tokens, CPF, CNPJ ou API keys.
- Rate limiting: teste 6+ requisições de login em 1 minuto e verifique HTTP 429.

## 13. Atualizar documentação

Após obter as URLs reais, edite:

- `docs/DEPLOYMENT.md`
- `docs/STAGING_CHECKLIST.md`
- `README.md`

Adicione a seção:

```markdown
## Ambiente de Staging

- **Backend:** https://<seu-backend>.up.railway.app
- **Frontend:** https://<seu-frontend>.vercel.app
- **Healthcheck:** https://<seu-backend>.up.railway.app/api/v1/health/
- **Railway services:** pagae-backend-web, pagae-celery-worker, pagae-celery-beat, PostgreSQL, Redis
- **Vercel project:** pagae-frontend
```

Não inclua segredos.

## 14. Commitar ajustes

Se precisar corrigir código, use:

```bash
git add -A
git commit -m "fix: stabilize Pagae staging deployment"
git push origin main
```

## 15. Checklist final

- [ ] Backend online no Railway e healthcheck retorna `ok`.
- [ ] Frontend online na Vercel.
- [ ] PostgreSQL e Redis conectados.
- [ ] Celery worker e beat online.
- [ ] Superusuário criado.
- [ ] Fluxo MVP funcionou em staging com `sandbox`.
- [ ] CI/CD passando no GitHub Actions.
- [ ] Documentação atualizada com URLs reais.
- [ ] Nenhuma credencial sensível exposta.
