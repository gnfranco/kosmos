# Kosmos Lex — P0/P1 Brasil: casos e processos judiciais

Base: `gnfranco/kosmos` (`linvora/hetzner-lex`). Referência funcional: `LabP2/gestaolegal` (AGPL-3.0), modelos `Caso` e `Processo`.

## Alterações

- Tradução: `Matter` passa a **Caso** e `Proceeding` a **Processo judicial**. `Case` continua **Dossiê**. Não mudar chaves internas.
- Campos adicionais, sem remover dados antigos: tipo de numeração (CNJ ou outro/legado), classe, vara, valor inicial/atual da causa em BRL, data de trânsito em julgado e URL do tribunal. `date_filed` continua distribuição; `forum` identifica tribunal/foro.
- `Proceeding` e `HistoricalProceeding` recebem os novos campos pela migration `0058`. Registros existentes ficam `OTHER`, preservando identificadores e histórico.
- CNJ com validação de 20 dígitos e Módulo 97 Base 10 conforme Resolução CNJ 65/2008, Anexo VIII: https://atos.cnj.jus.br/atos/detalhar/atos-normativos?documento=119. Validar número **não** comprova a existência do processo.
- Edição e exclusão limitadas ao processo do caso informado na rota; exclusão apenas por DELETE e definição de principal apenas por POST.
- Tradução por gettext; não transformar valores financeiros preexistentes em reais apenas trocando o símbolo $.

## Aceite/implantação

Antes do deploy, executar check, makemigrations --check, testes CNJ/legado, permissão cruzada, migração em banco temporário e backup dos dados/arquivos. Após deploy, validar HTTPS, login/2FA, caso fictício com processos CNJ e legado, histórico e telas móveis.

Migração aditiva, mas rollback em banco com novos dados deve ser feito após preservar os campos novos. Ainda não liberado para dados reais de clientes.

## Etapas seguintes

P2: CPF/CNPJ e representantes; P3: atendimento inicial; P4: prazos e eventos; P5: adaptação financeira, honorários, ISS/NFS-e; P6: referências documentais no Escritório ON por API, sem duplicar arquivos.
