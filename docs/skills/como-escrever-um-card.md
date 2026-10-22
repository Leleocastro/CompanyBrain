# Como escrever um card e fazer o aceite (skill do po)

Skill do po. Cobre os dois procedimentos que se repetem: escrever um card com critérios verificáveis e fazer o aceite final. Origem de cada item: `caminho:linha` do CompanyBrain ou `§N` do `ck-contexto-do-projeto.md`. As colunas do board e os campos do corpo vêm das instruções do projeto no Multica — não estão versionados no repositório (ver "Perguntas em aberto").

## 1. Papel em 3 linhas

- Mantenho o backlog, escrevo critérios de aceite verificáveis, faço o aceite final e reabasteço o pipeline (`docs/produto/visao-do-produto.md:136`).
- Não decido solução técnica nem mexo em código: arquitetura é do tech-lead (`visao-do-produto.md:137`); implementação é dos devs.
- Só trabalho em card atribuído a mim, e handoff é ação (corpo + status + atribuição), nunca conversa (`visao-do-produto.md:141`).

## 2. Escrever um card

### 2.1 Antes de escrever

- Leia o card inteiro, as seções do `ck-contexto-do-projeto.md` que ele cita e a parte relevante do repositório. Só o necessário.
- Confronte o alvo do contexto com o que já existe: o que existe é base a aprimorar, não a refazer (`ck-contexto-do-projeto.md:16-18`; `visao-do-produto.md:7`).
- Nada inventado: código → `caminho:linha`; alvo → `§N` (`visao-do-produto.md:6`).
- O card deve caber num PR de até ~200 linhas; acima disso, volte ao tech-lead para quebrar (`docs/skills/checklist-revisao.md:9`).

### 2.2 Campos do corpo (nesta ordem)

| Campo | O que escrever |
|---|---|
| `Objetivo:` | Uma frase: o que muda e por quê. Sem solução técnica. |
| `História:` | Como <papel>, quero <x>, para <y> (`visao-do-produto.md:136`). |
| `Critérios de aceite:` | Dado/Quando/Então, um por comportamento (§2.3). |
| `Fase/Prioridade:` | Fase 0–3 (`§9`; `visao-do-produto.md:100-105`) e prioridade `urgent`/`high`/`medium`/`low`, com o motivo. |
| `Contexto:` | Seções `§N` e partes do repositório que o dev precisa ler. |
| `Premissas:` | Decisões pequenas e reversíveis, cada uma com o motivo. |
| `Bug:` | Só em card de defeito: passos, esperado vs. obtido, evidência, severidade, link do card original. |

Deixe vazios `Abordagem técnica:` (tech-lead), `Dev:` e `PR:` (executor). Não preencha campo de outro papel.

### 2.3 Critérios de aceite verificáveis

- Um critério = um comportamento observável. Formato: "Dado <estado>, quando <ação>, então <resultado>".
- Cada critério responde "como eu verifico isso?": artefato, caminho, saída de comando ou tela.
- Use os números e limites que já existem: planos, franquias e janela de backfill (`§8`; `ck-contexto-do-projeto.md:163-173`); fases e fora de escopo (`§9`; `ck-contexto-do-projeto.md:177-192`).
- Critério sem origem (`§N` ou `caminho:linha`) é chute: troque por pergunta em aberto.
- Diga também o que o card **não** faz: o que não muda e o que fica para depois (`ck-contexto-do-projeto.md:191-192`).
- Card `docs`: cite a pasta decidida pelo tech-lead (`docs/arquitetura/arquitetura-ck.md:122-135`), o teto de ~100 linhas (`docs/skills/checklist-revisao.md:53`) e o formato de PR `docs` (sem a KEY no título, no corpo ou na branch).

### 2.4 Labels e prioridade

- Área: `backend`, `frontend`, `infra`, `docs`, `bug`.
- Fase: `fase-0`, `fase-1`, `fase-2`, `fase-3` (`§9`; `visao-do-produto.md:100-105`).
- `retorno-1`/`retorno-2` só no handoff de devolução; o limite é 2 devoluções por card (`docs/skills/checklist-revisao.md:62`).

### 2.5 Quando mandar para `needs_spec` ou `refinement`

- `backlog`: card completo, sem assignee, parado até a fase.
- `refinement` + tech-lead: produto está claro, falta decisão técnica (`visao-do-produto.md:137`).
- `needs_spec` + po: falta informação de produto ou o critério está ambíguo/contraditório. Eu completo e devolvo a `refinement`.
- Produto, escopo, preço, contrato de API, segurança/LGPD ou credencial: não decido — `/note DÚVIDA:` para João Pedro e `blocked` (`visao-do-produto.md:135`).

## 3. Fazer o aceite

### 3.1 O que conferir em `acceptance`

- [ ] O card está `acceptance` e atribuído a mim; o PR está no campo `PR:` e foi mergeado.
- [ ] Percorri cada critério de aceite e aponto a evidência: diff/arquivo no `main`, saída de comando ou tela.
- [ ] O PR não trouxe mudança fora do escopo do card (`docs/skills/checklist-revisao.md:9`).
- [ ] Código: passou pelo QA em staging antes do merge (`docs/skills/checklist-revisao.md:63`). `docs` não passa por QA (`visao-do-produto.md:140`).
- [ ] Todo fato do artefato cita `caminho:linha` ou `§N`; divergência foi registrada, não "consertada" (`ck-contexto-do-projeto.md:18`).
- [ ] O não sabido está em "Perguntas em aberto"; nenhuma suposição virou fato (`visao-do-produto.md:8`).
- [ ] `docs`: arquivo no caminho acordado, curto e escaneável (`docs/skills/checklist-revisao.md:53`).

### 3.2 Aceitar ou devolver

- Aceito: `multica issue status <KEY> done --no-start`. Não reatribuo e não comento.
- Defeito técnico (não atende ao critério): label `retorno-N`, `refinement` + tech-lead; conta como devolução (`docs/skills/checklist-revisao.md:62`).
- Critério ambíguo que é meu: completo o card e devolvo a `refinement` + tech-lead.
- Discussão de código fica no PR, nunca no card (`visao-do-produto.md:139`).

### 3.3 Fim da Fase 0

- Ao aceitar o último card `fase-0`: uma passada de ajuste no backlog da Fase 1 com base nos documentos aceitos; consolidar todas as "Perguntas em aberto" num card único para João Pedro Rocha; parar.
- Não reabasteço nem puxo cards do `backlog`: a Fase 1 só começa por decisão de João Pedro (`visao-do-produto.md:135`; card CK-20).

## 4. Origem das afirmações

- `caminho:linha` para o que existe hoje; `§N` para o alvo (`visao-do-produto.md:6`).
- Divergência entre contexto e código: registre em "Perguntas em aberto", não resolva (`ck-contexto-do-projeto.md:18`).
- Lacuna do material: vira pergunta no próprio artefato, nunca suposição (`visao-do-produto.md:8`).

## Perguntas em aberto

1. As colunas do board e os campos do corpo só existem nas instruções do projeto no Multica; não há `AGENTS.md` no CompanyBrain. Versionar o fluxo em `docs/` ou manter fora do repositório?
2. Critério de "pronto" por fase não está definido (`§12.2`; `ck-contexto-do-projeto.md:273`). O aceite de fim de fase continua usando só os critérios do card e o doc de produto?
3. CK-21 (repositório novo greenfield ou CompanyBrain) aguarda decisão de João Pedro Rocha. Se o código migrar, os `caminho:linha` desta skill apontam para o lugar errado. Até a decisão, vale o CompanyBrain.
4. O "fim da Fase 0" desta skill vem das instruções do po e do card CK-20 (`blocked`), não de documento versionado. Confirmar o texto quando as perguntas da Fase 0 forem respondidas.
