---
title: "Apresentação · Engine de recomendação (cosseno)"
aliases: ["Engine na apresentação", "Motor de recomendação", "Cosseno explicado"]
tags: [tcc, apresentacao, engine, cosseno, recomendacao, metricas]
status: pronto
projeto: TCC
atualizado: 2026-10-08
---

> [!info] Apresentação: [[README|🎤 Roteiro]] · **🧮 Engine** · [[backend|⚙️ Backend]] · [[frontend|🎨 Front]] · [[ia|🤖 Camada de IA]] · [[demo-e-perguntas|🎬 Demo e banca]]

# 🧮 Engine de recomendação: o coração do EducMatch

> [!abstract] O que esta nota é
> Tudo o que a banca pode perguntar sobre **como o sistema escolhe os cursos**: as funções de `quiz/engine.py`, uma conta feita à mão, um exemplo real do banco e as **métricas medidas em 5.000 perfis simulados**.
> **É a parte em que o grupo deve gastar mais tempo.** Todo integrante precisa saber explicar esta nota, não só quem escreveu o código.

> [!success] Os números desta nota foram medidos, não estimados
> Medidos em 2026-10-08 com os seeds reais (12 áreas, 20 cursos, 10 questões), em 5.000 quizzes respondidos por sorteio (semente fixa = 1), usando as próprias funções da engine. A distribuição de confiança se reproduz com o comando do projeto:
> ```bash
> python manage.py medir_empate --n 5000
> ```
> As outras métricas (quem fica em 1º, tamanho do `tie_set`, tempo) saíram de uma simulação com as mesmas funções e a mesma semente.

---

## 🎯 1. A ideia em uma frase

> [!quote] Para decorar
> O aluno vira um **vetor de perfil** (quanto ele pontuou em cada área). Cada curso também é um **vetor** (quanto ele pertence a cada área). A engine mede o **ângulo** entre os dois com a **similaridade de cosseno**: quanto menor o ângulo, mais o curso combina com o aluno.

```
Quiz (10 questões × 4 alternativas)
   │  cada alternativa soma pesos em áreas  (Peso_alternativa, 0 a 5)
   ▼
Vetor do PERFIL  {eletrica: 18, metalurgia: 14, eletromecanica: 13, ...}
   │
   │      ┌── Vetor de cada CURSO  {eletrica: 5, eletromecanica: 3, ...}  (Peso_curso, 0 a 5)
   ▼      ▼
   cosseno(perfil, curso)  ──►  afinidade de 0 a 1  ──►  "86% de afinidade"
   │
   ▼
Ordena os 20 cursos → mede a confiança → corta no top 5 → marca o empate → grava
```

> [!tip] O que diferencia de uma "caixa-preta"
> Para cada curso, a engine também guarda **quais áreas mais pesaram e quanto** (`explicacao`). É o bloco **"Por que este curso?"** da tela de resultado. O aluno e a coordenação veem **o número por trás da recomendação**.

---

## 🧩 2. As funções, na ordem em que rodam

| # | Função | Entra | Sai | Em uma frase |
|:-:|---|---|---|---|
| 1 | `perfil_vetor(alternativas)` | alternativas escolhidas | `{area: soma}` | Soma os pesos de todas as respostas, área por área |
| 2 | `vetor_curso(curso)` | um `Curso` | `{area: peso}` | Os `Peso_curso` do curso; sem peso cadastrado, usa `area_principal = 1.0` para nenhum curso sumir |
| 3 | `dot(a, b)` · `norm(v)` | dois vetores | número | Produto escalar e tamanho do vetor: as peças do cosseno |
| 4 | `afinidade(a, b)` | perfil e curso | 0 a 1 | O **cosseno**. Se algum vetor for zero, devolve `0.0` em vez de dividir por zero |
| 5 | `explicacao(perfil, curso, nomes)` | perfil e curso | top 3 áreas | Contribuição de cada área (`perfil[a] × curso[a]`) e o percentual de cada uma |
| 6 | `rank_cursos(perfil, cursos, nomes)` | perfil e cursos | lista ordenada | Calcula as afinidades e ordena da maior para a menor |
| 7 | `confianca(ranking)` | ranking **inteiro** | alta / média / baixa | Quanto o 1º se separou do 2º |
| 8 | `conjunto_de_empate(ranking)` | ranking **cortado** | ids | Os cursos a menos de 0,02 do 1º (o `tie_set`) |
| 9 | `banda(afinidade)` | uma afinidade | baixo / médio / alto | Nível de **um** curso: < 0,5 · < 0,8 · ≥ 0,8. Reservada para a camada de IA: um 1º lugar "baixo" não pode virar "combina muito com você". Ainda não é chamada |
| ★ | **`recomendar(tentativa)`** | uma `Tentativa` | grava tudo | A orquestradora: chama as outras e grava as recomendações |

> [!important] Funções 1 a 9 são **puras**
> Recebem números e devolvem números: não leem nem escrevem no banco. Por isso dá para testar o cálculo sozinho (`quiz/tests/test_engine_puro.py`) e simular milhares de perfis em menos de 1 ms cada. Só a `recomendar()` toca o banco.

---

## ✏️ 3. Uma conta feita à mão (coloque num slide)

Um aluno com 3 áreas e dois cursos. São números pequenos, de propósito, para a conta caber no quadro:

| | TI | Design | Mecânica |
|---|:-:|:-:|:-:|
| **Perfil do aluno** | 5 | 1 | 4 |
| **Curso A · Programação** | 5 | 2 | 0 |
| **Curso B · Usinagem** | 1 | 0 | 5 |

**Curso A, Programação**

```
perfil · curso   = 5×5 + 1×2 + 4×0           = 27
‖perfil‖         = √(5² + 1² + 4²) = √42     = 6,4807
‖curso‖          = √(5² + 2²)      = √29     = 5,3852

cos = 27 / (6,4807 × 5,3852) = 27 / 34,900   = 0,7736  →  77% de afinidade
```

**Curso B, Usinagem**

```
perfil · curso   = 5×1 + 1×0 + 4×5           = 25
‖curso‖          = √(1² + 5²)      = √26     = 5,0990

cos = 25 / (6,4807 × 5,0990) = 25 / 33,045   = 0,7565  →  76% de afinidade
```

**"Por que este curso?" do Curso A:** TI contribui 5×5 = 25 e Design contribui 1×2 = 2. De 27 no total, **TI = 92,6%** e **Design = 7,4%**.

> [!example] O exemplo já mostra o empate
> 0,7736 − 0,7565 = **0,0171**, menos que a régua de **0,02**. Para a engine, os dois cursos estão **empatados**: a confiança sai **baixa**, o `tie_set` tem os dois e a tela avisa o aluno. Esses números foram conferidos rodando as funções da engine: o sistema dá exatamente estes valores.

> [!tip] Por que o cosseno, e não uma soma simples
> O cosseno mede a **direção** do vetor (a *proporção* entre as áreas), não o **tamanho**. Um aluno que marcou pesos altos em tudo não "ganha" de um que marcou pesos baixos: dois alunos com as mesmas preferências relativas recebem a mesma recomendação. E, como nenhum peso é negativo, o resultado já sai entre 0 e 1, pronto para virar porcentagem (`round(score * 100)`).

---

## 🔬 4. Um caso real, do banco

Quiz respondido sempre com a **1ª alternativa**:

**Perfil:** Elétrica 18 · Metalurgia 14 · Eletromecânica 13 · Mecânica 9 · RH 5 · IA 4 · TI 4 · Automotiva 3 · Marketing 1

| `rank_engine` | Curso | Afinidade | Áreas que mais pesaram |
|:-:|---|:-:|---|
| **1** | Operação e Programação de Robô de Soldagem MAG | **0,8622** | Metalurgia 37,8% · Eletromecânica 21,1% · Elétrica 19,5% |
| **2** | Caldeireiro Montador | **0,8514** | Metalurgia 38,7% · Eletromecânica 21,5% · Elétrica 19,9% |
| 3 | Comandos Elétricos e CLP | 0,8170 | Elétrica 58,1% · Eletromecânica 33,5% · Mecânica 5,8% |
| 4 | Manutenção Eletromecânica Industrial | 0,8100 | Elétrica 40,0% · Eletromecânica 36,1% · Mecânica 20,0% |
| 5 | Eletricista Instalador | 0,8063 | Elétrica 65,2% · Eletromecânica 28,3% · Mecânica 6,5% |

- Diferença entre o 1º e o 2º: **0,0109**, menos que 0,02 → confiança **baixa**
- `tie_set = [19, 16]`: o Robô de Soldagem e o Caldeireiro estão empatados

> [!note] 🎓 Por que Elétrica é a área mais forte e mesmo assim o 1º lugar é de Metalurgia
> O cosseno compara o **formato** dos dois vetores. O Robô de Soldagem tem peso em Metalurgia **e** em Elétrica **e** em Eletromecânica, que são as três áreas mais fortes desse aluno. Os cursos "só de Elétrica" combinam numa área só. É uma ótima pergunta para antecipar na banca.

---

## ⚖️ 5. Confiança e empate: a régua de 0,02

```python
EMPATE = 0.02                 # diferença ABSOLUTA de afinidade
BANDA_CONFIANCA_ALTA = 0.08
CASAS = 6                     # arredonda antes de comparar: 0.80 - 0.75 = 0.05000000000000004
```

| Diferença entre o 1º e o 2º | Confiança | O que a tela faz |
|---|:-:|---|
| ≥ 0,08 | **alta** | Mostra o resultado normalmente |
| de 0,02 a 0,08 | **média** | Mostra o resultado normalmente |
| < 0,02 | **baixa** | Mostra o aviso *"Mais de um curso combinou com você quase na mesma medida…"* |

> [!important] Três lugares, um número só
> A mesma constante `EMPATE` decide: **(1)** a confiança "baixa", **(2)** quem entra no `tie_set` e **(3)** a regra 2 da camada de IA (a LLM só pode trocar o 1º lugar por um curso do `tie_set`). Se fossem três números, um dia eles iam discordar.

> [!note] 🎓 Detalhes que a banca pode cobrar
> - **A confiança é medida no ranking inteiro, antes do corte do top 5.** Senão ela mudaria conforme o limite configurado.
> - **O `tie_set` é medido depois do corte**, porque só os 5 cursos entregues podem ir para o 1º lugar.
> - **Arredondar antes de comparar** (`CASAS = 6`): em ponto flutuante, `0.80 − 0.75` dá `0.05000000000000004`. Sem arredondar, um empate exato poderia não ser reconhecido.
> - **A régua foi calibrada com dados.** O comando `medir_empate` mediu a distribuição das diferenças no quiz de 10 perguntas (commit `8b5b3bd`, "calibra a régua de empate").

---

## 📊 6. Métricas da engine (5.000 perfis simulados)

### O catálogo e o quiz

| Métrica | Valor |
|---|:-:|
| Áreas | **12** (todas medidas pelo quiz ✅) |
| Cursos ativos | **20** |
| Pesos de curso (`Peso_curso`) | **73** (de 2 a 6 áreas por curso) |
| Questões × alternativas | **10 × 4** = 40 alternativas, **80** pesos |
| Combinações de respostas possíveis | **4¹⁰ = 1.048.576** |

### Desempenho

| Métrica | Valor |
|---|:-:|
| Tempo de um ranking dos 20 cursos (em memória) | **≈ 0,9 ms** |
| Consultas ao banco em `recomendar()` | **12, sempre** (não cresce com o número de respostas: sem N+1) |
| Tempo de `recomendar()` com gravação | ≈ 66 ms (SQLite local) |

### Qualidade das recomendações

| Métrica | Valor | Como ler |
|---|:-:|---|
| Confiança **alta** / **média** / **baixa** | **18% / 48% / 34%** | Em 1 de cada 3 perfis sorteados há empate técnico, e o sistema **avisa** em vez de fingir certeza |
| `tie_set` com 1 curso / 2 / 3 ou mais | **66% / 27% / 7%** | Em 2 de cada 3 perfis, o 1º lugar não está em disputa |
| Afinidade do 1º lugar | média **0,754** (de 0,457 a 0,964) | Nível do 1º: **68% "médio"**, **32% "alto"**, 0% "baixo" |
| Afinidade do 5º lugar | média **0,599** | O 5º ainda é uma alternativa razoável |
| Cursos que já apareceram no top 5 | **20 de 20** | Nenhum curso fica "invisível" |
| Cursos que já ficaram em 1º | **18 de 20** | Os dois que nunca ficaram são as especializações de inspeção de solda |

### Quem mais fica em 1º lugar (5.000 perfis)

| Curso | % das vezes em 1º | % das vezes no top 5 |
|---|:-:|:-:|
| Automação Industrial | **25,7%** | 70,2% |
| Usinagem CNC | 17,9% | 59,3% |
| Python para Análise de Dados | 12,6% | 26,5% |
| Manutenção Eletromecânica Industrial | 9,1% | 55,2% |
| Injeção Eletrônica Automotiva | 7,8% | 39,0% |
| *… mais 13 cursos* | < 8% cada | |
| Inspeção de Qualidade em Soldagem · Inspetor de Líquido Penetrante | **0%** | 4,2% · 8,9% |

> [!warning] Leia isto como **diagnóstico dos pesos**, não como defeito
> Perfis sorteados não são alunos reais: na escola, as respostas não são aleatórias. Mesmo assim, a simulação mostra duas coisas que vale **dizer antes que a banca pergunte**:
> 1. **Automação Industrial aparece muito** (1 em cada 4 perfis), porque tem peso em muitas áreas ao mesmo tempo, e o cosseno favorece cursos "generalistas" quando o perfil é variado.
> 2. **As especializações de inspeção nunca ficam em 1º.** São cursos de nicho, para quem já é da área. Faz sentido como alternativa, não como principal.
>
> Os dois pontos se ajustam **no admin, mudando pesos**, sem mexer em código. A validação dos pesos com a coordenação é o próximo passo (ver §8).

---

## 💾 7. `recomendar(tentativa)`: a orquestradora

```python
@transaction.atomic
def recomendar(tentativa, limit=None):
    ...
    perfil  = perfil_vetor(...)                    # 1. perfil
    ranking = rank_cursos(perfil, cursos, nomes)   # 2. os 20 cursos ativos, ordenados
    tentativa.confidence_band = confianca(ranking) # 3. confiança ANTES do corte
    ranking = ranking[:limit]                      # 4. top 5
    tentativa.tie_set = conjunto_de_empate(ranking)# 5. empate DEPOIS do corte
    Recomendacao.objects.bulk_create([...])        # 6. grava rank_engine = rank_final
```

| Decisão técnica | Por quê |
|---|---|
| `@transaction.atomic` | Ou grava tudo (tentativa + 5 recomendações), ou nada |
| `select_related` + `prefetch_related` | Número fixo de consultas, não uma por resposta (sem **N+1**) |
| Apaga as recomendações antigas e faz `bulk_create` | Recalcular é **idempotente**: rodar duas vezes dá o mesmo resultado |
| `Curso.objects.filter(is_active=True)` | Curso desativado sai do cálculo **sem apagar o histórico** |
| `limit` vem de `settings.QUIZ_RECOMENDACAO_LIMIT` (5) | O tamanho do top N é configuração, não código |
| `rank_engine` **e** `rank_final` | Hoje são iguais. Com a camada de IA, `rank_final` pode mudar e `rank_engine` continua guardando o que a engine calculou (ver [[ia|🤖 Camada de IA]]) |

---

## 🧭 8. Limites (diga antes que perguntem)

| Limite | O que já existe para lidar com ele |
|---|---|
| Os pesos foram definidos pelo grupo, sem validação empírica | Editáveis no admin. A avaliação de fim de curso pergunta *"O curso combinou com o que o quiz mostrou?"* para medir isso com alunos de verdade |
| Cursos "generalistas" aparecem mais | A métrica de §6 mostra isso; ajustar os pesos resolve |
| É recomendação **baseada em conteúdo**, não em histórico de outros alunos | Não há dados históricos rotulados para treinar um modelo. O cosseno é explicável e auditável |
| O empate depende de uma régua fixa (0,02) | Calibrada com `medir_empate`. Pode ser recalibrada quando houver tentativas reais (o comando também mede as reais) |

> [!question] As 3 perguntas mais prováveis sobre a engine
> 1. **"Por que não usar IA para recomendar?"** Não há histórico rotulado para treinar. O cosseno é **determinístico** (mesma resposta, mesmo resultado), **explicável** e **auditável**. A IA entra para **explicar** a recomendação, e só pode mexer onde a engine diz que há empate (ver [[ia|🤖 Camada de IA]]).
> 2. **"De onde vêm os pesos?"** Do catálogo, definidos pelo grupo e gravados em seeds reproduzíveis. São editáveis pelo admin, sem código.
> 3. **"Como sabem que funciona?"** Testes automatizados do cálculo, uma conta à mão que confere com o sistema, 5.000 perfis simulados e, em produção, a pergunta 6 da avaliação de fim de curso.
