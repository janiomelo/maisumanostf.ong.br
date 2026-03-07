# Arquitetura e Roadmap de Crescimento

## Objetivo

Definir uma base tecnica para crescimento da plataforma em etapas, sem quebrar as interfaces publicas atuais.

Sequencia aprovada:
1. Estrutura
2. Wiki
3. Apoios e defesas (demais modulos)

## Estado atual

- Aplicacao Flask SSR com uma home publica.
- Rotas publicas principais: `/` e `/api/contagem-regressiva`.
- Sem banco de dados, sem autenticacao e sem painel.
- CI de testes ativo e cobertura minima obrigatoria.

## Principios de evolucao

- Preservar compatibilidade das rotas publicas existentes.
- Evoluir por fases curtas com testes automatizados em cada fase.
- Seguir politica `portugues first` para interfaces publicas e documentacao.
- Evitar adicionar infraestrutura sem necessidade comprovada.

## Fase 1 - Estrutura (agora)

Objetivo: organizar o codigo para crescer, sem introduzir funcionalidades novas para usuario final.

### Entrega desta fase

- Separacao por dominios com blueprints:
  - `publico` (paginas abertas)
  - `wiki` (publicacao/consulta)
  - `apoios` (fluxos futuros)
  - `defesas` (fluxos futuros)
  - `admin` (gestao)
- Camada de dominio para regras de negocio reutilizaveis.
- Camada de acesso a dados preparada para ORM/migrations.
- Organizacao de templates por namespace (`publico/`, `wiki/`, `admin/`).
- Estrutura de papeis inicial: `nao_editor`, `editor`, `admin`.

### Resultado esperado

- Codigo desacoplado para habilitar Wiki sem retrabalho.
- Base pronta para persistencia e autorizacao na fase seguinte.

## Fase 2 - Wiki

Objetivo: publicar e organizar conhecimento em formato wiki.

### Primeira entrega de conteudo

- Pagina inicial de wiki: **Estatuto Basico Ampliado**.

### Modelo de permissao inicial

- Leitura: publica.
- Edicao/publicacao: `editor` e `admin`.
- `nao_editor` nao edita.

### Evolucao futura de papeis

- Permissoes granulares por acao (criar, revisar, publicar, arquivar).
- Possibilidade de novos papeis sem quebrar o modelo inicial.

## Fase 3 - Apoios e Defesas

Objetivo: ativar participacao com seguranca e moderacao.

### Decisoes iniciais registradas

1. Apoios exigem autenticacao obrigatoria na primeira versao.
- Recomendacao: e-mail magico (link unico com expiração curta).

2. Defesas nao devem ser publicadas imediatamente.
- Recomendacao: moderacao manual inicial (fila de revisao).

3. Estrutura de papeis deve separar claramente editores e nao editores.
- Implementar RBAC simples desde o inicio para evitar retrabalho.

## Banco de dados: decisao

Recomendacao: **Postgres no Railway** como banco principal.

### Por que Postgres

- Dados relacionais (usuarios, apoios, defesas, wiki, historico, auditoria).
- Consultas e relatorios com filtros e agregacoes.
- Integridade transacional para fluxos de apoio/autenticacao.
- Migrations previsiveis para evolucao da estrutura.

### E o key-value do Railway?

- Nao recomendado como banco principal para este produto.
- Pode entrar depois para cache/rate limiting se houver necessidade real.

## E-mail transacional e caixa de entrada (dominio proprio)

Pergunta: "da para usar algo no Railway?"

Resposta curta:
- Railway nao oferece caixa de e-mail corporativa nativa (inbox/aliases) como produto principal.
- Para disparo de e-mail da aplicacao, o caminho mais seguro e usar provedor transacional externo.

### Definicoes fechadas para discussao de governanca e infra

1. Caixa de entrada humana
- Provedor: **Zoho Mail (Forever Free)**.
- Custo inicial: **R$ 0,00**.
- Capacidade: ate 5 contas com 5 GB cada no dominio da campanha.
- Endereco oficial inicial: `contato@maisumanostf.ong.br`.
- Aliases de lancamento: `apoio@maisumanostf.ong.br` e `wiki@maisumanostf.ong.br`, redirecionados para a inbox principal.

2. Disparo transacional da aplicacao
- Provedor recomendado: **Resend** (alternativa: Postmark).
- Faixa gratuita inicial: ate 3.000 e-mails/mes.
- Uso principal: e-mail magico, confirmacoes e notificacoes da aplicacao.
- Diretriz: priorizar entregabilidade e simplicidade de integracao com Flask.

3. Politica de link magico
- Validade do token: **15 a 30 minutos**.
- Regra de seguranca: nao exceder 30 minutos para reduzir risco de uso indevido.

4. Eventos minimos para auditoria de envio
- Armazenar: `id_usuario`, `timestamp_envio`, `status_envio` (enviado/erro), `ip_solicitante`.
- Armazenamento previsto para esta trilha: **Supabase** (camada de auditoria de eventos).

### Desenho de DNS para entregabilidade

No provedor DNS (Registro.br ou Cloudflare), configurar:

| Tipo | Entrada | Destino (exemplo) | Funcao |
| --- | --- | --- | --- |
| `MX` | `@` | `mx.zoho.com` | Receber e-mails humanos |
| `TXT` | `_spf` | `v=spf1 include:zoho.com include:resend.com ~all` | Autorizar remetentes |
| `CNAME` | `resend._domainkey` | chave fornecida pelo Resend | Assinatura DKIM |
| `TXT` | `_dmarc` | `v=DMARC1; p=quarantine;` | Politica anti-spoofing |

Observacao:
- Ajustar valores exatos de `MX` e `DKIM` conforme o painel do Zoho/Resend no momento da configuracao.
- A politica DMARC pode evoluir de `quarantine` para `reject` apos monitoramento inicial.

## Modelo de dados minimo (quando entrar DB)

- `usuarios`
- `papeis`
- `usuarios_papeis`
- `apoios`
- `defesas`
- `defesas_moderacao`
- `wiki_paginas`
- `wiki_revisoes`
- `auditoria_eventos`

## Riscos e mitigacoes

- Spam e abuso em formularios: habilitar moderacao e rate limit antes de abrir fluxo publico de defesas.
- Retrabalho de permissao: iniciar com RBAC basico ja na fase de estrutura.
- Dependencia de e-mail: homologar provedor transacional em ambiente de teste antes da entrada de apoios.

## Respostas consolidadas para o grupo

1. Apoios exigem autenticacao obrigatoria na primeira versao?
- **Sim.** Implementar com e-mail magico.

2. Defesas sao publicadas imediatamente?
- **Nao.** Publicacao inicial somente apos moderacao manual.

3. Wiki tera edicao por quem no inicio?
- **Apenas `editor` e `admin`**. `nao_editor` so leitura.

4. Provedor de e-mail transacional sera definido agora?
- **Sim.** Definir Resend (com Postmark como alternativa).

## Checklist de decisao antes de implementar Wiki

1. Confirmar estrutura de papeis inicial (`nao_editor`, `editor`, `admin`).
2. Definir slug e escopo da primeira pagina: `estatuto-basico-ampliado`.
3. Definir formato da wiki (Markdown persistido + render SSR).
4. Definir se revisao para publicacao sera obrigatoria ja na primeira versao.

## Proximos passos imediatos

1. Executar Fase 1 (estrutura) sem mudar comportamento publico.
2. Revisar este documento e ajustar regras de papel.
3. Abrir implementacao da Wiki como proxima entrega.
