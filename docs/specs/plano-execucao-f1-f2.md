---
title: "Plano de execução — Frentes 1 e 2 em blocos (motor e camada de IA)"
aliases: ["Plano de execução F1+F2", "Blocos do motor e da IA", "Ordem de serviço F1 F2", "Execução F1-F2"]
tags: [tcc, execucao, planejamento, git, engine, ia, llm, motor]
status: em-andamento
projeto: TCC
criado: 2026-08-25
---

> [!info] Spec: [[Projetos/EducMatch(Secretária)/spec-motor-e-ia-frentes-1-2|🧭 Spec F1+F2]] · Código do Bloco 0: [[Projetos/EducMatch(Secretária)/passo-a-passo-f1-01-f1-02|🔧 Passo a passo F1-01 e F1-02]] · Git: [[git-fluxo-aplicado-tcc|🎓 Fluxo de Git do TCC]] · Trilha irmã: [[handoff-autenticacao-colaborador 🟢|🤝 Handoff da autenticação]]

# 🗂️ Plano de execução — Frentes 1 e 2

> [!abstract] O que esta nota é
> A [[Projetos/EducMatch(Secretária)/spec-motor-e-ia-frentes-1-2|spec]] diz **o quê** e **por quê**. Esta diz **em que ordem, em qual branch e quando abrir PR** — o mesmo formato do [[handoff-autenticacao-colaborador 🟢|🤝 handoff da autenticação]], para as duas trilhas rodarem em paralelo sem se atropelar.
> Repositório auditado em **2026-08-25**, no commit `a628753`.

> [!danger] O repositório foi re-clonado e o trabalho de F1-01 e F1-02 se perdeu
> O `git reflog` tem uma entrada só (`clone: from ...`), o `origin` tem **apenas** `main` em `a628753`, e não existe outra cópia no disco. O commit `1068eb0`, que continha as duas tarefas, não é mais alcançável.
> **Não é um desastre:** as duas estão escritas linha a linha em [[Projetos/EducMatch(Secretária)/passo-a-passo-f1-01-f1-02|🔧 passo a passo]], que está commitado e publicado no vault. Refazer é mecânico. Mas é o **Bloco 0**, antes de qualquer outra coisa — e não só por sua causa: a migration do colega depende dela.

---

## 1️⃣ Estado real, hoje

| Peça | Estado |
|---|---|
| Quiz, engine, API, site | ✅ funcionando, commit `a628753` |
| Suíte de testes | ✅ **12 verdes** |
| F1-01 (limite configurável) · F1-02 (campos da camada de IA) | ❌ **perdidos no re-clone — Bloco 0** |
| F1-03 `build_payload` · F1-04 conjunto de empate e banda | ❌ nunca foram feitos |
| `quiz/llm/`, `quiz/delivery.py`, `quiz/prompts/` | ❌ não existem |
| Migrations do app `quiz` | só `0001_initial` |

> [!important] A migration `0002` é sua, e o colega está esperando por ela
> O [[handoff-autenticacao-colaborador 🟢|handoff da autenticação]] diz que a AUT-04 cria a `0003_quizattempt_user` com dependência em `0002_camada_ia`. **Essa premissa só passa a ser verdadeira quando o seu Bloco 0 entrar na `main`.** Se o colega chegar na AUT-04 antes, a migration dele nasce `0002` também — e duas `0002` no mesmo app é o único conflito desta divisão que o Git não resolve sozinho.

---

## 2️⃣ Git — como você entrega

Mesmo fluxo do resto do grupo ([[git-fluxo-aplicado-tcc|🎓 GitHub Flow]]): só `main` e branches curtas. Uma branch por bloco, com o escopo da frente no nome, conforme a convenção já registrada:

| Frente | Padrão |
|---|---|
| 1 · 🧮 Motor | `feat/motor-*` |
| 2 · 🤖 Camada de IA | `feat/ia-*` |

```bash
git checkout main && git pull
git checkout -b feat/motor-<assunto>
```

Commits em [[git-commits-e-mensagens|Conventional Commits]] com escopo `motor` ou `ia`. Um PR por bloco, mesclado antes de abrir o próximo.

> [!success] Seu revisor fixo agora existe
> Era pendência aberta desde a primeira spec: dono de duas frentes sem revisor. **A revisão vira mútua com a trilha de autenticação** — você revisa os PRs dele, ele revisa os seus. Some o risco de você aprovar o próprio trabalho por falta de alternativa.

---

## 3️⃣ A trilha — sete blocos

| Bloco | Tarefas | Branch | O que existe ao final |
|:---:|---|---|---|
| **0** | F1-01 + F1-02 | `feat/motor-campos-ia` | Limite no settings, modelo com os campos da camada de IA |
| **1** | F1-04 + F1-03 | `feat/motor-confianca-e-payload` | Conjunto de empate, banda e o `build_payload` — **contrato C1 fechado** |
| **2** | F2-01 + F2-02 + F2-03 | `feat/ia-provider-offline` | Protocolo, `FakeProvider` e configuração por `.env` |
| **3** | F2-04 + F2-05 + F2-06 | `feat/ia-prompt-e-validacao` | Prompt em arquivo e o validador das 5 regras |
| **4** | F2-07 + F2-08 + F2-09 | `feat/ia-entrega` | Orquestração, Gemini real e o endpoint do contrato C3 |
| **5** | F1-05 + F2-10 | `feat/motor-sensibilidade` · `feat/ia-experimento` | **A evidência**: CSV de sensibilidade e CSV do experimento |
| **6** | F1-06 + F1-07 + F1-08 + F2-11 | `feat/motor-recalibracao` · docs | Recalibração com o catálogo real e os capítulos escritos |

> [!warning] Se algo tiver que cair, não pode ser o Bloco 5
> F1-05 e F2-10 são as duas tarefas que produzem **número**, e são as que a banca mais valoriza. Quando o calendário apertar, a tentação é cortar delas porque "o sistema já funciona" — mas sistema funcionando sem medição é projeto de portfólio, não TCC. Corte tela, corte polimento de texto; a evidência fica.

---

## 4️⃣ Bloco 0 — refazer F1-01 e F1-02

**Siga [[Projetos/EducMatch(Secretária)/passo-a-passo-f1-01-f1-02|🔧 Passo a passo F1-01 e F1-02]] do começo ao fim.** Ela continua válida palavra por palavra.

> [!success] Os números de linha da nota voltaram a bater
> A nota foi escrita contra o commit `a628753`, e o re-clone devolveu o repositório exatamente para lá. É o raro caso em que perder trabalho não invalidou a documentação: você pode colar os trechos sem conferir deslocamento de linha.

### O que mudou desde que aquela nota foi escrita

| # | Mudança | Onde já está refletido |
|---|---|---|
| 1 | `confidence_level` virou **`confidence_band`** (`alta / media / baixa`) e nasceu **`tie_set`** (`JSONField(default=list)`) | ✅ **já corrigido na própria nota** — commit `83ff466` |
| 2 | **F1-04 passou na frente do F1-03** — `build_payload` não fecha sem os campos de confiança | ✅ callout na nota e na spec |
| 3 | O contrato **C1 ganhou os blocos `respostas` e `confianca`** | Spec, seção 2 — afeta o **Bloco 1**, não o 0 |
| 4 | O contrato **C2 ganhou a 5ª regra** (`principal` dentro do `conjunto_empate`) | Spec, seção 2 — afeta o **Bloco 3** |
| 5 | O limiar fixo de 0,05 saiu do prompt e virou conjunto de empate calculado pela engine | Spec, seção "O papel da IA" |

Ou seja: **para o Bloco 0 não mudou nada.** As mudanças 3, 4 e 5 são contrato e só entram nos blocos seguintes. A única coisa que a nota já absorveu e que vale conferir ao colar é a linha do `tie_set` — se você vir `confidence_level` em algum lugar, está lendo uma versão velha.

> [!important] Avise no grupo assim que este PR mesclar
> Uma frase basta: *"a `0002_camada_ia` está na main — quem for criar migration no app `quiz` agora cria a `0003`"*. É o que destrava a AUT-04 do colega.

**Pronto quando:** `makemigrations --check --dry-run` limpo · **14 testes verdes** · uma tentativa antiga abre no site sem erro.

---

## 5️⃣ Bloco 1 — F1-04 + F1-03 · confiança e o payload

O bloco que fecha o **contrato C1** e libera todo o resto da camada de IA.

**F1-04 — duas funções puras em `quiz/engine.py`:**

```python
EPSILON_EMPATE = 0.05

def conjunto_empate(ranking, epsilon=EPSILON_EMPATE): ...
def banda(score_top1): ...
```

Mais a gravação de `confidence_gap`, `confidence_band` e `tie_set` no `QuizAttempt`, dentro do `recommend`.

**F1-03 — `build_payload(attempt)` em `quiz/delivery.py`**, no formato exato da seção 2 da spec, incluindo os blocos `respostas` e `confianca`.

> [!warning] Os cortes da banda ainda não têm número — e não devem ganhar um por chute
> O ε tem significado matemático. Os cortes de banda são **escolha de produto**: a partir de qual score o sistema tem o direito de soar confiante ao recomendar uma formação a alguém. Deixe uma constante única, marcada com um `TODO` apontando para F1-05, e defina depois de ver a distribuição real de scores. Chutar `0.30` e `0.70` agora é criar mais um número indefensável — exatamente o erro que o 0,05 cometeu.

> [!tip] Escreva as duas funções puras primeiro e teste sem banco
> `conjunto_empate` e `banda` recebem números e devolvem números — `SimpleTestCase`, milissegundos, sem criar tabela. É a mesma separação puro/impuro que já sustenta a engine, e é o que permite testar o caso automotivo (conjunto de 1) e o elétrico (conjunto ≥ 2) sem montar tentativa nenhuma.

**Pronto quando:** conjunto de empate dá 1 no perfil automotivo e ≥ 2 no elétrico · banda testada nas três faixas · `build_payload` comparado campo a campo com o JSON do C1.

---

## 6️⃣ Bloco 2 — F2-01 + F2-02 + F2-03 · a camada offline

Protocolo `LLMProvider`, `FakeProvider`, `get_provider()` e as variáveis `LLM_*` no `.env`.

> [!important] Comece pelo dublê, não pelo Gemini
> É contraintuitivo, e é o que blinda o cronograma: se a credencial atrasar, os Blocos 2, 3 e metade do 4 já estão prontos e testados. Quando a chave chegar, é plugar.

> [!warning] `LLM_ENABLED=false` precisa de teste, não de boa-fé
> É o botão de pânico da defesa. Botão de pânico que ninguém apertou desde que foi instalado não é mitigação, é esperança. Teste explícito: com a flag desligada, nada instancia provider, nada toca rede, e a tela responde 200 com o resultado do motor.

> [!note] `settings.py` — escreva no fim do arquivo, num bloco comentado
> O colega está mexendo no mesmo arquivo na trilha de autenticação, logo abaixo de `AUTH_PASSWORD_VALIDATORS`. Regiões diferentes = merge sem conflito. Se os dois escreverem no mesmo lugar, o Git pede intervenção manual à toa.

**Pronto quando:** import limpo sem nenhum SDK instalado · `FakeProvider` devolve C2 válido para qualquer payload · flag desligada não instancia nada.

---

## 7️⃣ Bloco 3 — F2-04 + F2-05 + F2-06 · prompt e validação

> [!danger] A regra 2 do prompt v1 precisa ser reescrita **antes** de virar arquivo
> O texto em [[Projetos/EducMatch(Secretária)/prompt-padrao-recomendacao|📝 Prompt v1]] ainda fala em *"diferença de score menor que 0,05"*. Com o conjunto de empate isso sai e entra: *"escolha o principal entre os ids listados em `conjunto_empate`; se a lista tiver um id só, ele é o principal"*. Como o prompt ainda **não foi copiado para arquivo**, a correção é barata agora e cara depois de a v1 estar congelada — a política de versionamento proíbe editar versão já usada em resultado gravado.

O `DeliverySerializer` implementa as **5** regras do C2. A quinta é a que muda o jogo: com o conjunto de empate vindo no payload, o servidor sabe exatamente quem podia ser promovido. Deixa de ser instrução em português dentro do prompt e vira validação verificável.

**Pronto quando:** 7 testes de saída maliciosa, todos terminando em fallback e **nenhum** em 500.

---

## 8️⃣ Bloco 4 — F2-07 + F2-08 + F2-09 · entrega, Gemini e o endpoint

Orquestração com fallback, `GeminiProvider` com `temperature=0`, timeout de 8s, cache, metadados — e o endpoint do contrato **C3**.

> [!important] O C3 é o que destrava a Frente 4
> Enquanto ele não existir, a F4 não consegue desenhar a tela de entrega sem adivinhar formato. O campo `pronto: false` é o que permite a ela montar **uma** tela só: enquanto for falso, mostra o resultado do motor; quando virar verdadeiro, troca o texto. **Priorize F2-09 dentro do bloco** — é o único item da sua trilha que outra pessoa está esperando.

> [!warning] Reprodutibilidade não é só `temperature=0`
> O que garante a banca é o **cache**: mesma tentativa, mesma resposta, sem nova chamada. Antes da apresentação, rode os perfis de demonstração uma vez para populá-lo.

**Pronto quando:** uma tentativa real volta com texto do Gemini e `latency_ms` gravado · a segunda execução do mesmo perfil sai do cache com `cache_hit=True` · a F4 monta a tela sem te perguntar nada.

---

## 9️⃣ Bloco 5 — F1-05 + F2-10 · a evidência

**F1-05** — comando de análise de sensibilidade: o que acontece com o ranking quando um peso vai de 4 para 5. Saída em CSV.

**F2-10** — `manage.py run_experiment --n=30`: N perfis pelos dois caminhos, com taxa de divergência, latência, taxa de fallback e tokens.

> [!success] Agora o experimento mede um fenômeno frequente, não uma raridade
> Com o limiar antigo, divergência seria evento raro e o capítulo comparativo daria um número sem graça. Com o conjunto de empate, a LLM decide sempre que o cálculo empata — e em três dos quatro perfis de aceite ele empata. **A divergência vira o fenômeno central do capítulo**, com o `tie_set` gravado permitindo auditar se cada uma era permitida.

> [!question] Você não deve avaliar sozinho as divergências
> É a sua camada de IA sendo julgada. A avaliação humana (*melhorou · indiferente · piorou*) precisa de duas pessoas de outras frentes — o colega da autenticação é candidato natural, já que não tem interesse no resultado.

**Pronto quando:** os dois CSVs existem e as tabelas de métricas estão fechadas.

---

## 🔟 Bloco 6 — recalibração e escrita

F1-06 (recalibração com os 18 cursos reais) **depende da Frente 3** e é o único item da sua trilha travado por outra pessoa. F1-07, F1-08 e F2-11 são teste e escrita.

> [!warning] Se a F3 atrasar, este bloco esvazia — puxe trabalho, não espere
> O contorno se decide antes: adiante F1-07 (bateria de testes) e a redação de F1-08 com os dados fictícios, deixando só os números para trocar. O que não pode acontecer é você parar esperando catálogo.

> [!success] A escrita ficou mais barata do que a spec original previa
> O vault ganhou as pastas `Recomendação`, `Inteligência Artificial`, `Metodologia Científica` e `Testes`. Cada tarefa sua tem leitura de apoio mapeada na seção 6 da [[Projetos/EducMatch(Secretária)/spec-motor-e-ia-frentes-1-2|spec]] — escrever deixou de ser pesquisar do zero e virou amarrar código a nota que já existe.

---

## 1️⃣1️⃣ Rodando em paralelo com a trilha de autenticação

### O que cada um toca

| Área | AUT (colega) | F1/F2 (você) |
|---|:---:|:---:|
| `accounts/`, `templates/accounts/`, `base.html`, `style.css` | ✅ | — |
| `quiz/engine.py`, `quiz/delivery.py`, `quiz/llm/`, `quiz/prompts/` | — | ✅ |
| `quiz/models.py` + migration do `quiz` | ⚠️ AUT-04 | ⚠️ **Bloco 0** |
| `config/settings.py` | ⚠️ bloco de auth | ⚠️ bloco de LLM |
| `quiz/views.py` | ⚠️ AUT-05 | ⚠️ F2-09 |
| `templates/quiz/result.html` | ⚠️ AUT-08 | (F4) |

### As quatro regras

1. **Bloco 0 primeiro, e avisado no grupo.** É o único ponto de serialização das duas trilhas.
2. **`settings.py` em blocos separados e comentados** — o dele depois dos validadores de senha, o seu no fim.
3. **Ninguém cria migration no app `quiz` sem avisar.** Depois da `0002` (sua) e da `0003` (dele), a F2 não adiciona nenhuma.
4. **Quando o Bloco 1 dele mesclar, apague o banco e rode os seeds.** Dois minutos, uma vez só — é o preço do `AUTH_USER_MODEL`.

> [!tip] O que pode começar hoje, ao mesmo tempo
> Seu **Bloco 0** e o **Bloco 1 dele** não se encontram em lugar nenhum além do `settings.py`. As duas trilhas arrancam juntas; o primeiro encontro de verdade é a AUT-04, e até lá a sua `0002` já estará na `main`.

---

## 1️⃣2️⃣ O que continua em aberto

> [!todo] Nada disto trava o Bloco 0
> 1. **Ratificar os eixos D e C** (conjunto de empate + banda) — é mudança de contrato, então é decisão de grupo. Trava o **Bloco 1**.
> 2. **Top-5 ou top-3** — o `RECOMMENDATION_LIMIT` do Bloco 0 nasce com 5; mudar depois é uma linha, mas o número precisa ser decidido antes do prompt virar arquivo (Bloco 3).
> 3. **A camada de IA nasce para 18 cursos ou já para 180?** Se for 180, o C1 precisa dos atributos discriminantes (nível, carga horária, pré-requisito, eixo). Trava o **Bloco 1**.
> 4. **Quem guarda a credencial** do Gemini — trava só o Bloco 4.
> 5. **Dono da Frente 3** — trava o Bloco 6.

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/spec-motor-e-ia-frentes-1-2|🧭 Spec F1+F2]] — contratos, backlog e a base conceitual de cada tarefa
- [[Projetos/EducMatch(Secretária)/passo-a-passo-f1-01-f1-02|🔧 Passo a passo F1-01 e F1-02]] — o código do Bloco 0
- [[handoff-autenticacao-colaborador 🟢|🤝 Handoff da autenticação]] — a trilha que roda em paralelo
- [[git-fluxo-aplicado-tcc|🎓 Fluxo de Git do TCC]] · [[Projetos/EducMatch(Secretária)/divisao-de-trabalho-tcc|👥 Divisão de trabalho]]
- [[Projetos/EducMatch(Secretária)/camada-ia-plano-implementacao|🧩 Plano da camada de IA]] · [[Projetos/EducMatch(Secretária)/prompt-padrao-recomendacao|📝 Prompt v1]] · [[engine-matching-cosseno 🟢|🧮 Engine]]
- [[Projetos/EducMatch(Secretária)/TCC|🎓 TCC]] · [[Projetos|🚀 Projetos]]
