# Kosmos Lex — Linvora, ambiente de homologação

Aplicação jurídica separada do Escritório ON e do Odoo. **Não executar** `scripts/install.sh --prod` no Hetzner compartilhado: esse instalador instala Nginx, modifica configurações do sistema e usa nomes genéricos de serviços.

## Endereços e isolamento

- Publicação: `https://lex.linvora.com.br`, DNS A `lex` -> `2.31.52.232` (Registro.br).
- Sistema: `/srv/kosmos-lex/app`, serviço Linux próprio `kosmoslex`.
- Django/Gunicorn: `127.0.0.1:18085`, nunca diretamente público.
- Banco: PostgreSQL local, banco e papel exclusivos `kosmoslex`.
- Serviço web: `kosmos-lex.service`; tarefas: `kosmos-lex-worker.service`.
- Caddy: `/etc/caddy/lex.caddy`, importado ao final do Caddyfile principal.
- Autenticação extra de piloto em Caddy por hash bcrypt. Senha **não** versionada.
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
4. Usar `DEBUG=False`, `ENV=dev`, `ALLOWED_HOSTS=lex.linvora.com.br,127.0.0.1`, `CSRF_TRUSTED_ORIGINS=https://lex.linvora.com.br`, `TIME_ZONE=America/Sao_Paulo` e `EMAIL_NOTIFICATIONS=False`.
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
