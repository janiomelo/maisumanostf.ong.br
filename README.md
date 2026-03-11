# maisumanostf.ong.br

Home da campanha em formato "Wiki de Urgência".

## Escopo atual (primeiro commit)

- Landing page SSR com narrativa da campanha
- Contador regressivo para a próxima vaga
- Gráfico dinâmico (Chart.js) com histórico + cenários (risco e campanha)
- Conteúdo institucional (resumo, cronologia, vagas e referências)
- Wiki dinâmica persistida em banco com edição autenticada por papel

Nesta fase a assinatura autenticada do manifesto esta ativa.

## Stack

- Flask (SSR)
- Chart.js (visualização)
- Nginx via docker-compose

## Rodar em desenvolvimento

```bash
make init
make up
```

Abrir: `http://localhost:8000`

## Comandos úteis

```bash
make logs
make restart
make refresh
make down
make test
make test-unit
make test-functional
make test-e2e
make test-cov
make db-update
make user-create EMAIL=editor@dominio SENHA=trocar PAPEL=editor
```

## Cobertura no GitHub

O workflow `CI - Testes` publica cobertura na interface do GitHub em dois pontos:

- resumo do job (aba de `Checks` do PR/push), com a cobertura total de linhas;
- artefato `coverage-xml`, contendo o `coverage.xml` gerado na execucao.

## Configuração por ambiente

As variáveis da home ficam no `.env`:

- `COUNTDOWN_TARGET` (ISO datetime)
- `VACANCY_FUX_DATE` (YYYY-MM-DD)
- `VACANCY_CARMEN_DATE` (YYYY-MM-DD)
- `VACANCY_GILMAR_DATE` (YYYY-MM-DD)
- `GA4_MEASUREMENT_ID` (opcional; ex.: `G-XXXXXXXXXX`)

Variáveis de autenticação inicial (sessão):

- `AUTH_USER_ADMIN_EMAIL`, `AUTH_USER_ADMIN_PASSWORD`, `AUTH_USER_ADMIN_PAPEL`
- Esta configuração cria apenas o admin bootstrap no ambiente
- Demais usuários devem ser cadastrados no banco (ex.: `make user-create ...`)

Variáveis opcionais para login com Google (OAuth):

- `GOOGLE_OAUTH_ENABLED` (`true` ou `false`)
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI` (URL absoluta de callback em producao; ex.: `https://maisumanostf.ong.br/auth/google/callback`)
- `GOOGLE_DISCOVERY_URL` (padrão Google)

Importante em producao (erro `redirect_uri_mismatch`):

- cadastre no Google Cloud exatamente a mesma URL usada em `GOOGLE_REDIRECT_URI`;
- inclua variacoes necessarias (`www` e sem `www`) apenas se realmente usadas;
- garanta esquema `https`.

Variáveis opcionais para envio de e-mail de confirmacao de apoio (Resend):

- `RESEND_API_KEY`
- `RESEND_FROM_EMAIL` (ex.: `Mais Uma no STF <apoios@maisumanostf.ong.br>`)
- `RESEND_REPLY_TO` (opcional)
- `APOIOS_EMAIL_CONTATO` (canal de contato exibido no e-mail)
- `SITE_URL` (URL pública base usada no corpo do e-mail)

Variável opcional de conexão com banco (PostgreSQL):

- `DB_POOL_RECYCLE_SECONDS` (padrão `300`)
- Ajuda a renovar conexões antigas e reduzir falhas transitórias de SSL em produção

Variáveis opcionais para proxy reverso (URLs absolutas corretas com HTTPS):

- `PROXY_FIX_X_FOR` (padrão `1` em producao, `0` em desenvolvimento)
- `PROXY_FIX_X_PROTO` (padrão `1` em producao, `0` em desenvolvimento)
- `PROXY_FIX_X_HOST` (padrão `1` em producao, `0` em desenvolvimento)
- `PROXY_FIX_X_PORT` (padrão `0`)
- `PROXY_FIX_X_PREFIX` (padrão `0`)
- Ajuste esses valores quando houver mais de uma camada de proxy antes do Flask.

Após alterar variáveis, rode `make restart`.

Em `AMBIENTE_APLICACAO=producao`, a aplicação executa `db upgrade` automaticamente no boot.
Para bases legadas sem `alembic_version`, use `make db-update` (aplica stamp e upgrade de forma segura).

## Interfaces públicas

- Home: `/`
- Login: `/entrar`
- Iniciar login Google: `/auth/google/iniciar`
- Callback login Google: `/auth/google/callback`
- Logout: `/sair`
- Assinatura do manifesto (autenticada): `/apoios/assinar`
- Wiki pública: `/wiki/`
- Gestão da wiki (autenticada): `/wiki/gestao`
- Nova página wiki (autenticada): `/wiki/nova`
- Admin de usuários (apenas admin): `/admin/usuarios`
- API principal: `/api/contagem-regressiva`
	- Resposta JSON: `{"alvo": "<ISO datetime>"}`
- API legada (em transição): `/api/countdown`
	- Mantida temporariamente para compatibilidade
	- Use a rota nova em português

## Política de idioma (português first)

Este repositório adota `português first` para interfaces públicas e documentação.

- URLs públicas devem usar português, quando tecnicamente viável.
- Parâmetros públicos (rota, query string e campos JSON) devem usar português.
- Outros idiomas só são usados para termos consagrados de tecnologia e nomes de ferramentas.

Regras detalhadas: `docs/politica-idioma.md`.

Planejamento de crescimento: `docs/arquitetura-e-roadmap.md`.

## Próximas fases

O backlog técnico foi movido para `TODO.md`.