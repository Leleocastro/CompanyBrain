# Refinar e quebrar um card — skill do tech-lead

Procedimento do tech-lead para pegar um card em `refinement`, preencher `Abordagem técnica:` e rotear ao dev — quebrando o card quando não cabe num PR. Cada afirmação sobre o projeto cita a origem: `caminho:linha` do CompanyBrain ou `§N` do `ck-contexto-do-projeto.md`. `R1–R16` são as regras de fluxo do papel (instruções do agente no Multica, não do repositório). O repositório manda para "como é hoje"; o contexto manda para "como deve ser" (`ck-contexto-do-projeto.md:7-18`).

## 1. Ler antes de decidir

- [ ] Leia o card inteiro: objetivo, critérios de aceite, contexto, `Dev:` e labels.
- [ ] Leia só as seções do contexto que o card cita (`§5` em `ck-contexto-do-projeto.md:75`; `§7` em `:150`; `§9` em `:177`).
- [ ] Veja a lacuna que originou o card na tabela de alvo vs. hoje (`docs/arquitetura/arquitetura-ck.md:100`) e o estado da área em `docs/arquitetura/*-estado-atual.md`.
- [ ] Cheque as perguntas técnicas já abertas antes de criar outra (`docs/arquitetura/arquitetura-ck.md:157`).

## 2. Preencher `Abordagem técnica:`

Três blocos curtos, cada linha com origem.

**Contrato**
- Descreva entrada e saída antes do código: rota, método, payload, erros.
- Se tocar a API existente, parta dos modelos Pydantic `Node`, `Edge`, `PaginatedNodes`, `PaginatedEdges`, `NodeDetail` (`api/mock_graph/main.py:19-47`); mudar campo é mudar contrato.
- Se tocar a ingestão, preserve `Document`/`BaseConnector` (`ingestao/connectors/base.py:10-48`) e o registry (`ingestao/connectors/__init__.py:11`).
- Não invente rota pública: `§5` define auth dupla, `tenant_id` e rate limit, não a lista de endpoints (`ck-contexto-do-projeto.md:75`).

**Dependências**
- Liste os cards dos quais este depende, com a linha da tabela de lacunas que o originou (`docs/arquitetura/arquitetura-ck.md:100`).
- Diga o que é construção nova e o que se reaproveita: da Fase 1, só o conector GitHub e os contratos da ingestão se aproveitam (`docs/arquitetura/arquitetura-ck.md:17-20`).
- Se a dependência não está pronta, escreva se o card começa por ela ou espera.
- Não crie banco, fila ou transporte fora de `§5` (Postgres, Qdrant, Redis, S3) (`ck-contexto-do-projeto.md:75`).

**Definição de pronto**
- Código: teste que falha antes e passa depois, mais lint/format (`pyproject.toml:1-27`; `.pre-commit-config.yaml:2-39`).
- CI: o workflow do serviço tocado passa (`.github/workflows/service-*.yml`).
- Isolamento: todo dado lido/gravado carrega `tenant_id` (§7, `ck-contexto-do-projeto.md:150`); o log também (`§5` Observabilidade, `ck-contexto-do-projeto.md:127`).
- Doc: origem `caminho:linha`/`§N` e lacunas em "Perguntas em aberto" (`R16`; `ck-contexto-do-projeto.md:7-18`).
- Não há critério de pronto por fase no material (`ck-contexto-do-projeto.md:273`): a definição de pronto do card é o substituto até o po definir.

## 3. Roteamento: label e `Dev:`

| Entrega do PR | Label | `Dev:` |
|---|---|---|
| API, ingestão, pipeline, banco, auth | backend | dev-backend |
| `web/` (React 18 + Vite, `docs/arquitetura/arquitetura-ck.md:32`): wiki, chat, painel | frontend | dev-frontend |
| Docker, CI, deploy, ambientes | infra | devops |
| Documento ou skill em `docs/` | docs | quem escreve (tech-lead, reviewer ou qa) |

- Uma label por card (convenção de fluxo, como `R1–R16`); se pede duas áreas, tem duas responsabilidades — quebre (§4).
- `docs/` na raiz, uma pasta por tipo (`docs/arquitetura/arquitetura-ck.md:122`); código por serviço (`README.md:3-8`).
- Só atribua quando `Abordagem técnica:`, label e `Dev:` estiverem preenchidos; depois `todo` + o agente do `Dev:` (`R2`, `R13`).

## 4. Quando quebrar

- Quebre quando o card tem mais de uma responsabilidade ou o PR passaria de ~200 linhas (`R9`).
- Um card por entrega verificável; cards planos, sem `--parent`, ligados por label e projeto (`R12`).
- Cada card novo repete Objetivo, Critérios de aceite e Contexto, já com `Abordagem técnica:`; ajuste ou cancele o original.
- Quebre pela fronteira do serviço — `ingestao`, `api`, `web` (`docs/arquitetura/arquitetura-ck.md:26`) e os Dockerfiles por serviço em `docker/` (`docs/arquitetura/arquitetura-ck.md:51`) —, não por etapa de execução.
- Se a quebra revelar dependência entre os novos cards, diga a ordem no `Contexto:` de cada um.

## 5. Quando mandar para `needs_spec`

- Critério de aceite ambíguo, objetivo sem resultado observável ou escopo que só o po fecha → `needs_spec` + po (`R2`; papel do po).
- Pergunta de produto, contrato público, segurança/LGPD, custo ou terceiros que muda o escopo → `blocked` + João Pedro Rocha (`R5`, `R15`); não decida sozinho (`ck-contexto-do-projeto.md:17-18`).
- Dúvida pequena e reversível (nome, formato, detalhe de implementação): decida, registre em `Premissas:` e siga (`R15`).
- Na Fase 0, dúvida de conteúdo não bloqueia: vira "Perguntas em aberto" no documento (`docs/arquitetura/arquitetura-ck.md:157`).

## 6. Devolução excedida (R7)

- Devolução do reviewer/qa chega com `retorno-1` ou `retorno-2`; até duas, o card volta ao dev (`R7`; o feedback fica no PR, `R6`).
- Na terceira, o card vem para `refinement` e decide-se uma vez: reescrever o card, quebrar (§4) ou escalar ao humano (`R5`, `R7`).
- Não devolva de novo ao mesmo dev sem mudar algo no card: reescrita ou quebra precisam aparecer em `Abordagem técnica:` e nos critérios de aceite.

## Perguntas em aberto

- `R1–R16` não existem no repositório: ficam nas instruções do agente no Multica. Esta skill cita o número da regra, como `docs/skills/checklist-revisao.md` já faz; não há `caminho:linha` para elas.
- O card do tech-lead cita `AGENTS.md do projeto`; não há `AGENTS.md` no `main` (`git ls-tree -r origin/main --name-only` não retorna esse arquivo). Onde essas regras são versionadas?
- Não há rótulo de "pronto" por fase (`ck-contexto-do-projeto.md:273`); a definição de pronto por card é proxy até o po definir.
- `§5` não lista endpoints nem o contrato da API alvo (`ck-contexto-do-projeto.md:75`); o único contrato verificável hoje é o mock (`api/mock_graph/main.py:19-47`). Divergência registrada, não resolvida aqui.
- A tabela de labels não tem agente para `docs`; o `Dev:` de card `docs` fica com quem escreve. Confirmar se o po quer um `Dev:` fixo.
- CK-21 (repositório novo greenfield vs. CompanyBrain) e CK-20 (perguntas da Fase 0) pendentes: até a decisão de João Pedro Rocha, vale o CompanyBrain.
