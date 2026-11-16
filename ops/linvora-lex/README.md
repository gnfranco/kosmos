# Kosmos Lex — Linvora, ambiente de homologação

Aplicação jurídica separada do Escritório ON e do Odoo. **Não executar** `scripts/install.sh --prod` no Hetzner compartilhado: esse instalador instala Nginx, modifica configurações do sistema e usa nomes genéricos de serviços.

## Endereços e isolamento

- Publicação: `https://lex.linvora.com.br`, DNS A `lex` -> `2.31.52.232` (Registro.br).
- Sistema: `/srv/kosmos-lex/app`, serviço Linux próprio `kosmoslex`.
- Django/Gunicorn: `127.0.0.1:18085`, nunca diretamente público.
- Banco: PostgreSQL local, banco e papel exclusivos `kosmoslex`.
- Serviço web: `kosmos-lex.service`; tarefas: `kosmos-lex-worker.service`.
- Caddy: `/etc/caddy/lex.caddy`, importado ao final do Caddyfile principal.
- Autenticação no próprio Django/Kosmos com 2FA, sem prompt adicional de Basic Auth no Caddy. O Caddy aplica TLS, HSTS e oculta URLs técnicas.
- Variáveis e senhas: `/srv/kosmos-lex/app/config/.env`, **não versionar**.
- Arquivos: `media/` privado; Caddy serve apenas `static/`. **Nunca** expor `media/` diretamente.

## Git

```bash
git remote -v
# origin: https://github.com/gnfranco/kosmos.git
# upstream: https://github.com/Kosmos-Law/kosmos.git
git fetch upstream
# Integrar upstream somente em branch de trabalho, resolver conflitos e homologar
```

A branch `linvora/hetzner-lex` guarda a integração e a documentação de deploy, preservando a `dev` original. Não incorporar alterações diretamente na branch `dev` sem revisão.

## Regras de implantação

1. Criar DNS A `lex` no Registro.br, apontando ao IPv4 público do Hetzner.
2. Usar Python 3.13 instalado pelo `uv`, PostgreSQL 16 e extensões `vector` e `pg_trgm` **somente no banco kosmoslex**.
3. Criar uma role sem privilégios administrativos, banco exclusivo e segredo aleatório.
4. Usar `DEBUG=False`, `ENV=prod` para a execução hospedada, `ALLOWED_HOSTS=lex.linvora.com.br,127.0.0.1`, `CSRF_TRUSTED_ORIGINS=https://lex.linvora.com.br`, `TIME_ZONE=America/Sao_Paulo` e `EMAIL_NOTIFICATIONS=False` enquanto os dados forem fictícios.
5. Rodar `uv sync --frozen --no-dev`, `manage.py check --deploy`, `manage.py migrate` e `collectstatic`; registrar resultado.
6. Subir apenas serviços com prefixo `kosmos-lex`; não reiniciar os serviços de Odoo ou Escritório ON.
7. Testar Caddy com `caddy validate --config /etc/caddy/Caddyfile` antes de `systemctl reload caddy`; preservar cópia original do Caddyfile.
8. Homologar URL HTTPS, autenticação, assets, backup e restauração. **Somente dados fictícios** até aprovação.

## Atualização

```bash
git fetch upstream
git switch -c sync/upstream-YYYYMMDD linvora/hetzner-lex
git merge upstream/dev
# Executar testes, abrir PR, revisar e só então implantar a versão aprovada
```

Para operação: `systemctl status kosmos-lex kosmos-lex-worker`, `journalctl -u kosmos-lex -n 80`, `curl -I http://127.0.0.1:18085`.

A licença upstream é AGPL-3.0. Revisar obrigações de disponibilização do código ao distribuir/modificar aplicação acessível pela rede.

## Estado verificado — 16/11/2026

- Fork próprio com `origin` e `upstream`; deploy na branch `linvora/hetzner-lex`.
- Bootstrap de DB e extensões concluído: `ops/linvora-lex/bootstrap-db.sh`.
- Django inicializado: `ops/linvora-lex/init-app.sh`; migrações, busca, agendamentos e estáticos OK.
- Serviço web e worker em execução, com `MemoryMax`, via `ops/linvora-lex/install-services.sh`.
- Caddy 2.6.2: HTTPS automático válido, HTTP -> HTTPS, HSTS curto (24h), sem Basic Auth; login Django com 2FA. Endpoints técnicos `/health/*`, `/mcp*` e `/.well-known/*` inacessíveis publicamente.
- Admin de teste criado via `ops/linvora-lex/bootstrap-admin.sh`; SMTP local do Hetzner enviou e-mail de teste e a mensagem foi encontrada no Gmail.
- Verificação: `/health/live/`, `/health/ready/`, `/health/worker/` e `/accounts/login/` retornaram HTTP 200 localmente. Externamente, login HTTP 200, técnicos HTTP 404, TLS válido, HTTP HTTP 308 para HTTPS e estáticos HTTP 200.
- Os serviços anteriores `escritorio-ops`, `linvora-odoo20-shared`, `postgresql@16-main` e `caddy` permanecem ativos.
- Django hospedado com `DEBUG=False`, `ENV=prod`, `TIME_ZONE=America/Sao_Paulo`, notificações de e-mail desativadas no piloto. `check --deploy` ainda aponta recomendações de HSTS e redirect gerenciados no Caddy e X-Frame-Options SAMEORIGIN; revisar antes de liberar dados reais.

### Primeiro acesso (não versionar senhas)

No **Orion**, com acesso à VPN Hetzner:

```bash
ssh -i ~/.ssh/hetzner_linvora_ed25519 root@10.77.0.1 'cat /root/kosmos-lex-access.txt'
```

Utilizar somente `DJANGO_ADMIN_EMAIL` e `DJANGO_ADMIN_PASSWORD` do arquivo; os valores `CADDY_BASIC_*` são legados e **não** devem ser utilizados. O Kosmos exige um código de login enviado por e-mail ou TOTP configurado. As senhas permanecem no Hetzner (0600), nunca no Git ou nesta documentação.

### Próximos testes

Backup local inicial criado por `ops/linvora-lex/backup-lex.sh`: PostgreSQL custom dump e `media/` em `/srv/kosmos-lex/backups/`, acessíveis apenas ao root. **Restauração de teste concluída com sucesso** em banco temporário, com 404 migrações, e o banco temporário foi excluído. O timer `kosmos-lex-backup.timer` realiza backup local diário (06:30 UTC, aproximadamente 03:30 BRT), usando executável root-owned instalado em `/usr/local/sbin`. **Ainda faltam backup offsite, retenção/monitoramento e teste completo de recuperação operacional** antes de inserir dados reais.

Homologar navegação, permissões de usuários, agenda e casos, OCR, financeiro, exportação de dados e backup/restauração integral. Permanecer com dados fictícios até validação.
