# Roadmap do Pagaê

## Fase 0 — Discovery (concluída)

- Levantamento de mercado, concorrentes, jornadas e viabilidade regulatória.
- Decisão de modelo: correspondente bancário / parceiro SCD, sem licença própria.

## Fase 1 — MVP (atual)

Objetivo: colocar em produção um checkout Pix parcelado funcional para um grupo fechado de lojistas.

- [x] Autenticação JWT e cadastro de lojistas.
- [x] Cadastro de clientes e perfil de risco rule-based.
- [x] Criação de pedidos (`Order`) e sessões de checkout.
- [x] Geração de parcelas (`Installment`) e cobranças Pix.
- [x] Camada abstrata `PaymentProvider` (sandbox + Celcoin stub).
- [x] Simulação de pagamento e webhook sandbox.
- [x] Dashboard do lojista com vendas, pedidos e status de parcelas.
- [x] Rotina Celery para marcar parcelas vencidas e suspender limites.
- [x] Documentação técnica (arquitetura, API, segurança, regras de negócio).

## Fase 2 — Integração real de Pix

- Implementar provider Celcoin com credenciais reais (ambiente sandbox → produção).
- Adicionar providers alternativos: Asaas, Efí, Mercado Pago, Iugu, OpenPix.
- Conciliação automática de pagamentos via webhooks do provider.
- QR Code dinâmico real e expiração adequada.

## Fase 3 — KYC e risco

- Integração com CAF.io ou similar para validação de identidade.
- Consulta a Serasa/SCPC para score e negativação.
- Ajuste dinâmico de limites com base no histórico de pagamento.
- Regras de risco mais granulares (profissão, renda, comportamento).

## Fase 4 — Antecipação de recebíveis

- Parceria com SCD/FIDC para antecipar parcelas ao lojista.
- Claro contrato de cessão de crédito e rateio de risco.
- **Importante:** o Pagaê só oferecerá antecipação com parceiro financeiro regulado; no MVP o lojista recebe parcela a parcela.

## Fase 5 — Escala e produto

- Painel de administração para operações.
- Reembolsos, cancelamentos e chargebacks.
- App mobile para lojista (opcional).
- Multi-tenant, white-label e APIs avançadas (split, marketplace).

## Critérios de sucesso

- 650 clientes ativos para break-even operacional (estimado mês 8).
- Taxa de aprovação > 60% e inadimplência < 8% no primeiro trimestre.
