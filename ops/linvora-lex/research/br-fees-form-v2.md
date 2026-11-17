# Kosmos Lex Brasil — honorários contratuais: formulário desktop v2

Data: 17/11/2026. Origem: homologação visual do PR #17 em
linvora/hetzner-lex, após criação, edição e reabertura de caso de teste.

## Problema observado

A interface apresentava simultaneamente o faturamento interno herdado dos
Estados Unidos (billing_type, flat_fee_amount, deferred_fees, billable)
e o novo contrato de honorários brasileiro. O usuário registrou um exemplo
de honorários mistos (30% de êxito) e R$ 2.000 no faturamento interno;
a base de incidência contratual recebeu "1800000" como se fosse valor em reais.

Essas estruturas têm significados jurídicos e contábeis diferentes.
Não é seguro converter automaticamente o valor legado em parcela fixa
do contrato e tampouco inferir uma base contratual a partir do valor da causa.

## Correção implementada

- Campo novo fee_fixed_amount: parcela fixa DO CONTRATO, distinto
  de flat_fee_amount (faturamento interno Kosmos).
- Campo novo fee_hourly_rate: valor CONTRATUAL da hora, distinto
  do lançamento de tempo do faturamento interno.
- fee_success_percentage e fee_success_basis preservados, com labels
  mais claros e explicação de que a base deve identificar as verbas abrangidas.
- Notas contratuais apresentadas como Condições de pagamento.
- Em pt-BR, campos de faturamento norte-americano deixam de aparecer
  no formulário do caso; seus valores no banco são preservados em
  qualquer edição feita pelo formulário brasileiro.
- Aviso read-only para flat_fee_amount legado, sem copy/backfill;
  aviso adicional quando a base histórica é apenas numérica.
- Campos de valor e percentual exibidos conforme modalidade.
  Valor fixo obrigatório para FIXED/MIXED, percentual e base para
  SUCCESS/MIXED, valor da hora para HOURLY.
- Valores aceitos em pt-BR como 2000,00 ou 2.000,00;
  armazenamento Decimal, sem ponto flutuante.
- Mudança de modalidade limpa somente campos contratuais não mais
  pertinentes (não apaga o faturamento legado nem termos em notas).
- HistoricalMatter registra os novos valores.
- POST antigo sem campos contratuais preserva todos os termos existentes.
- Desktop é prioritário, sem redesign amplo de dispositivos móveis.

## Limites desta etapa

Nada calcula, emite ou cobra honorários automaticamente. Não há
geração de parcelas, contas a receber, nota fiscal, livro caixa,
ou reconciliação de valores recebidos pelo cliente.
A apuração de êxito e sucumbência será implementada em fluxo próprio
após validação das regras do contrato e da área jurídica.

## Homologação funcional sugerida

1. No desktop, abrir caso fictício com honorários mistos.
2. Informar R$ 2.000,00 fixos, 30% de êxito, base descrita,
   condições de pagamento; salvar e reabrir.
3. Alterar o valor fixo, verificar persistência e histórico.
4. Inspecionar caso criado antes do ajuste: o valor no campo antigo
   deve estar preservado, mas NAO copiado para o novo campo.
5. Testar troca entre misto, percentual, valor fixo, hora e gratuito.
6. Verificar que o faturamento interno, sucumbência e financeiro
   não foram alterados e que não houve cobrança gerada pelo cadastro.
