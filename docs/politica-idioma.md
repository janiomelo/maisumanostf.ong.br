# Politica de idioma do repositorio

## Objetivo

Padronizar comunicacao, interfaces publicas e documentacao em portugues, reduzindo ambiguidade e custo de manutencao.

## Regra principal

- Politica oficial: `portugues first`.
- Outros idiomas so podem ser usados para termos consagrados e amplamente adotados por comunidades tecnicas.

## Escopo obrigatorio (fase atual)

- URLs publicas.
- Parametros publicos em URL (path e query string).
- Campos publicos em respostas JSON.
- Documentacao do projeto.

## Convencoes

- Prefira nomes claros em portugues: exemplo `contagem-regressiva`, `alvo`, `participe`.
- Evite misturar portugues e ingles na mesma interface publica.
- Quando houver rota legada em outro idioma, manter somente durante periodo de transicao e com aviso de deprecacao.

## Excecoes permitidas

- Nomes proprios de bibliotecas, frameworks, protocolos e ferramentas: `Flask`, `Chart.js`, `JSON`, `Docker`, `HTTP`.
- Siglas institucionais ou juridicas consolidadas: `STF`, `CNJ`, `OAB`.

## Aplicacao incremental

- Mudancas devem priorizar interfaces publicas e documentacao.
- Refatoracoes internas de codigo para portugues podem ocorrer em etapas posteriores, sem quebrar compatibilidade desnecessaria.
