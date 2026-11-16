# Lex × Gestão Legal UFMG — avaliação comparativa inicial

**Data:** 16/11/2026
**Natureza:** análise de código-fonte / proposta de arquitetura, **sem migrações nem integrações executadas**.
**Kosmos de referência:** `gnfranco/kosmos`, branch `linvora/hetzner-lex`, commit inicial `d7c3b6df`.
**Gestão Legal de referência:** `gnfranco/gestaolegal` (fork de `LabP2/gestaolegal`), branch `master`, commit `b8f2f8d`.
**Licenças:** AGPL-3.0 nos dois repositórios; preservar avisos e revisar obrigações de oferta do código de modificações usadas em rede.

## Objetivo

Adotar o **Kosmos como aplicação principal** do escritório e usar o **Gestão Legal UFMG como referência de fluxos e modelos brasileiros**, portando seletivamente apenas funcionalidades aprovadas para a arquitetura Django/PostgreSQL existente. Não importar/mesclar um banco MySQL no PostgreSQL, nem copiar o frontend SvelteKit inteiro para HTMX.

### Código de origem e atualização

| Ambiente | Kosmos (principal) | Gestão Legal (referência) |
| --- | --- | --- |
| GitHub | https://github.com/gnfranco/kosmos | https://github.com/gnfranco/gestaolegal |
| Original/upstream | https://github.com/Kosmos-Law/kosmos | https://github.com/LabP2/gestaolegal |
| Orion | `~/source/repos/gnfranco/kosmos` | `~/source/repos/gnfranco/gestaolegal-ufmg` |
| MacBook | `~/Developer/kosmos` | `~/Developer/gestaolegal-ufmg` |
| Stack | Django 4.2, PostgreSQL, HTMX, template tags, Django-Q | Flask 3, SQLAlchemy, MySQL, SvelteKit, Docker |
| Papel | Instância Lex publicada | Leitura/benchmark; sem deploy de serviços |

O repositório UFMG também menciona `gestaolegalufmg/gestaolegal` no README, aparentemente outro checkout público; o fork foi feito de **LabP2/gestaolegal**, que pertence ao laboratório e estava mais atualizado na verificação. Monitorar eventual migração de origem antes de sincronizar forks.

## Distinção de entidades e nomenclatura

**Gestão Legal:** `Caso` = trabalho/atendimento jurídico; pode ter **vários `Processo`** judiciais, cliente(s), responsáveis, eventos e documentos (`gestaolegal/models/caso.py`, `processo.py`, `evento.py`).

**Kosmos:** `Matter` = assunto/caso atendido pelo escritório; pode ter **vários `Proceeding`** vinculados (`apps/matters/models.py`, `apps/matters/proceedings/models.py`). `Case` no Kosmos é o espaço de trabalho/documentos/provas, não sinônimo de processo CNJ.

**Recomendação de interface pt-BR:** avaliar `Matter → Caso/Pasta jurídica` (em vez de chamar sempre de Processo), `Proceeding → Processo judicial`, `Case → Dossiê`, `Intake → Atendimento inicial`. A tradução atual de `Matter` como `Processo` pode confundir quando uma demanda tem vários processos judiciais. A mudança deve ser tratada como UX e testes, sem mudar tabelas, chaves ou estados armazenados.

## Matriz funcional preliminar

| Domínio | Kosmos existente | Gestão Legal existente | Direção |
| --- | --- | --- | --- |
| Clientes PF/PJ | `Contact` genérico (`apps/contacts/models.py`) | `Atendido`, `Assistido`, representação legal, CPF/CNPJ/endereço (`models/atendido.py`, `assistido.py`) | **Adaptar** cadastro brasileiro em modelos/campos do Kosmos, validando CPF/CNPJ; não copiar dados socioeconômicos ou sensíveis sem necessidade |
| Caso e processo | `Matter` + `Proceeding`: case_number, forum, date_filed, status | `Caso` + `Processo`: espécie, vara, link, valores, distribuição, trânsito, posição, probabilidade | **Alta prioridade.** Estender `Proceeding` com metadados brasileiros sem duplicar `Matter` |
| Início do atendimento | `apps/intakes`, contatos e atividades | `OrientacaoJuridica`, histórico de atendimento, atendido → assistido; fila e plantão | **Adaptar o fluxo de triagem e orientação**, sem importar a lógica de elegibilidade de assistência gratuita no escritório privado |
| Prazos/agenda | `apps/calendar`, `apps/tasks`, responsáveis e notificações | `Evento`, `Lembrete`, caso, responsável e fluxo por unidade | Usar agenda/tarefas do Kosmos e acrescentar semântica de prazo judicial/ato, evitando segundo agendador paralelo |
| Documentos | `apps/case`: OCR, textos, citações, busca, dossiês; integração atual com Drive | `Arquivo`, `ArquivoCaso`, upload e permissões por unidade | **Manter Kosmos + Escritório ON** como prioridades; aproveitar só boas práticas de autorização/metadados; definir uma fonte única da verdade |
| Papéis e isolamento | Django permissions + membros por Matter; autenticação/2FA | Orientador, estagiário, colaborador; `RequestContext` por unidade | Avaliar perfis adequados à advocacia privada, sem transplante direto de isolamento entre unidades e sem enfraquecer autorização |
| Administração financeira | Honorários por hora/preço fixo, invoices, despesas, trust accounting e relatórios | Nenhum módulo de faturamento/contabilidade geral equivalente identificado nos modelos/rotas examinados | **Preservar modelo Kosmos temporariamente.** Abrir projeto separado para BRL, contratos de honorários, ISS/NFS-e, repasses e contas. Trust accounting dos EUA não equivale automaticamente a contabilidade jurídica brasileira |
| Localização | pt-BR parcial: menus, login e dashboard, PR #2 | Português nativo e terminologia brasileira | Usar a UFMG como referência terminológica, mantendo gettext do Django e preservando en-US original |
| Unidades / escalas | Escritório e usuários | Múltiplas unidades, escalas, fila, presença e prioridades | Útil apenas se houver necessidade comprovada de unidades independentes ou atendimento por plantão. Não priorizar para o piloto |
| Relatórios | Administrativo/financeiro (apps/reports) | Atendimentos e operação da assistência judiciária | Avaliar indicadores brasileiros em relatórios, preservando base financeira e permissões do Kosmos |

## Achados de código e cuidados

1. **Metadados jurídicos são complementares:** o `Proceeding` atual tem `forum`, `case_number` e `date_filed` mas não contém, como campos próprios, vara, valor da causa, distribuição, trânsito em julgado ou espécie processual. O `Processo` da UFMG traz esses dados.
2. **Não presumir CNJ validado:** `gestaolegal/models/processo_input.py` apenas remove espaços e limita `numero` a 25 caracteres; não foi identificada ali validação do dígito verificador CNJ. Especificação/validação devem ser implementadas e testadas independentemente.
3. **Moeda e tipos:** `ProcessoCreateInput` usa `Decimal` para valores da causa; o dataclass `Processo` anota os valores como `float`. Em Django, escolher `DecimalField` e jamais trocar `$` por `R$` sem revisar a moeda efetiva e cálculos.
4. **Dados sensíveis:** `Assistido` inclui renda, raça, doenças na família e critérios socioeconômicos próprios da assistência judiciária. Não incorporar automaticamente no cadastro geral por minimização de dados/LGPD.
5. **Segurança:** `ProcessoService._caso_da_unidade_ativa` verifica se o caso pertence à unidade e evita divulgar sua existência; conceito aproveitável em testes de isolamento de acesso por processo no Kosmos, independentemente do código.
6. **Sem integração judicial confirmada:** nenhuma das partes examinadas comprova ingestão automática integral de andamentos DJEN, DataJud ou tribunais. Deve ser tratado como módulo separado com fontes e requisitos oficiais.

## Proposta de implementação evolutiva

| Etapa | Entrega | Condição para aceitar |
| --- | --- | --- |
| P0 — Decisão terminológica | Nomes `Caso` / `Processo judicial` / `Dossiê` / `Atendimento inicial`, pt-BR consistente | Revisão com escritório e regressão de menu/telas |
| P1 — Processo judicial BR | Extensão de `Proceeding` com campos necessários, migração aditiva, formulários e pesquisa | 1 caso com múltiplos processos, status e histórico preservados, testes de autorização, testes CNJ |
| P2 — Cadastro brasileiro | CPF/CNPJ, contatos PF/PJ, representação legal e endereço; validações | Sem necessidade de dados sensíveis; permissão, máscara, busca e deduplicação testadas |
| P3 — Atendimento jurídico | Triagem e orientação vinculadas ao `Intake` e possível conversão em `Matter` | Rastreamento de origem, responsável, cronologia e histórico |
| P4 — Agenda e prazos | Prazos judiciais, audiência, publicação, responsável e alertas | Testes de fuso, feriados, competência, revisão humana; **não automatizar prazo legal sem critérios** |
| P5 — Financeiro brasileiro | Diagnóstico e modelagem honorários, recebimentos, despesas, repasses, BRL, tributos | Parecer contábil/jurídico antes de substituir partes de trust/invoices; testes de precisão |
| P6 — Escritório ON | Correlação de IDs de processos e referências documentais por API | Sem cópia unilateral, sem duplicação, com permissões, trilha de auditoria e plano de rollback |

**Regra:** cada etapa deve virar PR pequeno no Kosmos, com testes e nota de compatibilidade, mantendo as duas origens sincronizáveis. Nunca fazer merge de branches completas dos dois projetos: são arquiteturas distintas.

## Atualização do fork de referência

No Orion/MacBook, apenas quando desejado:

```bash
cd gestaolegal-ufmg
git fetch upstream
git switch -c review/ufmg-YYYYMMDD master
git log --oneline --left-right master...upstream/master
# Revisar alterações; só depois atualizar o fork
```

Sem executar `docker compose up`, scripts de seed, reset de banco ou importação de dados até definir uma sandbox independente (na máquina local, não no Hetzner de produção).

**Status desta análise:** mapa arquitetural baseado nos arquivos citados e no README; não equivale a benchmark funcional da UI nem auditoria de segurança completa.
