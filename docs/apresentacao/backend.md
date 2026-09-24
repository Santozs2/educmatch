# Backend: o que apresentar

Ordem sugerida: **models → engine → views → painel/privacidade → contas → testes**. A engine é o coração da apresentação: gaste mais tempo nela.

---

## 1. Models (o DER em palavras)

Mostre o DER e explique **três grupos**. Não descreva campo por campo; destaque as decisões.

### Catálogo (`catalogo/models.py`)

| Model | Papel | O que destacar |
| --- | --- | --- |
| `Area` | Uma área de interesse (ex.: TI, Mecânica) | `slug` **único**: é a chave estável que a engine usa para montar os vetores. O nome pode mudar, o slug não. |
| `Curso` | Curso técnico ofertado | `is_active`: curso desativado sai do cálculo e do painel sem apagar o histórico. |
| `Peso_curso` | Quanto um curso pertence a cada área (0 a 5) | Vira o **vetor do curso**. `unique_together (curso, area)` impede peso duplicado. |

### Quiz (`quiz/models.py`)

| Model | Papel | O que destacar |
| --- | --- | --- |
| `Questao` / `Alternativa` | Perguntas e opções | `order` e `is_active`: dá para reordenar ou tirar uma pergunta pelo admin, sem mexer no código. |
| `Peso_alternativa` | Quanto cada opção soma em cada área (0 a 5) | Vira o **vetor do perfil** do aluno. |
| `Tentativa_de_resposta` | Uma vez que alguém respondeu o quiz | `user` é **opcional** (pode responder sem conta). Guarda `confidence_band`, `diferenca` e `tie_set`. Tem índice em `criado_em` porque o painel filtra por período. |
| `Resposta` | Alternativa escolhida em cada questão | `unique_together (tentativa, questao)`: uma resposta por pergunta. |
| `Recomendacao` | Resultado calculado | `score`, `rank` e `explicacao` (JSON com as áreas que mais pesaram). Tem índice em `(rank, curso)` para as métricas do painel. |
| `QuestionarioLink` | Link que a coordenação distribui | `token` UUID (impossível de adivinhar) e `ativo` (dá para fechar o link). |

### Contas (`accounts/models.py`)

| Model | Papel | O que destacar |
| --- | --- | --- |
| `User` | Usuário customizado | `USERNAME_FIELD = "email"`: login por e-mail. `AUTH_USER_MODEL` foi definido **antes da primeira migração**, que é o jeito certo no Django. |
| `Interesse` | "Minha lista" de cursos | **Snapshot** (`rank_snapshot`, `afinidade_snapshot`, `era_principal`): a foto do momento em que o aluno salvou. Se ele refizer o teste, o histórico não muda. `on_delete=PROTECT` no curso: não se apaga um curso que alguém salvou. |

**Frase para o slide:** "Pesos em vez de regras: para mudar o que o quiz mede, a coordenação edita números no admin, não o código."

---

## 2. Engine de recomendação (`quiz/engine.py`) ★

Esta é a parte que a banca mais vai querer entender. Explique em **4 passos**, cada um com o nome da função.

### Passo 1: vetor do perfil (`perfil_vetor`)

Soma os pesos de todas as alternativas escolhidas, **área por área**.

```
Respostas: A (ti: 3, design: 1)  +  B (ti: 2, mecanica: 4)
Perfil  = { ti: 5, design: 1, mecanica: 4 }
```

### Passo 2: vetor do curso (`vetor_curso`)

Vem dos `Peso_curso`. Se o curso não tiver peso cadastrado, usa `area_principal = 1.0` como reserva, para nenhum curso ficar de fora.

### Passo 3: afinidade = cosseno (`afinidade`, `dot`, `norm`)

```
            perfil · curso
cos(θ) = ─────────────────────
          ‖perfil‖ × ‖curso‖
```

Por que **cosseno** e não distância ou soma simples?

- Mede **direção** (o formato do perfil), não **tamanho**. Quem marcou pesos altos em tudo não "ganha" de quem marcou pesos baixos: o que conta é a **proporção** entre as áreas.
- O resultado já sai entre 0 e 1 (pesos não são negativos), o que vira direto a porcentagem de afinidade (`round(score * 100)`).
- Divisão por zero tratada: `if not denominador: return 0.0`.

### Passo 4: explicação e confiança

- **`explicacao`**: para cada curso, calcula a contribuição de cada área (`perfil[area] × curso[area]`), pega as **3 maiores** e o percentual de cada uma. É o bloco "Por que este curso?" da tela de resultado. **Isso é o que diferencia de uma caixa-preta.**
- **`confianca`**: quanto o 1º colocado se separou do 2º, relativo ao 1º: `(primeiro − segundo) / primeiro`.
  - ≥ 15% → `alta` · ≥ 5% → `media` · abaixo → `baixa` (a tela avisa o aluno para refazer ou falar com a secretaria).
  - É medida **no ranking inteiro, antes do corte** do top 5. Senão a confiança mudaria conforme o limite configurado.

### A função que orquestra: `recomedacao(tentativa)`

Pontos técnicos para citar:

- `@transaction.atomic`: ou grava tudo (tentativa atualizada + recomendações), ou nada.
- `select_related("alternativa")` + `prefetch_related("alternativa__pesos__area")`: evita o problema **N+1** (poucas consultas fixas, não uma por resposta).
- Recalcular é **idempotente**: apaga as recomendações antigas da tentativa e faz `bulk_create` das novas.
- O limite (5) vem de `settings.QUIZ_RECOMENDACAO_LIMIT`, não está fixo no código.

> Dica: tenha uma **conta feita à mão** num slide (2 áreas, 1 aluno, 2 cursos) e mostre que o sistema dá o mesmo número. Isso convence mais que qualquer explicação.

---

## 3. Views principais

Todas são **function-based views**, exceto o login (`EntrarView`, que herda de `LoginView`).

### `quiz/web_views.py`

| View | Rota | O que destacar |
| --- | --- | --- |
| `pagina_quiz` | `/` | **GET** mostra a introdução e as perguntas. **POST** valida se todas foram respondidas. Se faltar alguma, guarda as respostas **na sessão** e redireciona para a primeira em branco (`#questao-N`); o quiz funciona sem JS. Completo, cria `Tentativa` + `Resposta` (`bulk_create`) + chama a engine dentro de `transaction.atomic()` e redireciona (padrão **Post/Redirect/Get**, que evita reenviar ao atualizar a página). |
| `acessar_questionario` | `/questionario/<uuid:token>/` | Link inválido ou fechado → página própria com **404**. Válido → grava o token na sessão; a tentativa sai marcada como "via link". |
| `resultado_pagina` | `/resultado/<id>/` | **Controle de acesso (contrato C6):** tentativa com dono só o dono vê; tentativa anônima só no navegador que respondeu (id na sessão). Caso contrário, **404** (e não 403, para não revelar que o id existe). |

### `catalogo/views.py`, `curso_detalhe`

`get_object_or_404(..., is_active=True)`. Se vier `?tentativa=<id>`, usa `tentativa_visivel()` (`quiz/permissoes.py`) com a **mesma regra** do resultado para mostrar a afinidade daquele aluno com o curso. A regra fica num lugar só.

### `accounts/views.py`

- `EntrarView`, `cadastrar_conta`: login por e-mail e cadastro.
- `salvar_interesse` (`@require_POST`): funciona como **alternar** (salva; se já estava salvo, remove). Se a pessoa não está logada, guarda o curso como **interesse pendente** na sessão e manda para o login com `?next=` apontando de volta ao resultado. Ao entrar (`EntrarView.get_success_url`) ou criar conta, `_salvar_interesse_pendente` grava o interesse sozinho. O aluno não perde o clique.
- `lista_interesse`, `minhas_tentativas`, `aluno_perfil`: `@login_required`.

### `painel/views.py`

- `dashboard` (`@staff_member_required`): escolhe o período (30/90/365 dias/tudo), calcula o total e **só busca as outras métricas se houver massa suficiente**.
- `gerar_link` / `fechar_link` (`@require_POST` + staff): criam e desativam `QuestionarioLink`.

---

## 4. Painel e privacidade (`painel/metricas.py` + `painel/privacidade.py`)

Separação de responsabilidades que vale mostrar:

- **`metricas.py`** só faz consultas agregadas (`annotate`, `Count` com `filter=`, `values`): top cursos em 1º lugar, top 5, conversão recomendado→interesse, aderência (em que posição estava o curso que o aluno salvou), demanda por área, distribuição de confiança, cursos nunca recomendados, cobertura das áreas pelo quiz.
- **`privacidade.py`** aplica o **k-anonimato** com `K_MINIMO = 5`:
  1. `periodo_tem_massa_suficiente`: com menos de 5 tentativas no período, **só o total** sai do servidor.
  2. `suprimir_pequenos`: qualquer contagem < 5 vira `None` e aparece como "—".
  3. Detalhe fino: quando o número de interessados é suprimido, a **taxa** também é zerada. Senão `taxa × recomendados / 100` revelaria o número escondido. **Esse é um ótimo exemplo para a banca.**

Por que isso importa: são dados de estudantes, muitos menores de idade (LGPD). Para ver um caso individual, a coordenação usa o `/admin`, que exige permissão.

---

## 5. Contas: o signal de "adoção" (`accounts/signals.py`)

Problema: o aluno responde **sem conta** e só cria conta depois. Como a tentativa vira dele?

- `@receiver(user_logged_in)` → `adotar_tentativas_da_sessao`.
- Duas condições obrigatórias: o id está **na sessão deste navegador** (não adota a tentativa de outra pessoa) **e** a tentativa ainda **não tem dono** (não "rouba" uma já adotada).
- Um `update()` só, sem laço.

E o `registrar_interesse` (`accounts/servicos.py`) centraliza a gravação do interesse com `get_or_create`: é **idempotente** e o snapshot nunca é sobrescrito.

---

## 6. Qualidade e testes

- **64 testes** (`python manage.py test` em `backend/`). Rode antes e mostre o "OK" num print.

| Arquivo | O que prova |
| --- | --- |
| `quiz/tests/test_engine_puro.py` | Cosseno, vetores e explicação sem banco |
| `quiz/tests/test_motor.py`, `test_recomendacao.py` | Engine gravando recomendações |
| `quiz/tests/test_contratos.py` | Contratos entre as partes do sistema |
| `quiz/tests/test_rotas_web.py`, `test_paginas.py`, `test_telas.py`, `test_resultado.py` | Rotas, telas e controle de acesso ao resultado |
| `accounts/tests/test_c4_interesse.py`, `test_c5_rotas.py`, `test_c6_claim.py` | Snapshot do interesse, rotas da conta e a "adoção" da tentativa |
| `painel/tests/test_metricas.py`, `test_privacidade.py` | Métricas e supressão k = 5 |
| `core/tests.py` | Tabelas de fuso do MySQL (sem elas o filtro por data volta vazio) |

- Configuração por **variáveis de ambiente** (`.env`, fora do Git): chave, `DEBUG`, hosts e banco.
- Seeds reproduzíveis: `seed_areas`, `seed_cursos`, `seed_questoes` (12 áreas, 20 cursos, 73 pesos).
