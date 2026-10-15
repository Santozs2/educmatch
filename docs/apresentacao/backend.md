---
title: "Apresentação · Backend (models, views, painel, avaliação, testes)"
aliases: ["Backend na apresentação", "O que apresentar do backend"]
tags: [tcc, apresentacao, backend, django, painel, avaliacao, testes]
status: pronto
projeto: TCC
atualizado: 2026-10-08
---

> [!info] Apresentação: [[README|🎤 Roteiro]] · [[engine|🧮 Engine]] · **⚙️ Backend** · [[frontend|🎨 Front]] · [[ia|🤖 Camada de IA]] · [[demo-e-perguntas|🎬 Demo e banca]]

# ⚙️ Backend: o que apresentar

> [!abstract] O que esta nota é
> O backend Django em **6 apps**, na ordem sugerida para a apresentação: **models → views → painel → avaliação → contas → deploy e testes**.
> A engine tem nota própria ([[engine|🧮 Engine]]) porque é o coração do trabalho: **gaste mais tempo nela do que aqui**.

> [!success] Conferido no código em 2026-10-08
> Base: `develop` em `06baffc`. Suíte: **203 testes** (atualizado em 2026-10-15, com a camada de IA). Sem nenhuma rota de API pública.

---

## 🗺️ 1. Os apps em um quadro

| App | Responsabilidade | Arquivos-chave |
|---|---|---|
| `core` | Settings (tudo do `.env`), rotas raiz, dados da escola | `settings.py`, `urls.py`, `contexto.py` |
| `catalogo` | Áreas, cursos e o peso de cada curso em cada área | `models.py`, `seed_areas`, `seed_cursos` |
| `quiz` | Questões, tentativas, **engine**, resultado | `engine.py` ★, `web_views.py`, `permissoes.py` |
| `accounts` | Login por e-mail, lista de interesse, adoção da tentativa | `models.py`, `servicos.py`, `signals.py` |
| `painel` | Métricas agregadas para a coordenação | `metricas.py`, `metricas_avaliacao.py`, `privacidade.py`, `views.py` |
| `avaliacao` | Avaliação de fim de curso, **anônima por desenho** | `models.py`, `views.py`, `seed_avaliacao` |

> [!quote] Frase para o slide
> **"Pesos em vez de regras":** para mudar o que o quiz mede, a coordenação edita números no admin, não o código.

---

## 🗃️ 2. Models: as decisões, não os campos

### Catálogo (`catalogo/models.py`)

| Model | Papel | O que destacar |
|---|---|---|
| `Area` | Uma área (Elétrica, TI, Metalurgia…) | `slug` **único**: é a chave estável que a engine usa nos vetores. O nome pode mudar; o slug não |
| `Curso` | Curso técnico ofertado | `is_active`: curso desativado sai do cálculo e do painel **sem apagar o histórico** |
| `Peso_curso` | Quanto um curso pertence a cada área (0 a 5) | Vira o **vetor do curso**. `unique_together (curso, area)` impede peso duplicado |

### Quiz (`quiz/models.py`)

| Model | Papel | O que destacar |
|---|---|---|
| `Questao` · `Alternativa` | Perguntas e opções (hoje 10 × 4) | `order` e `is_active`: reordenar ou tirar uma pergunta pelo admin |
| `Peso_alternativa` | Quanto cada opção soma em cada área (0 a 5) | Vira o **vetor do perfil**. São 80 pesos |
| `Tentativa_de_resposta` | Uma vez que alguém respondeu | `user` **opcional** (dá para responder sem conta). Guarda `confidence_band`, `diferenca`, `tie_set` e `iniciado_em`. Também tem os **metadados da LLM** (`llm_model`, `latency_ms`, `tokens_*`, `used_fallback`, `diverged`, `cache_hit`), prontos para a camada de IA |
| `Resposta` | Alternativa escolhida em cada questão | `unique_together (tentativa, questao)`: uma resposta por pergunta |
| `Recomendacao` | Os 5 cursos calculados | `score`, **`rank_engine`** (ordem da engine), **`rank_final`** (ordem entregue), `explicacao` (JSON) e `llm_text` |
| `QuestionarioLink` | Link que a coordenação distribui | `token` UUID (impossível de adivinhar) e `ativo` (fecha o link) |
| `InicioDeQuiz` | Um quiz **começado** | Não guarda usuário nem sessão: é só uma contagem, usada na **taxa de conclusão** |

> [!important] `rank_engine` × `rank_final`
> Hoje os dois são iguais. Separar as colunas agora é o que permite à camada de IA reordenar **sem perder** o que a engine calculou, e é isso que vai permitir medir a divergência ([[ia|🤖 Camada de IA]]).

### Contas (`accounts/models.py`)

| Model | Papel | O que destacar |
|---|---|---|
| `User` | Usuário customizado | `USERNAME_FIELD = "email"`: login por e-mail. Definido **antes da primeira migração**, que é o jeito certo no Django |
| `Interesse` | A "Minha lista" de cursos | **Snapshot** (`rank_snapshot`, `rank_engine_snapshot`, `afinidade_snapshot`, `era_principal`): a foto do momento em que o aluno salvou. `status` (interessado → contatado → descartado/removido) alimenta o **funil** do painel. `on_delete=PROTECT`: não se apaga um curso que alguém salvou |

### Avaliação (`avaliacao/models.py`)

| Model | Papel | O que destacar |
|---|---|---|
| `Pergunta` | 7 perguntas fixas (seed) | Tipos: `nps` (0 a 10), `escala` (1 a 5), `escolha`, `texto` |
| `LinkDeAvaliacao` | Um link por **curso + turma** | `token` UUID, `ativo` |
| `RespostaDeAvaliacao` | Uma resposta | Guarda **só o link e o dia** (`DateField`, não `DateTime`) |
| `ItemDeResposta` | A resposta de cada pergunta | `UniqueConstraint (resposta, pergunta)` |

> [!tip] Anônimo **por desenho**, não por promessa
> Nenhum model da avaliação **tem onde** guardar usuário, nome, e-mail, IP ou horário. Até a hora foi cortada: "respondeu às 10h14", junto com a turma, apontaria para uma pessoa. Dá para dizer à turma "é anônimo" sem precisar confiar em ninguém.

---

## 🛣️ 3. Views e rotas

Todas são **function-based views**, menos o login (`EntrarView`, herda de `LoginView`).

### Aluno

| Rota | View | O que destacar |
|---|---|---|
| `/` | `pagina_quiz` | **GET** mostra a intro e as perguntas e registra o **início** (`InicioDeQuiz`, uma vez por navegador). **POST** valida: faltou resposta → guarda na sessão e volta para a 1ª em branco (`#questao-N`), funcionando **sem JS**. Completo → cria `Tentativa` + `Resposta` (`bulk_create`) + chama a engine dentro de `transaction.atomic()` e redireciona (**Post/Redirect/Get**) |
| `/questionario/<uuid>/` | `acessar_questionario` | Link inválido ou fechado → página própria com **404**. Válido → token na sessão; a tentativa sai "via link" |
| `/resultado/<id>/` | `resultado_pagina` | **Contrato C6:** tentativa com dono, só o dono vê; anônima, só o navegador que respondeu. Fora disso, **404** (e não 403, para não revelar que o id existe). Mostra a ordem **`rank_final`** |
| `/cursos/<id>/` | `curso_detalhe` | Com `?tentativa=<id>`, mostra a afinidade daquele aluno usando `tentativa_visivel()`: **a mesma regra** do resultado, num lugar só (`quiz/permissoes.py`) |
| `/entrar/`, `/cadastro_usuario/` | `EntrarView`, `cadastrar_conta` | Login por e-mail e cadastro |
| `/interesse/salvar/` | `salvar_interesse` | Sem login → guarda como **interesse pendente** na sessão e manda para o login com `?next=`. Ao entrar, o interesse é gravado sozinho: **o aluno não perde o clique** |
| `/lista_interesse/`, `/meus-testes/`, `/meu-perfil/` | `@login_required` | Área do aluno |
| `/avaliacao/<uuid>/` | `responder` | Formulário da avaliação; a sessão impede responder duas vezes no mesmo navegador |

### Coordenação (`/painel/`, todas com `@staff_member_required`)

| Tela | Rota | Métricas (funções de `painel/metricas.py`) |
|---|---|---|
| **Início** | `/painel/` | total de testes, via link, conversão geral, testes por dia (gráfico), demanda por área, atividade recente, links ativos |
| **Quiz** | `/painel/quiz/` | top cursos em 1º e no top 5, cursos mais salvos, **distribuição de confiança**, **aderência** (em que posição estava o curso salvo), conversão por curso, **taxa de conclusão**, **tempo típico** (mediana), cursos nunca recomendados, cobertura das áreas |
| **Cursos** | `/painel/cursos/` | desempenho por curso (em 1º, no top 5), demanda por área |
| **Links** | `/painel/links/` | testes por link; gerar e fechar links |
| **Interesse** | `/painel/interesse/` | **funil** por status, interesse por curso (total, contatados, quantos eram o 1º) |
| **Avaliações** | `/painel/avaliacoes/…` | links por turma, **NPS**, distribuição das notas e das escolhas por pergunta, filtro por curso, **exportar CSV** |

Ações (`@require_POST` + staff): `gerar_link`, `fechar_link`, `fechar_um_link`, `gerar_link_avaliacao`, `fechar_link_avaliacao`. Depois de agir, a view volta só para uma tela de uma lista permitida (`VOLTAS_PERMITIDAS`), e nunca para um endereço vindo do usuário.

---

## 📈 4. Painel: como as métricas são feitas

> [!important] Funções puras, sem pessoa
> O `metricas.py` diz no topo: *nenhuma função recebe `request` nem usuário, e nenhuma lê `user` ou `respondido_por`*. O painel fala de **cursos e demanda**, nunca de pessoas. E, por serem puras, as métricas são **testáveis sem navegador** (`painel/tests/test_metricas.py`).

Técnicas para citar:

| Técnica | Onde | Por quê |
|---|---|---|
| `annotate(Count(..., filter=Q(...)))` | conversão, interesse por curso | Várias contagens numa consulta só |
| `TruncDate` / `TruncMonth` | `tentativas_por_dia` | Por dia até 62 dias; por mês em períodos maiores |
| **Mediana**, não média | `tempo_tipico` | Uma aba esquecida aberta por um dia puxaria a média para horas, mas não mexe na mediana |
| Taxa limitada a 100% | `taxa_de_conclusao` | Tentativas antigas não têm `iniciado_em` e inflariam a taxa |
| Períodos com o filtro na URL | `PERIODOS` (diário, mensal, anual, mês escolhido) | Trocar de tela **não reseta** o filtro (`periodo_qs`) |
| NPS | `metricas_avaliacao.nps` | % de notas 9-10 menos % de notas 0-6, de −100 a 100 |

### Privacidade: o mecanismo e a decisão do grupo

`painel/privacidade.py` tem o **k-anonimato** pronto:

1. `periodo_tem_massa_suficiente`: com menos de k testes no período, **só o total** sai do servidor.
2. `suprimir_pequenos` / `suprimir_campos`: uma contagem < k vira "—", e **a linha continua na tabela** (sumir com ela também vazaria: quem lê deduziria que o curso que falta tem menos de k).
3. **A taxa também some** quando o número dela some. Senão, `taxa × recomendados / 100` devolveria o número escondido. **Esse é um ótimo exemplo para a banca.**
4. Na avaliação, só os cursos com k respostas ou mais entram no "Todos os cursos" (`cursos_com_massa`). Senão, a diferença entre o NPS geral e o dos outros cursos revelaria a opinião de 3 pessoas.

> [!warning] Hoje `K_MINIMO = 0`: a supressão está **desligada**
> Decisão do grupo em 2026-10-01: o painel mostra todos os números. Ele é restrito à coordenação (`staff`) e **nunca mostra nome nem e-mail**, só contagens. O mecanismo continua inteiro e testado: **para religar, basta voltar `K_MINIMO` para 5.**
> Na banca, apresente assim: *"construímos o k-anonimato, testamos e deixamos como chave. Para o volume de uma escola, a coordenação preferiu ver todos os números."* **Não diga que o painel suprime números hoje.**

---

## 👤 5. Contas: adoção da tentativa e snapshot

**O problema:** o aluno responde **sem conta** e só cria a conta depois. Como a tentativa passa a ser dele?

- `accounts/signals.py` → `@receiver(user_logged_in)` → `adotar_tentativas_da_sessao`.
- Duas condições obrigatórias: o id está **na sessão deste navegador** (não adota a de outra pessoa) **e** a tentativa **ainda não tem dono** (não "rouba" uma já adotada).
- Um `update()` só, sem laço.

`accounts/servicos.py` → `registrar_interesse` usa `get_or_create`: é **idempotente**, e o snapshot **nunca** é sobrescrito. Guarda as duas posições (`rank_snapshot` = o que o aluno viu, `rank_engine_snapshot` = o que a engine calculou), o que já deixa pronta a medição da camada de IA.

---

## ☁️ 6. Configuração e deploy

| Item | Como está |
|---|---|
| Configuração | **Tudo do `.env`** (chave, `DEBUG`, hosts, banco, `LLM_*`). O `.env` nunca vai para o Git; os nomes estão no `.env.example` |
| Banco | MySQL, fuso `America/Sao_Paulo` (exige as tabelas de fuso do MySQL; o `core/tests.py` confere) |
| Cache | `DatabaseCache` (tabela `educmatch_cache`): sobrevive a reinício, pensado para a camada de IA |
| Deploy | **Azure App Service** (Linux): `startup.sh` roda `migrate`, `createcachetable`, os 4 seeds e `collectstatic`, e sobe o **gunicorn** com 2 workers |
| Arquivos estáticos | **WhiteNoise** com `CompressedManifestStaticFilesStorage` |
| HTTPS atrás do proxy | `SECURE_PROXY_SSL_HEADER` e `CSRF_TRUSTED_ORIGINS` vindos do `.env` |
| Seeds | `update_or_create`: rodar a cada boot **não duplica** nada |

---

## ✅ 7. Qualidade e testes: 203 testes

| App | Testes | O que prova |
|---|:-:|---|
| `quiz` | **111** | Cosseno sem banco (`test_engine_puro`), motor gravando, empate e régua (`test_empate`, `test_medir_empate`), `rank_final` (`test_rank_final`), contratos, telas, rotas, início do quiz, controle de acesso ao resultado e **a camada de IA** (49: provedor, prompt, validação, cache, fallback, tela e experimento) |
| `painel` | **59** | Métricas, supressão e taxas escondidas (`test_privacidade`), telas do painel, avaliações e o bloco "Camada de IA" |
| `accounts` | **19** | Snapshot do interesse (C4), rotas da conta (C5) e adoção da tentativa (C6) |
| `avaliacao` | **11** | A resposta **não tem onde** guardar quem respondeu, guarda o dia e não a hora, link fechado dá 404, o mesmo navegador não envia duas vezes |
| `core` | **3** | Tabelas de fuso do MySQL, cache no banco, variáveis da LLM |

> [!tip] Rode antes de apresentar e mostre o "OK" num print
> ```bash
> cd backend
> python manage.py test
> python manage.py makemigrations --check --dry-run   # "No changes detected"
> ```
> A CI do GitHub (`.github/workflows/test.yml`) roda a suíte num MySQL 8 a cada PR e a cada push na `main` e na `develop`. A LLM fica desligada, porque `LLM_ENABLED` é `0` por padrão.
