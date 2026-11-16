# Kosmos Lex Brasil — fluxo de trabalho pelo GitHub

Data: 16/11/2026. Repositório: `gnfranco/kosmos`.

## Planejamento

Issues do repositório foram habilitadas. Milestones L1–L6 organizam os lotes:
L1 pt-BR + casos, L2 clientes PF/PJ, L3 trabalhista/previdenciário,
L4 agenda e prazos, L5 financeiro, L6 Escritório ON.

O token do GitHub CLI no Orion tem escopo `repo`, mas não `read:project/project`;
o quadro GitHub Projects só poderá ser criado após conceder esses escopos.
Até lá, a organização é feita com **Issues, milestones e labels**:
`status:ready`, `status:in-progress`, `status:review`, `status:done`,
e categorias `lex:localizacao`, `lex:juridico`, `lex:qa`, `lex:infra`.

Cada agente deve ler Issues e o PR em andamento, atualizar status e testes,
sem reiniciar projetos, nem misturar branches `upstream/dev` com produção.

## L1 — Cadastro de casos pt-BR

Issues #5, #6, #7 e #8.

- `MatterForm`: labels e opções de situação/trabalho/cobrança traduzíveis,
sem alterar códigos persistidos.
- Data de abertura por extenso `DD/MM/AAAA` no modal, entrada ISO permitida
para compatibilidade de clientes antigos. Guardar `DateField` nativo,
não strings brasileiras no banco.
- Modal no celular: rolagem interna e rodapé acessível.
- `PracticeArea` já é uma entidade editável em Configurações, com
`is_active`; nenhuma alteração de schema é necessária nesta etapa.
- `python manage.py seed_br_practice_areas` adiciona 13 categorias brasileiras.
  Em uma instância **pt-br** somente, a opção
  `--deactivate-unused-legacy` desativa sementes americanas **sem casos nem
  atendimentos associados**, preservando áreas customizadas e registros usados.
  `--dry-run` permite simular com rollback da transação.
- Categorias podem ser reativadas pelo administrador em
  Configurações > Áreas de atuação. Exclusão com caso/atendimento associado
  passa a ser bloqueada em vez de desvincular silenciosamente.
- Catálogo gettext pt-BR sem entradas marcadas fuzzy.

### Implantação controlada

1. Validar em worktree no Hetzner e PostgreSQL de QA: testes do módulo e
   regressão (incluindo cliente antigo, caso referenciado e proteção de acesso).
2. Criar backup pré-implantação via `kosmos-lex-backup.service`.
3. Integrar PR em `linvora/hetzner-lex`; conferir diff e migrações.
4. Fazer pull em `/srv/kosmos-lex/app`, rodar
   `python manage.py check` e `makemigrations --check --dry-run`.
5. Confirmar `LANGUAGE_CODE=pt-br`, simular o cadastro:
   `python manage.py seed_br_practice_areas --deactivate-unused-legacy --dry-run`.
6. Aplicar sem `--dry-run` e reiniciar somente serviços do Kosmos.
7. Testar HTTPS/login, apresentação das áreas brasileiras e data em `DD/MM/AAAA`
   no cadastro móvel, preferencialmente com **dados fictícios**.
8. Não mexer no Escritório ON nem nas outras aplicações da VPS.

## Etapas seguintes

Abrir PRs pequenos para CPF/CNPJ (L2), práticas trabalhistas e
previdenciárias (L3) e adaptação financeira (L5). Usar o Gestão Legal
UFMG como referência funcional, não importar seus modelos diretamente.
