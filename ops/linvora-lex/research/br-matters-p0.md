# Kosmos Lex Brasil — P0: cadastro de casos e áreas jurídicas

Data de referência: 16/11/2026. Base de trabalho: linvora/hetzner-lex
(bc67f2a7). Referência funcional: Gestão Legal da UFMG, pesquisa no PR #3.
Escopo: adaptar o Kosmos sem fundir frameworks ou bases de dados.

## Compatibilidade jurídica e técnica

- Matter é **Caso**. Proceeding é **Processo judicial**, que continua
  opcional. Case permanece **Dossiê**. Nenhum identificador de banco muda.
- PracticeArea já é um cadastro Django, com name, is_active, FK em
  Matter e Intake e histórico (HistoricalRecords). O painel existente
  de Configurações permite incluir, editar e desativar áreas.
- A migração 0059 cria as onze áreas brasileiras por get_or_create,
  mantendo todos os nomes, IDs, vínculos e estados anteriores. Não remove
  categorias americanas; as sem uso podem ser desativadas por administrador
  depois da conferência do cadastro real, sem perder histórico.
- Formulários de casos mostram apenas áreas ativas ao criar. Ao editar um
  caso, a categoria previamente vinculada continua disponível mesmo se
  estiver desativada. Formulários e filtros devem preservar os PKs.
- A administração das áreas passa a exigir is_admin no servidor. A remoção
  de uma área vinculada a caso ou atendimento retorna 409, preservando as
  FKs; o menu de gestão prefere edição/desativação e não oferece Exclusão.
- Códigos de status e cobrança permanecem em inglês no banco e nas APIs.
  Apenas seus rótulos são localizados por gettext no contexto pt-br.
- O formulário brasileiro de data usa entrada DD/MM/AAAA explícita no
  celular, mas continua aceitando ISO AAAA-MM-DD em POSTs antigos. O dado
  persistido continua sendo DateField. Essa decisão evita depender do
  formato exibido pelo input type=date do navegador Android.
- O modal de casos mantém botões de ação visíveis e torna apenas os campos
  roláveis em telas estreitas. Não altera modais de outros módulos.

## Homologação

1. Em PostgreSQL 16 isolado com pgvector, rodar migrações, manage.py check,
   makemigrations --check --dry-run, pytest e compilação gettext.
2. Verificar no Android: **Adicionar caso**, datas DD/MM/AAAA, seleção de
   Direito Trabalhista e Previdenciário, erros de validação, edição, estado
   e botões Salvar/Cancelar sem ultrapassar o viewport.
3. Em Configurações > Casos, adicionar uma área de exemplo, desativá-la,
   comprovar que desaparece do novo cadastro, permanece nos casos existentes
   e a opção de desativação funciona apenas para administrador.
4. Conferir acessos à lista de casos, atendimentos, processos judiciais,
   calendário e demais serviços existentes.
5. Antes do deploy: snapshot local do banco Kosmos, sem afetar outros bancos.
   Aplicar migração 0059, compilar mensagens (MO já versionado), atualizar
   estáticos, reiniciar somente kosmos-lex e kosmos-lex-worker.
6. Após deploy: HTTPS, serviço, autenticação/2FA, abertura e edição de um
   caso fictício, sem dados reais. Registrar SHA e pendências de UI.

## Limites deste P0

A revisão e eventual desativação das áreas americanas não ocorre
automaticamente: pode haver formulários de intake e casos legados que ainda
dependam delas. O financeiro norte-americano, cadastro CPF/CNPJ, fluxos
trabalhistas/previdenciários específicos e integração Escritório ON permanecem
em sprints posteriores.
