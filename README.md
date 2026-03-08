# maisumanostf.ong.br

Home da campanha em formato "Wiki de Urgência".

## Escopo atual (primeiro commit)

- Landing page SSR com narrativa da campanha
- Contador regressivo para a próxima vaga
- Gráfico dinâmico (Chart.js) com histórico + cenários (risco e campanha)
- Conteúdo institucional (resumo, cronologia, vagas e referências)
- Wiki dinâmica persistida em banco com edição autenticada por papel

Nesta fase a assinatura pública ainda não está ativa.

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

Variável opcional de conexão com banco (PostgreSQL):

- `DB_POOL_RECYCLE_SECONDS` (padrão `300`)
- Ajuda a renovar conexões antigas e reduzir falhas transitórias de SSL em produção

Após alterar variáveis, rode `make restart`.

Em `AMBIENTE_APLICACAO=producao`, a aplicação executa `db upgrade` automaticamente no boot.
Para bases legadas sem `alembic_version`, use `make db-update` (aplica stamp e upgrade de forma segura).

## Interfaces públicas

- Home: `/`
- Login: `/entrar`
- Logout: `/sair`
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