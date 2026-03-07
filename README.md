# maisumanostf.ong.br

Home da campanha em formato "Wiki de Urgência" (fase 1).

## Escopo atual (primeiro commit)

- Landing page SSR com narrativa da campanha
- Contador regressivo para a próxima vaga
- Gráfico dinâmico (Chart.js) com histórico + cenários (risco e campanha)
- Conteúdo institucional (resumo, cronologia, vagas e referências)

Nesta fase não há banco de dados, autenticação ou coleta de assinaturas.

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
```

## Configuração por ambiente

As variáveis da home ficam no `.env`:

- `COUNTDOWN_TARGET` (ISO datetime)
- `VACANCY_FUX_DATE` (YYYY-MM-DD)
- `VACANCY_CARMEN_DATE` (YYYY-MM-DD)
- `VACANCY_GILMAR_DATE` (YYYY-MM-DD)

Após alterar variáveis, rode `make restart`.

## Próximas fases

O backlog técnico foi movido para `TODO.md`.