# Kosmos Lex Brasil — honorários contratuais (primeira etapa)

Data: 16/11/2026. Base: linvora/hetzner-lex, após P0.
Referência: o Gestão Legal da UFMG é voltado à assistência judiciária gratuita
e não tem modelo próprio para contrato de honorários de êxito no código examinado.

## Implementação

- Cadastro em Matter separado de billing_type, que continua servindo ao
  mecanismo norte-americano de faturamento por hora ou valor fixo.
- Modalidades: não informado, hora, valor fixo, êxito, misto, por etapa,
  gratuito/pro bono e outro. Sem presumir percentuais contratuais por área.
- Para êxito e misto: percentual decimal e **descrição obrigatória da base**.
  Ex.: valores efetivamente recebidos, parcelas vencidas ou proveito econômico,
  conforme contrato específico. Não escolher automaticamente a base.
- Notas adicionais podem registrar entrada, condições, vencimentos e exceções.
- Histórico dos campos em HistoricalMatter. Nenhum faturamento, repasse,
  lançamento contábil, nota fiscal ou cobrança gerado ao salvar.
- Exibição focada no desktop, e faturamento legado claramente distinto.
- POSTs de formulários antigos, sem os novos campos, preservam valores
  existentes. Casos legados começam com modalidade não informada.

## Cuidados jurídicos

- Estatuto da Advocacia, Lei 8.906/1994, arts. 22 a 24.
- Código de Ética e Disciplina OAB (Resolução 02/2015), arts. 48–50.
- Consulta OAB 089/2025/OEP: quota litis e limites éticos são examinados em
  função do contrato, do benefício do cliente e da sucumbência.
- Não fixar percentuais automaticamente, impor teto genérico na interface
  ou presumir que a base corresponde ao valor da causa ou da condenação.
- O contrato escrito revisado e assinado prevalece: a tela não substitui
  o instrumento jurídico, apenas registra metadados para uso operacional.

## Etapas futuras (não incluídas)

- Registro do instrumento assinado, versões e conferência.
- Lançamentos de valores reconhecidos/recebidos, parcelas e abatimentos.
- Apuração verificável dos valores devidos, separando sucumbência e
  honorários contratuais, por área e natureza de benefício.
- Cobrança, conciliação, emissão fiscal brasileira e prestação de contas,
  sem adaptação apressada do motor de trust accounting do Kosmos.
