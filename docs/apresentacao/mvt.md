---
title: "Arquitetura MVT do EducMatch (Model · View · Template)"
aliases: ["MVT", "MVT do EducMatch", "Model View Template", "Arquitetura MVT"]
tags: [tcc, arquitetura, mvt, django, models, views, templates]
status: pronto
projeto: TCC
atualizado: 2026-10-27
---

> [!info] Relacionado: [[apresentacao/README|🎤 Roteiro]] · [[apresentacao/backend|⚙️ Backend]] · [[apresentacao/frontend|🎨 Front]] · [[apresentacao/engine|🧮 Engine]]

# 🏛️ O MVT do EducMatch

> [!abstract] O que esta nota é
> Como o **Model–View–Template** do Django está aplicado neste projeto: o que cada
> camada faz, **onde cada arquivo mora** e como uma requisição atravessa as três.
> A [[apresentacao/backend|nota de backend]] descreve as decisões de modelagem e a
> [[apresentacao/frontend|do front]] descreve CSS e JavaScript. Esta aqui é a **cola
> entre elas**: o caminho que o dado faz.

---

## 🧭 1. MVT em uma frase

O Django chama de MVT o que outros frameworks chamam de MVC, com os nomes trocados:

| Camada | No Django | No EducMatch |
|---|---|---|
| **Model** | Classes que viram tabelas, em `models.py` | 6 apps, cada um com os seus models |
| **View** | Função que recebe `HttpRequest` e devolve `HttpResponse` | `web_views.py`, `views.py` — **funções**, não classes (exceto `EntrarView`) |
| **Template** | HTML com tags do Django, em `templates/` | `backend/templates/` mais um `templates/` por app |

> [!important] O "controlador" não é a View
> Quem decide **qual** view atende a URL é o `urls.py` (o `URLconf`). A View é o que
> o MVC chamaria de controlador; o "V" de MVC (a apresentação) é o **Template**.
> É só isso que a troca de sigla significa.

```
Navegador
   │  GET /resultado/12/
   ▼
core/urls.py ──► quiz/web_urls.py ──► resultado_pagina(request, pk=12)   ← VIEW
                                            │
                                            │ consulta
                                            ▼
                                   quiz/models.py                        ← MODEL
                                   Tentativa_de_resposta, Recomendacao
                                            │
                                            │ devolve objetos Python
                                            ▼
                                   render(request, "quiz/resultado.html", contexto)
                                            │
                                            ▼
                                   templates/quiz/resultado.html          ← TEMPLATE
                                   extends base.html
                                            │
                                            ▼
                                        HTML pronto
```

---

## 🗃️ 2. Model — onde o dado mora

Cada app tem o seu `models.py`. Nenhuma view escreve SQL: tudo passa pelo ORM.

| App | Models | Papel na camada |
|---|---|---|
| `catalogo` | `Area`, `Curso`, `Peso_curso` | O catálogo e os **vetores dos cursos** |
| `quiz` | `Questao`, `Alternativa`, `Peso_alternativa`, `Tentativa_de_resposta`, `Resposta`, `Recomendacao`, `QuestionarioLink`, `InicioDeQuiz` | O questionário e o resultado |
| `accounts` | `User` (login por e-mail), `Interesse` | Conta e lista de interesse |
| `avaliacao` | `Pergunta`, `LinkDeAvaliacao`, `RespostaDeAvaliacao`, `ItemDeResposta` | Avaliação de fim de curso |
| `painel` | — | **Não tem model próprio**: só lê os outros |

### Três coisas que este projeto põe no Model, e não na View

**1. A ordem de exibição.** `Recomendacao.Meta.ordering = ["rank_final"]`
([`quiz/models.py`](../backend/quiz/models.py)). A view não ordena nada: ela confia
no model. Por isso `resultado_pagina` pode fazer `itens[0]` e saber que é o 1º lugar.

```python
class Meta:
    unique_together = ('tentativa', 'curso')
    # A tela mostra a ordem que o aluno viu, não a que a engine calculou.
    ordering = ["rank_final"]
```

> [!tip] Por que isso é bom na banca
> `rank_engine` guarda a ordem da engine e `rank_final` a ordem entregue. O model
> ordena pela **entregue**, e a comparação entre as duas é o que mede a divergência
> da LLM. Duas colunas em vez de uma, e nada se perde.

**2. As regras de integridade.** São `constraints` do banco, não `if` na view:

- `unique_together (tentativa, questao)` em `Resposta` — uma resposta por pergunta.
- `unique_together (tentativa, curso)` em `Recomendacao`.
- `UniqueConstraint(["resposta", "pergunta"])` em `ItemDeResposta`.
- `Area.slug` único — é a chave estável que a engine usa nos vetores.

**3. O que é "derivado" e fica gravado.** `Tentativa_de_resposta` guarda `diferenca`,
`confidence_band` e `tie_set`, calculados uma vez pela engine. A tela **não recalcula**:
o resultado de ontem continua mostrando o que o aluno viu ontem, mesmo que os pesos
tenham mudado desde então.

> [!warning] O que NÃO está no Model
> A **similaridade de cosseno** não é um método de model. Está em
> [`quiz/engine.py`](../backend/quiz/engine.py) como **funções puras** que recebem
> dicionários e devolvem números, sem tocar no banco. É o que permite simular milhares
> de perfis sem gravar nada. Ver [[apresentacao/engine|🧮 Engine]].

---

## ⚙️ 3. View — onde a decisão acontece

As views são **funções**. A única baseada em classe é `EntrarView`, que aproveita a
`LoginView` do Django.

### Os quatro padrões de view do projeto

**① View de leitura** — consulta, monta contexto, renderiza.
Exemplo: `resultado_pagina` em [`quiz/web_views.py`](../backend/quiz/web_views.py).

```python
recomendacoes = tentativa.recomendacoes.select_related("curso__area_principal")
itens = [
    {
        "rank": rec.rank_final,
        "match": round(rec.score * 100),
        "curso": rec.curso,
        "areas": areas_da_recomendacao(rec),
        "texto": rec.llm_text,  # vazio sem LLM ou no fallback: a tela mostra a descrição
    }
    for rec in recomendacoes
]
return render(request, "quiz/resultado.html", {...})
```

Duas coisas para notar: o `select_related` evita o N+1 (uma consulta, não uma por
curso), e a view **já converte** `score` em percentual. O template não calcula.

**② View de formulário** — o mesmo endereço atende `GET` e `POST`.
Exemplo: `responder` em [`avaliacao/views.py`](../backend/avaliacao/views.py).

```python
form = FormularioDeAvaliacao(perguntas, request.POST or None)
if request.method == "POST" and form.is_valid():
    ...  # grava e redireciona
return render(request, "avaliacao/responder.html", {"link": link, "form": form})
```

O `request.POST or None` é o idioma do Django para "formulário vazio no GET,
preenchido no POST". Quando a validação falha, cai no mesmo `render` do fim — e o
template reexibe os valores e os erros, porque o `form` já os carrega.

**③ View que grava** — tudo dentro de `transaction.atomic()`.
Exemplo: `pagina_quiz` no POST final.

```python
with transaction.atomic():
    tentativa = Tentativa_de_resposta.objects.create(...)
    Resposta.objects.bulk_create([...])
    recomendar(tentativa)
# Fora da transação: a chamada de rede (até LLM_TIMEOUT) não segura o banco,
# e o resultado da engine já está gravado se a LLM falhar.
entregar(tentativa)
```

> [!important] A linha mais importante do fluxo
> `recomendar()` está **dentro** da transação e `entregar()` **fora**. A engine e as
> respostas gravam juntas ou não gravam; a LLM é um enfeite que pode falhar depois,
> sem desfazer nada e sem manter uma transação aberta esperando a rede.

**④ View de ação** — não renderiza nada, só executa e redireciona.
Exemplo: `gerar_link` em [`painel/views.py`](../backend/painel/views.py), com
`@require_POST` e `messages.success()`. O padrão é **POST → redirect**, para que
recarregar a página não repita a ação.

### PRG: Post/Redirect/Get

Nenhuma view do projeto responde a um `POST` com HTML. Ou redireciona, ou (quando a
validação falha) re-renderiza o formulário. É o que faz o botão "voltar" do navegador
não reenviar um quiz.

### Onde fica o controle de acesso

| Camada | Como | Onde |
|---|---|---|
| Painel inteiro | `@staff_member_required` | `painel/views.py`, em toda view |
| Resultado e tentativas | Regra própria (contrato C6) | [`quiz/permissoes.py`](../backend/quiz/permissoes.py) |
| Links de quiz/avaliação | Token UUID + `ativo=True` | `acessar_questionario`, `_link_ativo` |

A regra do C6 é a que tem jeito próprio: tentativa **com dono** só o dono vê;
tentativa **anônima** só o navegador que a respondeu vê, porque o `pk` ficou na
sessão. Qualquer outro caso é `Http404` — não `403`, para não confirmar que o id existe.

---

## 🎨 4. Template — onde o HTML nasce

### Como o Django acha os arquivos

`core/settings.py` liga as duas estratégias ao mesmo tempo:

```python
'DIRS': [BASE_DIR / 'templates'],   # templates do projeto
'APP_DIRS': True,                   # mais o templates/ de cada app
```

Por isso existem dois lugares, e a diferença é proposital:

| Lugar | O que fica lá |
|---|---|
| `backend/templates/` | `base.html`, `componentes/` e as telas do quiz — o que é **do projeto** |
| `backend/<app>/templates/<app>/` | `painel/` (16 arquivos), `accounts/` (4), `avaliacao/` (3), `catalogo/` (1) |

O subdiretório com o nome do app (`painel/templates/painel/`) não é redundância: é o
que evita colisão quando dois apps têm um `inicio.html`.

> [!note] O app `quiz` é a exceção
> Ele **não tem** `templates/` próprio: as telas dele moram em
> `backend/templates/quiz/`, junto do `base.html`. É coerente com o resto — o quiz é o
> fluxo principal do projeto, não um módulo acoplável — mas vale saber ao procurar o
> arquivo.

### A herança em três níveis

```
base.html                     ← topo, rodapé, CSS base, acessibilidade, mensagens
   │
   ├── quiz/quiz.html         ← {% extends "base.html" %}
   ├── quiz/resultado.html
   ├── avaliacao/responder.html
   │
   └── painel/base_painel.html   ← extends base.html e APAGA o que não serve:
          │                         {% block topo %}{% endblock %}
          │                         {% block rodape %}{% endblock %}
          ├── painel/inicio.html
          ├── painel/quiz.html
          └── painel/avaliacoes.html
```

> [!tip] O truque do `base_painel.html`
> O painel herda do mesmo `base.html` do aluno, mas **sobrescreve os blocos com vazio**
> para trocar o cabeçalho do site pelo menu lateral. Reaproveita `<head>`, CSS de
> tokens e o script de acessibilidade sem herdar a navegação do aluno.

Os blocos que o `base.html` oferece: `title`, `estilos`, `classe_body`, `topo`,
`mensagens`, `content`, `rodape`, `scripts`.

### Componentes incluídos

`templates/componentes/` guarda pedaços reutilizáveis, chamados com `{% include %}`:

| Componente | Para quê | Usado em |
|---|---|---|
| `_campo.html` | Campo de formulário com label, ajuda e erros no padrão do projeto | formulários de conta, painel e avaliação |
| `_barra.html` | Barra de percentual | `resultado.html` (match e áreas), `curso_detalhe.html` |
| `_anel.html` | Anel de afinidade em SVG | `resultado.html`, só no curso em destaque |
| `_topo_voltar.html` | Substitui o `{% block topo %}` por um cabeçalho com "voltar" | `entrar.html`, `criar_conta.html` |
| `_secretaria.html` | Bloco de contato da escola (vem do context processor) | `curso_detalhe.html` |

O `_campo.html` é o que mais aparece, e recebe o campo por parâmetro:

```django
{% include "componentes/_campo.html" with campo=form.email %}
```

Ele lê `campo.errors`, `campo.help_text` e `campo.field.required` — tudo que o
**Form** já sabe. Nenhuma view precisa dizer ao template como desenhar um erro.

### Context processors: o contexto que toda tela recebe

[`core/contexto.py`](../backend/core/contexto.py) injeta duas coisas em **todos** os
templates, sem nenhuma view passar:

```python
def escola(request):
    """Os dados da escola em todo template: {{ escola.nome }}, {{ escola.telefone }}..."""
    return {"escola": settings.ESCOLA}

def versao(request):
    """O commit que está no ar, para o <meta name="versao"> do base.html."""
    return {"versao": settings.VERSAO}
```

Mais os três do Django: `request`, `auth` (o `{{ user }}` do menu) e `messages`.

### O que o template pode e o que não pode fazer

> [!danger] A regra do projeto
> O template **formata**; ele não calcula e não consulta.

O percentual chega pronto da view (`round(rec.score * 100)`). O que o template faz é
coisa de apresentação: `{% widthratio %}` para a largura da barra de progresso,
`|default:''`, `{% url %}` para nunca escrever um endereço na mão.

Quando a formatação é específica demais para um filtro embutido, vira **template tag**
própria — hoje há uma só, em [`painel/templatetags/painel_extras.py`](../backend/painel/templatetags/painel_extras.py):

```python
@register.filter
def duracao(valor):
    """timedelta -> "08:42" (min:seg) ou "1h05" acima de uma hora."""
```

Um `timedelta` virando texto é decisão de tela, não de dado — por isso é filtro, e
não um campo calculado no model.

---

## 🔀 5. Um fluxo completo, camada por camada

O quiz é o caminho mais interessante, porque passa pelas três camadas **várias vezes**:
uma pergunta por requisição.

```
① Coordenação clica "gerar link"        VIEW  painel.gerar_link (@require_POST)
                                        MODEL QuestionarioLink.objects.create()
                                        └─► redirect (PRG)

② Aluno abre /questionario/<uuid>/      VIEW  acessar_questionario
                                        MODEL filtra token + ativo=True
                                        └─► token na SESSÃO, redirect para "/"
                                            (link inválido → link_invalido.html, 404)

③ GET "/" com ?etapa=1                  VIEW  pagina_quiz (ramo GET)
                                        MODEL InicioDeQuiz.objects.create()  ← taxa de conclusão
                                        TPL   quiz/quiz.html

④ POST de cada pergunta                 VIEW  pagina_quiz (ramo POST, incompleto)
                                        └─► guarda na sessão e redireciona para
                                            ?etapa=N#questao-N   (nada no banco ainda)

⑤ POST da última                        VIEW  pagina_quiz (ramo POST, completo)
                                        MODEL Tentativa + Respostas + recomendar()
                                              ...tudo em transaction.atomic()
                                        └─► entregar() FORA da transação (LLM)
                                        └─► redirect para /resultado/<pk>/

⑥ GET /resultado/<pk>/                  VIEW  resultado_pagina (checa C6)
                                        MODEL recomendacoes, ordenadas por rank_final
                                        TPL   quiz/resultado.html → _anel.html

⑦ Aluno salva um curso                  VIEW  accounts.salvar_interesse
                                        MODEL Interesse (snapshot do curso)
```

> [!note] Por que as respostas parciais ficam na sessão
> Até a última pergunta, **nada vai para o banco**. Quem desiste no meio não deixa uma
> tentativa pela metade sujando as métricas do painel — e o único registro de que
> começou é o `InicioDeQuiz`, que não guarda usuário nem sessão: é só uma contagem.

---

## 🧪 6. Como cada camada é testada

A separação MVT aparece na suíte: cada camada tem o seu tipo de teste.

| Camada | Como se testa | Onde |
|---|---|---|
| Engine (funções puras) | Chama função, confere número. Sem banco | `quiz/tests/test_engine_puro.py`, `test_motor.py` |
| Model | Cria objeto, confere constraint e ordenação | `quiz/tests/test_rank_final.py` |
| View | `self.client.get/post`, confere status e redirect | `quiz/tests/test_rotas_web.py`, `accounts/tests/test_c5_rotas.py` |
| Template | `assertContains` no HTML renderizado | `quiz/tests/test_telas.py`, `painel/tests/test_telas.py` |
| Acesso (C6) | Tenta ver tentativa de outro e espera 404 | `accounts/tests/test_c6_claim.py` |

```bash
cd backend
python manage.py test
```

---

## 📌 7. Resumo para decorar

> [!quote] As quatro frases
> 1. **O Model guarda e garante.** Ordenação e unicidade são dele, não da view.
> 2. **A View decide e converte.** Checa acesso, consulta com `select_related`, deixa o
>    dado pronto e redireciona depois de todo POST.
> 3. **O Template só apresenta.** Herda de `base.html`, inclui componentes, não calcula.
> 4. **A engine não é nenhuma das três.** É uma camada de funções puras que a View chama
>    — e é por isso que dá para testá-la sozinha.
