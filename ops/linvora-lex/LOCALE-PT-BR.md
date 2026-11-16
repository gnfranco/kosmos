# Kosmos Lex — localização brasileira (pt-BR)

**Estado:** fase 1 da tradução da interface. Não representa localização jurídica/financeira completa.

## Implementação

- Django 4.2 já possui `USE_I18N=True`. O projeto original usava `LANGUAGE_CODE="en-us"` e não tinha mensagens marcadas para tradução.
- `LANGUAGE_CODE` agora aceita `config/.env`; o padrão de código continua `en-us` para preservar o comportamento upstream. **No Hetzner Lex** a configuração é `LANGUAGE_CODE=pt-br`.
- Os catálogos `locale/pt_BR/LC_MESSAGES/django.po` e `.mo` incluem as traduções desta etapa.
- Menus, login, segundo fator, recuperação de senha, dashboard, filtros de período e alguns erros de autenticação usam `{% trans %}`, `gettext` ou `gettext_lazy`.
- Os textos originais permanecem em inglês como `msgid`; somente a apresentação é traduzida. Chaves internas, URLs e dados persistidos não são modificados.
- Datas e formatos numéricos são interpretados pela configuração de idioma do Django; fuso horário no Lex segue `America/Sao_Paulo`.

## Atualização de tradução e upstream

Ao adicionar novas mensagens, marque os textos com `{% load i18n %}` + `{% trans "Texto" %}` nos templates, ou `gettext` / `gettext_lazy` no Python. Depois:

```bash
django-admin makemessages -l pt_BR --no-location --no-wrap
# Preencher os msgstr no arquivo locale/pt_BR/LC_MESSAGES/django.po
django-admin compilemessages -l pt_BR
# Executar verificação de templates e testes de regressão
```

Não traduzir regras de negócios alterando strings armazenadas, estados, identificadores, validações, seleções do banco ou nomes de parâmetros. Integrar upstream em branch separada e revisar novos textos ingleses para marcar e catalogar.

## Limitações reconhecidas

Este primeiro lote cobre navegação, autenticação e dashboard (85 mensagens), **não os 513 templates inteiros**, rótulos de todas as telas, JS de todos os módulos e mensagens dinâmicas. A tradução deve seguir em lotes com testes.

**Cuidado financeiro:** o Kosmos utiliza convenções norte-americanas de faturamento, contas fiduciárias e símbolos `$` no HTML. Alterar `$` para `R$` é incorreto sem verificar a unidade e os cálculos de cada valor. Formatação monetária, honorários, regras fiscais, tabelas de tribunais e modelagem jurídica brasileira exigem etapa própria de adaptação. Não utilizar documentos reais de clientes antes de homologar essas diferenças.
