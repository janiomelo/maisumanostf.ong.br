# Projeto: Historico de Alteracoes da Wiki

## Objetivo

Implementar versionamento de paginas wiki para permitir:

- auditoria de quem alterou;
- comparacao entre revisoes;
- recuperacao de versoes anteriores.

## Escopo proposto

1. Persistencia de revisoes
- Nova tabela `wiki_revisoes` contendo:
  - `id`
  - `wiki_pagina_id`
  - `titulo`
  - `conteudo_markdown`
  - `autor_email`
  - `tipo_evento` (`criacao`, `edicao`, `restauracao`)
  - `criado_em`

2. Autorias por pagina
- Adicionar em `wiki_paginas`:
  - `autor_email_criacao` (autor original)
  - `autor_email_ultima_edicao` (autor da ultima alteracao)

3. Fluxo de gravacao
- Em toda criacao/edicao de pagina:
  - atualizar `wiki_paginas`;
  - inserir snapshot completo em `wiki_revisoes` na mesma transacao.

4. Interfaces administrativas
- Tela de historico por pagina:
  - lista de revisoes com data e autor;
  - visualizacao de conteudo da revisao;
  - restauracao para versao anterior.

5. Seguranca e governanca
- Restauracao apenas para `editor` e `admin`.
- Registro de evento de restauracao em `wiki_revisoes`.

## Fases sugeridas

### Fase 1 (MVP tecnico)
- Criar tabela `wiki_revisoes` e gravar revisao em toda alteracao.
- Exibir historico simples (data + autor) na pagina de edicao.

### Fase 2 (Operacional)
- Exibir diff basico entre versoes (linha a linha).
- Restauracao de versao anterior com confirmacao.

### Fase 3 (Governanca)
- Filtros por autor, periodo e tipo de evento.
- Exportacao de trilha de auditoria.

## Riscos e cuidados

- Crescimento de armazenamento por snapshots completos.
- Necessidade de sanitizacao continua no render markdown.
- Garantir transacao atomica entre pagina atual e revisao.

## Criterios de pronto (MVP)

- Toda criacao/edicao gera um registro em `wiki_revisoes`.
- Historico exibido na tela de edicao da pagina.
- Testes unitarios e funcionais cobrindo criacao, edicao e leitura de historico.
