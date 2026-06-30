# Regras de negócio do Pagaê

## Produto

O Pagaê é um checkout que permite ao lojista oferecer pagamento parcelado via Pix. O cliente paga a entrada (primeira parcela) no momento da compra e as próximas parcelas são geradas automaticamente para pagamento futuro.

## O que está no MVP

- Cadastro de lojistas e clientes.
- Criação de pedidos e checkout.
- Análise de risco rule-based.
- Geração de parcelas e cobranças Pix (sandbox).
- Simulação de pagamento e webhook fake.
- Dashboard do lojista com acompanhamento de parcelas.
- Rotina de identificação de atrasos.

## O que NÃO está no MVP

- **Antecipação de recebíveis:** o lojista recebe conforme as parcelas são pagas. Antecipação será avaliada em fase futura com parceiro financeiro regulado.
- **Assunção de risco de inadimplência:** o Pagaê não assume o risco de default do cliente nesta fase. Inadimplência gera suspensão do limite e ações de cobrança.
- **Juros e juros compostos:** o modelo inicial é de parcelamento sem juros ao consumidor; o MDR é descontado do valor líquido ao lojista.
- **KYC real:** a validação de identidade é stub; será integrada com CAF.io/Serasa na Fase 3.

## Regras de risco (MVP)

O motor de risco (`CreditEngine`) aplica as seguintes regras, registrando todas em `RiskAnalysis`:

1. **CPF obrigatório:** o cliente deve ter CPF cadastrado.
2. **Telefone obrigatório:** telefone é obrigatório para contato e cobrança.
3. **KYC aprovado:** o cliente deve estar com status `approved` (stub para MVP).
4. **Cliente bloqueado:** se houver bloqueio ativo, a compra é negada.
5. **Limite máximo para primeira compra:** definido por faixa de score (R$150, R$300, R$500).
6. **Bloqueio se houver parcela atrasada:** parcelas em status `overdue` suspendem o limite automaticamente.
7. **Velocity:** máximo de 2 aplicações de crédito por CPF a cada 24 horas.

Os motivos de reprovação são armazenados e podem ser consultados.

## Parcelas

- Parcelas são geradas automaticamente no ato da aprovação.
- Vencimento a cada 15 dias (configurável futuramente).
- A última parcela absorve diferenças de arredondamento.
- Status possíveis: `pending`, `paid`, `overdue`, `cancelled`, `refunded`.
- A cada manhã o Celery identifica parcelas vencidas e:
  - marca como `overdue`;
  - calcula `days_past_due`;
  - bloqueia o cliente;
  - envia lembretes (stubs).

## Cobranças Pix

- Cada parcela gera uma cobrança Pix (`PixCharge` / `PaymentTransaction`).
- QR Code e copia-e-cola são exibidos no checkout público.
- O provider pode ser trocado via `PAYMENT_PROVIDER` (sandbox, celcoin, etc.).

## Repasse ao lojista

- O lojista recebe o valor líquido (`net_amount = total - MDR`) conforme as parcelas são pagas.
- No MVP o repasse é manual/disparado via API. A automação completa e antecipação ficam para fases futuras.
- MDR padrão: 7% (negociável por lojista).

## Webhooks para o lojista

Eventos entregues assincronamente:

- `checkout.approved`
- `installment.paid`
- `installment.overdue`
- `webhook.test`

## Proibições

- Não copiar textos, layouts, cores ou fluxos de concorrentes.
- Não afirmar que o Pagaê é uma instituição financeira ou assume risco de inadimplência no MVP.
- Não prometer antecipação ao lojista nesta fase.

## Glossário

- **MDR:** taxa de desconto sobre o valor da transação.
- **DPD:** days past due (dias de atraso).
- **GMV:** gross merchandise value (valor bruto transacionado).
- **SCD:** Sociedade de Crédito Direto (parceiro regulado para empréstimo/crédito no futuro).
