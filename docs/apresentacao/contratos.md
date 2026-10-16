---
title: "Os contratos do EducMatch (C1 a C6)"
aliases: ["Contratos", "C1 a C6", "Contratos do EducMatch", "Conformidade dos contratos"]
tags: [tcc, apresentacao, contratos, arquitetura, testes]
status: pronto
projeto: TCC
atualizado: 2026-10-16
---

> [!info] Apresentação: [[README|🎤 Roteiro]] · [[engine|🧮 Engine]] · [[backend|⚙️ Backend]] · [[frontend|🎨 Front]] · [[ia|🤖 Camada de IA]] · **📜 Contratos** · [[demo-e-perguntas|🎬 Demo e banca]]

# 📜 Os contratos do EducMatch (C1 a C6)

> [!abstract] O que esta nota é
> Os seis contratos do projeto **como estão no código da v0.3**: o que cada um congela, quem publica e quem consome, onde está implementado e qual teste prova isso. Também registra **onde o código se afastou da especificação original, e por quê**.
> A auditoria da v0.1 (11/09/2026, no cofre: `contratos-c1-a-c6`) mostrava C1 a C3 inexistentes e C4 a C6 parciais. Hoje os seis estão implementados e cobertos por teste.

---

## 🧭 1. O que "contrato" quer dizer aqui

Não é contrato jurídico. É o sentido da engenharia de software: **a descrição fixa do que um módulo entrega e do que o outro pode assumir**. Com isso, duas pessoas escrevem os dois lados sem precisar conversar a cada mudança.

No EducMatch, os contratos existem porque o trabalho foi dividido entre **4 pessoas, por fronteira de contrato**. Um sistema escrito por uma pessoa só teria as mesmas funções, mas não precisaria do documento que as congela.

> [!important] A regra que vale para todos
> **Um contrato que nenhum teste confere é só uma convenção.** Por isso cada contrato abaixo aponta para o teste que o prova. A saída de `python manage.py test quiz.tests.test_contratos -v 2` **é a tabela de conformidade**: ela é gerada pelo código, e não declarada num documento.

---

## 🗺️ 2. O mapa dos seis

```
 catálogo ──► engine ──C1──► camada de IA ──C2──► validação ──C3──► tela do aluno
                                                                      │
                               conta · lista de interesse · claim ◄───┘
                                         C4 · C5 · C6
```

| # | Contrato | Publica → Consome | Onde está | Teste que prova | Status |
|:-:|---|---|---|---|:-:|
| **C1** | Entrada da LLM (`build_payload`) | engine → camada de IA | `quiz/delivery.py` | `test_contratos` · `test_llm_base` | ✅ |
| **C2** | Saída da LLM e as 5 regras | LLM → validação | `quiz/serializers.py` | `test_contratos` · `test_llm_entrega_v1` | ✅ |
| **C3** | Entrega ao aluno | camada de IA → tela | `quiz/delivery.py` · `quiz/web_views.py` | `test_contratos` · `test_llm_gravacao` · `test_llm_tela` | ✅ (mudou de forma) |
| **C4** | Registro de interesse | lista → painel e métricas | `accounts/models.py` · `accounts/servicos.py` | `test_c4_interesse` · `test_contratos` | ✅ |
| **C5** | Rotas e autorização | conta → aluno | `accounts/urls.py` · `quiz/permissoes.py` | `test_c5_rotas` | ✅ (1 pendência) |
| **C6** | *Claim* da tentativa anônima | sessão → conta | `accounts/signals.py` | `test_c6_claim` · `test_contratos` | ✅ |

> [!tip] Para conferir na hora, diante da banca
> ```bash
> cd backend
> python manage.py test quiz.tests.test_contratos accounts.tests -v 2
> ```
> Cada linha `test_c1_...` a `test_c6_...` com `ok` é um contrato cumprido. **Nenhum teste fica em `skip`** desde a v0.3.

---

## 1️⃣ C1: a entrada da LLM (`build_payload`)

**A engine publica, a camada de IA consome.** É o JSON que vai dentro do prompt, no bloco `DADOS`. Os valores abaixo são ilustrativos; o formato é o real:

```json
{
  "perfil": {
    "areas_fortes": [
      {"area": "metalurgia", "area_name": "Metalurgia", "pontuacao": 7.0}
    ]
  },
  "candidatos": [
    {"course_id": 19, "nome": "Operação e Programação de Robô de Soldagem MAG",
     "descricao": "...", "score": 0.8622, "rank_engine": 1,
     "top_areas": [{"area_name": "Metalurgia", "percentual": 41.2}]}
  ],
  "tie_set": [19, 16]
}
```

**O que o contrato garante:**
- **Sem dado pessoal:** não leva nome, e-mail nem usuário. Há um teste específico para isso (`test_nao_leva_dado_pessoal`).
- Os **5 candidatos** vêm na ordem da engine (`rank_engine` de 1 a 5).
- O `tie_set` é um subconjunto dos candidatos. São os cursos que podem ocupar o 1º lugar.
- Até **3 áreas fortes**, só as que têm pontuação positiva.

> [!note] Onde o código se afastou da especificação original
> A spec F1+F2 previa mais dois blocos: `respostas[]` (o texto de cada pergunta com a alternativa escolhida) e `confianca` (o score do 1º, a diferença para o 2º e a banda). Na implementação:
> - o `confianca.conjunto_empate` virou o **`tie_set` no nível de cima**;
> - a banda de confiança ficou na `Tentativa` (`confidence_band`), fora do payload;
> - o **`respostas[]` não foi implementado**.
>
> A própria spec avisava a consequência: sem as respostas em texto, a LLM recebe **os mesmos números que a engine usou** e não tem com o que desempatar. Isso ajuda a explicar a **divergência de 0%** no experimento ([[ia|🤖 Camada de IA, §6]]). Um `respostas[]` num prompt v2 é o primeiro candidato a trabalho futuro.

---

## 2️⃣ C2: a saída da LLM e as 5 regras

**A LLM produz, o servidor valida.** O formato é 1 `principal` + 4 `alternativas`:

```json
{
  "principal":    {"course_id": 19, "texto": "3 a 5 frases"},
  "alternativas": [{"course_id": 16, "texto": "1 a 2 frases"}, "... mais 3"]
}
```

| # | Regra | Como o código confere |
|:-:|---|---|
| 1 | Todo `course_id` veio da lista de candidatos | `set(ids) - set(candidatos)` vazio |
| 2 | Nenhum curso repetido | `len(ids) == len(set(ids))` |
| 3 | Nenhum candidato descartado | `set(candidatos) - set(ids)` vazio |
| 4 | Texto não vazio e dentro do limite | `CharField(max_length=600)` no principal e `220` nas alternativas |
| 5 | **O principal está no `tie_set`** | `ids[0] in tie_set` |

**Se qualquer regra quebrar:** a resposta vira `LLMInvalidOutput`, o aluno recebe a ordem da engine (fallback) e **a saída recusada não entra no cache**. Antes de validar, o leitor tolera texto e cercas de código em volta do JSON: ele pega do primeiro `{` ao último `}`.

> [!success] Por que a regra 5 é a mais importante
> No prompt, "não troque o 1º lugar fora do empate" é **uma instrução em linguagem natural**, e o servidor não tem como saber se o modelo obedeceu. Com o `tie_set` calculado pela engine e enviado no payload, o servidor **sabe de antemão quem podia ir para o 1º lugar**. A instrução vira um predicado booleano, conferido em tempo de execução, com consequência definida (o fallback).

---

## 3️⃣ C3: a entrega ao aluno

**A camada de IA publica, a tela consome.** Este é o contrato que mais mudou de forma.

| | Spec original (F2-09) | Implementado (Passo 9) |
|---|---|---|
| Forma | Endpoint `GET /api/quiz/attempts/<pk>/entrega/` | Etapa dentro do **POST do quiz** |
| Carregamento | Duas etapas, com o campo `pronto` | **Uma etapa**, com timeout de 8 s |
| Por quê | Desacoplar a tela da chamada à LLM | A tela "Analisando" já cobre a espera, e o cache serve as repetições na hora. Duas etapas exigiriam JavaScript buscando o texto depois, para um ganho pequeno |

**O fluxo:**
1. Dentro de `transaction.atomic()`, a engine grava os 5 cursos. **O resultado já existe aqui.**
2. **Fora da transação**, o `entregar(tentativa)` chama a LLM, valida (C2) e grava.
3. O aluno é redirecionado para `/resultado/<id>/`.

**O que fica gravado:**

| Onde | Campos |
|---|---|
| `Recomendacao` | `rank_engine` (a ordem da engine), `rank_final` (a ordem entregue) e `llm_text` |
| `Tentativa_de_resposta` | `llm_model`, `prompt_version`, `latency_ms`, `tokens_in`, `tokens_out`, `used_fallback`, `diverged`, `cache_hit` |

**O que o aluno vê:** os cursos na ordem do `rank_final`, com o texto da LLM e o selo *"Texto escrito com IA"*. No fallback, ou com `LLM_ENABLED=0`, a tela mostra a descrição do curso, igual à v0.2.

> [!important] O contrato do lado do aluno: nunca quebrar
> Timeout, provedor fora do ar, saída inválida, bug nosso e até um erro do banco na hora de gravar a entrega: tudo vira fallback, e **nunca erro 500**. Depois de um timeout ou de um 429/503, a camada **para de chamar a LLM por `LLM_PAUSA` segundos** (30 por padrão), e os próximos alunos vão direto para a engine (EDU-202).

---

## 4️⃣ C4: o registro de interesse

**A lista de interesse publica; o painel e as métricas consomem.** É a "foto" do momento em que o aluno salvou um curso.

| Campo | Para quê |
|---|---|
| `usuario`, `curso` | Quem salvou o quê. **Único por par**: salvar de novo não duplica |
| `tentativa_origem` | De qual resultado veio o interesse |
| `rank_snapshot` | A posição **entregue** (`rank_final`) no momento em que foi salvo |
| `rank_engine_snapshot` | A posição **da engine** no mesmo momento |
| `afinidade_snapshot` | O score de afinidade |
| `era_principal` | Era o 1º colocado entregue? |
| `status` | `interessado` · `contatado` · `descartado` · `removido` |
| `criado_em` | `auto_now_add`: a data do primeiro salvamento **não muda depois** |

**As garantias estruturais:**
- `on_delete=PROTECT` no curso: apagar um curso não apaga em silêncio a prova de que alguém o queria.
- `on_delete=SET_NULL` na tentativa: o interesse sobrevive se a tentativa for apagada.
- **Remover é *soft delete*:** o `status` vira `removido`, e a linha e a foto ficam.

**Um único lugar grava interesse:** `accounts/servicos.py → registrar_interesse()`.
- Ele é idempotente: chamar de novo não muda nada.
- **A foto nunca é reescrita.** Se o aluno remove o curso e salva de novo, o mesmo registro volta para `interessado` com a foto original.
- Ele só aceita a foto de uma tentativa que a pessoa pode ver (`tentativa_visivel`). Uma tentativa de outra pessoa não empresta a foto.

> [!example] As perguntas que o C4 responde com uma consulta
> - **Aderência:** o aluno salvou o 1º colocado ou desceu até o 3º? (`rank_snapshot`)
> - **O aluno seguiu a IA ou a engine?** Quando a LLM trocou o 1º lugar, ele salvou qual dos dois? (`rank_snapshot` × `rank_engine_snapshot`)
> - **Conversão ao longo do tempo:** confiável porque o `criado_em` não muda mais. Na v0.1 era `auto_now`, e a data mudava a cada `save()`.

---

## 5️⃣ C5: rotas e autorização

**A conta publica, o aluno consome.**

| Método | Rota | Nome | Quem pode |
|---|---|---|---|
| `GET` `POST` | `/entrar/` | `entrar` | Todos |
| `GET` `POST` | `/cadastro_usuario/` | `cadastro_usuario` | Todos |
| `POST` | `/logout/` | `logout` | Logado |
| `GET` | `/lista_interesse/` | `lista_interesse` | **Só o dono** |
| `POST` | `/interesse/salvar/` | `interesse-salvar` | Todos (anônimo vira pendente, ver C6) |
| `POST` | `/interesse/remover/` | `interesse-remover` | Só o dono |
| `POST` | `/lista_interesse/<pk>/remover/` | `remover_interesse` | Só o dono |
| `GET` | `/meus-testes/` | `minhas-tentativas` | **Só o dono** |
| `GET` | `/meu-perfil/` | `aluno-perfil` | **Só o dono** |
| `GET` | `/resultado/<pk>/` | `quiz-resultado` | Dono, ou o navegador que respondeu (C6) |

**As três regras:**
1. **`login_required` não é autorização.** Quem protege os dados é o queryset filtrado pelo dono, como em `get_object_or_404(Interesse, pk=pk, usuario=request.user)`, e não uma busca por `pk` seguida de comparação.
2. **404, e não 403**, para o recurso de outra pessoa. Um 403 confirmaria que o recurso existe.
3. **Toda rota que escreve aceita só POST.** Um link que faz GET recebe 405 e não executa a ação.

> [!bug] Pendência: uma rota quebrada desde a v0.1
> `lista_interesse/<int:pk>/salvar/` (nome `salvar_interesse`) aponta para `salvar_interesse(request)`, que **não recebe `pk`**. Qualquer POST nessa rota termina em erro 500. Nenhuma tela usa a rota, que já tinha sido apontada na auditoria de setembro. A correção é **apagar a linha** do `accounts/urls.py`, porque o salvar de verdade é o `/interesse/salvar/`.

> [!note] Os nomes ficaram como estão
> A spec propunha `/criar-conta/`, `/sair/` e `/minha-lista/`. O código usa `/cadastro_usuario/`, `/logout/` e `/lista_interesse/`. A **regra de autorização** foi seguida à risca e os **nomes** derivaram. Esta nota documenta os nomes reais, para que o contrato e o código voltem a falar a mesma língua.

---

## 6️⃣ C6: o *claim* da tentativa anônima

**A sessão publica, a conta consome.** É o que faz o quiz respondido sem login aparecer em `/meus-testes/` depois que a pessoa cria a conta.

```
1. o visitante responde o quiz
   └── o id da tentativa vai para session["minhas_tentativas"]

2. clica em "salvar na minha lista" sem estar logado
   └── session["interesse_pendente"] = {curso_id, tentativa_id}
   └── vai para /entrar/?next=/resultado/<id>/

3. entra ou cria a conta  ◄── O CLAIM
   └── signal user_logged_in → adotar_tentativas_da_sessao()
   └── as tentativas da sessão sem dono ganham este usuário
   └── o interesse pendente é salvo (registrar_interesse, C4)

4. volta para /resultado/<id>/, já com o curso na lista
```

**As duas condições do claim, ambas obrigatórias:**
1. O id está na sessão **deste navegador**. Sem isso, qualquer pessoa logada adotaria uma tentativa alheia mandando ids à mão.
2. A tentativa **ainda não tem dono**. Sem isso, uma tentativa já adotada poderia ser adotada de novo.

A mesma regra decide quem pode ver um resultado (`quiz/permissoes.py → tentativa_visivel`): uma tentativa com dono, só o dono vê; uma tentativa anônima, só o navegador que a respondeu.

> [!warning] O detalhe que quebrou o C6 na v0.1
> O receiver só existe se o módulo `signals` for importado. Isso acontece em `AccountsConfig.ready()`. Na v0.1 não havia `ready()`, então o signal nunca se registrava, sem nenhum erro. Hoje o teste `test_c6_o_claim_esta_conectado` **quebra se alguém tirar esse import**.

---

## 📈 7. Da v0.1 à v0.3

| # | v0.1 (auditoria de 11/09) | v0.3 (hoje) |
|:-:|---|---|
| C1 | ❌ não existia | ✅ `build_payload`, sem `respostas[]` |
| C2 | ❌ não existia | ✅ as 5 regras no `DeliverySerializer` |
| C3 | ❌ não existia; as rotas REST davam erro 500 | ✅ entrega no POST do quiz, com fallback e pausa; a API REST foi removida |
| C4 | 🟡 sem os campos de snapshot; `criado_em` com `auto_now` | ✅ snapshot completo, gravação num lugar só, soft delete |
| C5 | 🟡 nomes de rota divergentes; uma rota quebrada | ✅ autorização testada · 🟡 a rota quebrada continua |
| C6 | 🟡 o signal não fazia nada e nunca rodava | ✅ claim com as duas condições, registrado no `ready()` |

---

## 🧩 8. Pendências e trabalho futuro

| Item | Contrato | Tamanho |
|---|:-:|---|
| Apagar a rota `lista_interesse/<pk>/salvar/` | C5 | 1 linha + 1 teste |
| `respostas[]` no payload, para a LLM ter com o que desempatar | C1 | Prompt v2 + experimento comparando com a v1 |
| Banda de confiança no payload | C1 | Pequeno, junto com o item acima |

## 📎 Veja também

- [[ia|🤖 Camada de IA]]: as travas, o experimento e a decisão A
- [[backend|⚙️ Backend]]: os models e as views
- `docs/specs/spec-ia-passo-08-prompt-e-validacao.md` (C2) · `docs/specs/spec-ia-passo-09-provedor-real.md` (C3)
- `backend/quiz/tests/test_contratos.py`: a tabela de conformidade em forma de teste
