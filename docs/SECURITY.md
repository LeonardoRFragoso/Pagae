# Segurança do Pagaê

## Autenticação e autorização

- **JWT:** tokens de acesso curto (15 min) e refresh de 7 dias, com rotação e blacklist.
- **API Keys:** prefixo visível e hash SHA-256 armazenado; a chave completa é exibida apenas no momento da criação.
- **Papéis:** `customer`, `merchant_owner`, `ops`, `admin`. Cada endpoint valida o papel necessário.
- **CORS:** restrito a origens configuradas em produção (`CORS_ALLOWED_ORIGINS`).

## Dados sensíveis

- CPF e CNPJ são armazenados em texto por enquanto (MVP), com comentários explícitos para criptografia em produção.
- Em produção recomenda-se:
  - Criptografia de campo (AES-256) para CPF/CNPJ/pix_key.
  - Hash de senhas com Argon2 (padrão Django).
  - Uso de KMS (AWS, GCP, HashiCorp Vault) para chaves.
- Nunca retornar dados sensíveis completos em endpoints públicos.

## Webhooks

- URL configurada pelo lojista deve usar HTTPS em produção.
- Payload assinado com `webhook_secret` (HMAC-SHA256 a ser implementado na Fase 2).
- Retry automático com backoff para entregas falhas; número máximo de tentativas antes de marcar como `exhausted`.

## Infraestrutura e hardening de deploy

- Docker Compose para desenvolvimento; Docker + Railway para produção inicial.
- Banco de dados PostgreSQL com backups automáticos.
- Redis isolado por slot (0=cache, 1=broker, 2=resultado).
- Secrets via variáveis de ambiente (python-decouple), nunca no código.
- Logs em JSON estruturados, sem expor senhas, tokens, CPF, CNPJ ou chaves de API.
- Settings separadas por ambiente: `development`, `staging`, `production`.
- Em produção: `DEBUG=False`, `ALLOWED_HOSTS` explícito, `SECURE_SSL_REDIRECT`,
  `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`,
  `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`, `X_FRAME_OPTIONS=DENY`,
  `SECURE_PROXY_SSL_HEADER` para Railway/Vercel.
- CORS/CSRF restritos a origens configuradas (`CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`).
- Rate limiting via DRF throttling: login (5/min), registro (5/h), checkout público (60/min),
  simulação de pagamento (20/min), webhook sandbox (60/min).

## Comunicação

- HTTPS obrigatório em produção.
- Webhooks de providers validados por `txid` e idempotência.
- Tokens de API revogáveis pelo lojista.

## Conformidade

- O Pagaê não é uma instituição financeira no MVP. Opera como correspondente/parceiro de SCD.
- Dados de clientes tratados conforme LGPD.
- Auditoria de risco e decisões armazenada em `RiskAnalysis`.

## Próximos passos de segurança

1. Implementar criptografia de CPF/CNPJ e pix_key em repouso.
2. Implementar assinatura HMAC verificável nos webhooks.
3. Adicionar 2FA para acesso ao portal do lojista.
4. Auditoria de acessos e alterações de dados sensíveis.
5. Penetration test e revisão de segurança antes de liberar acesso aberto.
