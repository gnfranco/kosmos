# L2a — Cadastro brasileiro inicial de contatos

Data de implementação: 19/11/2026.
Issue #9: https://github.com/gnfranco/kosmos/issues/9

## Objetivo e escopo do primeiro PR

A homologação do formulário de honorários do PR #18 foi visualmente
aprovada em 19/11. O cadastro de contatos brasileiro é a próxima frente,
mas foi dividido para reduzir risco e facilitar testes.

Esta primeira fase adiciona ao modelo Contact e histórico:
- tipo de pessoa: não informado, PF e PJ;
- CPF/CNPJ opcional, com armazenamento normalizado, sem pontuação;
- nome fantasia opcional para PJ.

Na interface pt-BR:
- formulário criar/editar oferece os três campos;
- CPF com módulo 11 e dois dígitos verificadores;
- CNPJ numérico tradicional e alfanumérico (12 caracteres base +
  dois dígitos numéricos). Cálculo por ASCII - 48 e módulo 11.
  Referência oficial: https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/documentos-tecnicos/cnpj/manual-dv-cnpj.pdf
- telefone celular/fixo brasileiro com DDD, +55 opcional, armazenamento
  apenas dígitos, renderização brasileira e links tel:+55 em
  contatos brasileiros PF/PJ.
- visualização interna do documento mostra apenas os últimos quatro
  caracteres (inteiro disponível apenas na edição autenticada).
- nome/razão social com até 100 caracteres (limite do modelo).
- formulários e mensagens essenciais em português.

## Compatibilidade, proteção e limites

- Migração aditiva, sem exigir CPF ou CNPJ para contatos antigos,
  estrangeiros, sem documentação ou apenas prospectos.
- Não converte automaticamente nomes, endereços, empregadores,
  documentos ou telefones legados.
- Formulários antigos que não enviam campos BR não apagam os dados
  identificadores existentes. Em en-US, o esquema US segue no formulário.
- A coluna CPF/CNPJ não é unique nesta fase: antes de bloquear
  duplicatas há que auditar importações, homônimos, representações,
  cadastros históricos e dados incorretos.
- Não envia CPF/CNPJ adicionalmente para Google Contacts nem outros
  conectores; nenhuma consulta externa ou validação cadastral na RFB
  é feita. Só é validada sintaxe e dígitos verificadores.
- O documento está armazenado em coluna textual do banco existente;
  é dado pessoal identificável. Revisão LGPD, logs/exportação, acesso
  por papel e política de retenção deverão anteceder uso com clientes
  reais. Não usar CPF real nos testes.
- Regras de validação estão no formulário. Escritas por API/ORM podem
  contornar ModelForm, como ocorre em outros campos legados; revisar
  essas entradas antes de ampliar integrações.

## Itens que permanecem na issue #9 após este PR

1. Endereços brasileiros estruturados: CEP, logradouro, número,
   complemento, município e UF, respeitando address legado.
2. Representantes legais como relações de Contact (uma pessoa não
   deve ser duplicada em campos de texto); cardinalidade, vigência
   e papéis processuais.
3. Pesquisa/deduplicação segura por CPF/CNPJ e revisão de
   permissões por usuário/processo.
4. Integração de PF/PJ em Intake/Matter, autorização e sincronização.
5. Homologação de desktop com dados fictícios, revisão de privacidade
   e deploy somente após QA e aprovação.

## Critérios de aceite L2a

PostgreSQL isolado; manage.py check, makemigrations --check; testes
de CPF/CNPJ (incluindo exemplo oficial alfanumérico), telefone, histórico,
preservação em edição legada, CRUD HTTP de contato, UI e regressões
de contatos/casos/atendimentos.
