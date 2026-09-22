---
title: "Spec — Pessoa D · Telas do aluno (PR-0 limpeza · PR-7 telas · PR-8 acessibilidade e rotas)"
aliases: ["Spec pessoa D", "Spec telas do aluno", "PR-0 limpeza", "PR-7 telas", "PR-8 acessibilidade", "Passo a passo das telas"]
tags: [tcc, front, django, templates, css, javascript, acessibilidade, spec, passo-a-passo]
status: proposto
projeto: TCC
criado: 2026-09-22
---

> [!info] Mapa: [[Projetos/EducMatch(Secretária)/tarefas-backend-por-pessoa|👥 Tarefas por pessoa]] · Front atual: [[Projetos/EducMatch(Secretária)/front-templates-django|🎨 Templates do Django]] · Contratos: [[contratos-c1-a-c6 🟢|📜 C5 e C6]] · Colegas: [[Projetos/EducMatch(Secretária)/spec-pessoa-a-infra|🧱 A]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-b-dados-motor|🧮 B]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-c-painel|📊 C]]

# 🎨 Spec — Pessoa D · Telas do aluno

> [!abstract] O que esta nota é
> O **como** da frente das telas, arquivo por arquivo. Missão em uma frase: fazer o caminho do aluno (**entrar no quiz → responder → ver o resultado → conhecer o curso → salvar na lista**) funcionar inteiro, **acessível por teclado** e **funcionando mesmo sem JavaScript**.
> Escrita contra o commit `a04c8e9` (branch `chore/remove-react-e-api`).

> [!success] O que já foi verificado (2026-09-22)
> Todo o código desta nota foi aplicado numa **cópia** do repositório, no MySQL local, junto com as specs A, B e C:
> - os **7 testes de tela** novos passam, e os testes de rota do C5 e do C6, que davam erro de import e de nome, passam os **8**;
> - a suíte inteira, com as quatro specs, fecha em **59 testes, 58 verdes** (o vermelho é o do fuso, que fica verde com as tabelas de fuso carregadas).
>
> **Não** verificado: a navegação por teclado e o quiz com o JavaScript desligado. Isso é clique, não teste automático, e está na §9.

> [!important] Por que HTML, CSS e JS puro (decisão de 2026-09-22)
> 1. **Todo o grupo consegue mexer no front**, não só uma pessoa;
> 2. **Um processo, um endereço**: sem API, sem CORS, sem CSRF entre origens;
> 3. **Aprimoramento progressivo**: o quiz é um formulário HTML que funciona **sem JavaScript**; o `quiz.js` só o transforma num passo a passo. Se o JS falhar na apresentação, o quiz continua respondível.
>
> É um parágrafo pronto para a monografia, na seção que explica por que o React saiu.

## 🧭 O mapa

| Tarefa | O que faz | Arquivos | PR |
|---|---|---|---|
| **D-0** | o que a C precisa no `base.html` | `templates/base.html` | PR-0 ou primeiro commit do PR-7 |
| **D-1** | o aviso de baixa confiança que nunca aparecia | `resultado.html` | PR-7 |
| **D-2** | a página do curso (existe, mas ninguém chega nela) | `catalogo/` e `resultado.html` | PR-7 |
| **D-3** | o perfil sem números inventados | `accounts/views.py`, `aluno_perfil.html` | PR-7 |
| **D-4** | "Meus testes" com o 1º curso | `accounts/views.py`, `tentativas.html` | PR-7 |
| **D-5** | o link de questionário da escola | `web_views.py`, `link_invalido.html`, `quiz.html` | PR-8 |
| **D-6** | acessibilidade | `style.css` | PR-8 |
| **D-7** | a base de testes e os testes de rota C5 e C6 | `quiz/tests/base.py`, `accounts/tests/` | PR-8 |

### O que é seu e o que não é

| ✅ Seu | ❌ De outra pessoa |
|---|---|
| `templates/` (menos `quiz/dashboard.html`), `accounts/templates/`, `catalogo/templates/` | `painel/` e `static/css/painel.css` → **C** |
| `static/css/style.css`, `static/js/quiz.js` | `models.py`, migrações, `quiz/engine.py` → **B** |
| `quiz/web_views.py`, `accounts/views.py`, `accounts/urls.py`, `catalogo/views.py`, `catalogo/urls.py` | `core/settings.py` → **A** |
| `quiz/tests/base.py`, `accounts/tests/test_c5_rotas.py`, `test_c6_claim.py`, `quiz/tests/test_telas.py` | |

> [!warning] Três funções que a pessoa B vai mexer nos seus arquivos
> `areas_da_recomendacao` (em `web_views.py`), `_salvar_interesse_pendente` e `salvar_interesse` (em `accounts/views.py`). **Não toque nelas até o PR-2 da B entrar.** O Git junta sozinho mudanças em funções diferentes do mesmo arquivo; o problema é duas pessoas na mesma função.

---

## 0️⃣ PR-0 — fechar a remoção do React e da API

Você já fez o commit `a04c8e9` na branch `chore/remove-react-e-api` e deu push. Falta abrir o PR, **mas antes**:

> [!danger] O commit levou a configuração da sua máquina junto
> O `a04c8e9` muda o `core/settings.py` para `'USER': 'tecmysql'`. Se isso entrar na `main`, quem usa `root` quebra. Tire do PR antes de abrir:
> ```bash
> git switch chore/remove-react-e-api
> git checkout main -- backend/core/settings.py
> git commit -m "chore: nao versiona o usuario do banco desta maquina"
> git push
> ```
> Até o PR-1 da pessoa A entrar, rode o projeto com a sua mudança local sem commitá-la. Depois do PR-1, você usa `DB_USER=tecmysql` no `.env`, e o problema some.

Depois abra o PR, peça revisão e mescle. Avise: "PR-0 entrou: `git pull`. O front agora é só o Django, em `localhost:8000`".

---

## 1️⃣ D-0 — `templates/base.html` (o que a pessoa C precisa)

Faça isto **no primeiro dia**, num commit pequeno no começo do PR-7, e avise a C.

No `<head>`, depois do Font Awesome:

```html
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
    {% block estilos %}{% endblock %}
</head>
```

No menu do usuário, troque o link do dashboard:

```html
<!-- ANTES -->
{% if user.is_superuser %}<a href="{% url 'dashboard' %}">Dashboard</a>{% endif %}

<!-- DEPOIS -->
{% if user.is_staff %}<a href="{% url 'painel-dashboard' %}">Painel</a>{% endif %}
```

> [!note] A segunda troca só funciona depois do PR-4 da C
> `painel-dashboard` só existe quando a C montar a URL. Até lá, faça só o `{% block estilos %}`; a troca do link vai junto com o PR-4 (combine com a C quem faz).

---

## 🚦 Antes do PR-7

```bash
git switch main && git pull              # já com o PR-0
git switch -c feat/telas-aluno           # se já criou a partir do PR-0: git rebase main
python manage.py test 2>&1 | tail -5     # a linha de base
```

**Referências visuais:** `Desktop/guia-de-estilo-educmatch.pdf` e `Desktop/wireframes-educmatch.pdf`. Toda cor e tamanho novos entram como variável no `:root` do `style.css` (o arquivo já tem `--preto`, `--vermelho`, `--linha`...), para ninguém repetir `#e33b32` em 30 lugares.

---

## 2️⃣ D-1 — o aviso de baixa confiança

Em `templates/quiz/resultado.html`, o aviso testava um campo que **não existe**:

```html
<!-- ANTES: nunca aparecia -->
{% if tentativa.confidence_level == "baixa" %}

<!-- DEPOIS -->
{% if tentativa.confidence_band == "baixa" %}
```

✅ Você já fez essa troca no seu clone, e ela ainda não tem commit. Falta o teste que prova (está na §8, `test_aviso_de_baixa_confianca_aparece`).

> [!important] Este é o bug da REC-04
> A spec REC dizia que "o aviso de baixa confiança nunca dispara" e culpava o motor. A causa real era esta linha do template. Vale uma frase na monografia: **o sintoma estava na tela, e a spec procurou no cálculo.**

---

## 3️⃣ D-2 — a página do curso

`templates/quiz/curso_detalhe.html` existe, mas **não tem view nem rota**: ninguém chega nela. E usa campos que não existem (`curso.nome`, `curso.main_area`, `curso.description`).

### `catalogo/views.py` — substitua

```python
from django.shortcuts import get_object_or_404, render

from accounts.models import Interesse
from catalogo.models import Curso


def curso_detalhe(request, pk):
    curso = get_object_or_404(
        Curso.objects.select_related("area_principal"), pk=pk, is_active=True
    )
    # De onde a pessoa veio: permite "voltar para o meu resultado" e salvar
    # o curso com o snapshot daquela tentativa.
    tentativa_id = request.GET.get("tentativa", "")
    if not tentativa_id.isdigit():
        tentativa_id = ""

    salvo = (
        request.user.is_authenticated
        and Interesse.objects.filter(usuario=request.user, curso=curso).exists()
    )
    return render(request, "catalogo/curso_detalhe.html", {
        "curso": curso,
        "tentativa_id": tentativa_id,
        "salvo": salvo,
    })
```

> [!note] Por que o `isdigit()`
> O `tentativa_id` vai parar dentro de um `{% url %}`. Aceitar só números evita que alguém monte um link com texto qualquer ali.

### `catalogo/urls.py` (arquivo novo)

```python
from django.urls import path

from catalogo.views import curso_detalhe

urlpatterns = [
    path("<int:pk>/", curso_detalhe, name="curso-detalhe"),
]
```

### `core/urls.py` — uma linha

```python
    path("cursos/", include("catalogo.urls")),
```

Antes das rotas com prefixo vazio (`""`).

### `catalogo/templates/catalogo/curso_detalhe.html` (arquivo novo)

Apague `templates/quiz/curso_detalhe.html` (`git rm`) e crie este no app do catálogo:

```html
{% extends "base.html" %}

{% block title %}{{ curso.nome_curso }}{% endblock %}

{% block content %}
{% if tentativa_id %}
<a class="botao botao--ghost" href="{% url 'quiz-resultado' tentativa_id %}">
    <span aria-hidden="true">&larr;</span> Voltar para o meu resultado
</a>
{% endif %}

<section>
    <p>Sobre o curso</p>
    <h1>{{ curso.nome_curso }}</h1>

    <ul class="etiquetas">
        <li>{{ curso.area_principal.nome }}</li>
        <li>{{ curso.duracao }} horas</li>
        {% if curso.inicio_dia %}<li>Início em {{ curso.inicio_dia|date:"d/m/Y" }}</li>{% endif %}
    </ul>

    <h2>Descrição</h2>
    <p>{{ curso.descricao|linebreaksbr }}</p>

    <form method="post" action="{% url 'interesse-salvar' %}">
        {% csrf_token %}
        <input type="hidden" name="curso_id" value="{{ curso.id }}">
        {% if tentativa_id %}<input type="hidden" name="tentativa_id" value="{{ tentativa_id }}">{% endif %}
        <button class="botao" type="submit">
            {% if salvo %}Remover da minha lista{% else %}Salvar na minha lista{% endif %}
        </button>
    </form>
</section>
{% endblock %}
```

### `templates/quiz/resultado.html` — o nome do curso vira link

No destaque:

```html
<!-- ANTES -->
        <h2>{{ destaque.curso.nome_curso }}</h2>

<!-- DEPOIS -->
        <h2>
            <a href="{% url 'curso-detalhe' destaque.curso.id %}?tentativa={{ tentativa.pk }}">{{ destaque.curso.nome_curso }}</a>
        </h2>
```

Nos outros quatro:

```html
<!-- ANTES -->
                <h3>{{ item.curso.nome_curso }}</h3>

<!-- DEPOIS -->
                <h3>
                    <a href="{% url 'curso-detalhe' item.curso.id %}?tentativa={{ tentativa.pk }}">{{ item.curso.nome_curso }}</a>
                </h3>
```

---

## 4️⃣ D-3 — o perfil sem números inventados

A view `aluno_perfil` mandava para a tela `aulas_concluidas`, `horas_estudadas`, `exercicios_feitos` e `sequencia_dias`, **todos fixos em 0**. O sistema não mede nada disso. Na banca, número inventado na tela é pergunta difícil.

### `accounts/views.py` — a função `aluno_perfil`, do `tentativas =` até o fim

```python
    tentativas = Tentativa_de_resposta.objects.filter(user=request.user).prefetch_related(
        "recomendacoes__curso"
    )
    historico = []
    for tentativa in tentativas:
        # recomendacoes vem ordenada por rank (Meta.ordering): a primeira é o 1º lugar
        destaque = next(iter(tentativa.recomendacoes.all()), None)
        historico.append({
            "tentativa_id": tentativa.pk,
            "curso": destaque.curso if destaque else None,
            "match": round(destaque.score * 100) if destaque else None,
            "data": tentativa.criado_em,
        })

    # Só o que o sistema mede de verdade: nada de aulas, horas ou sequência de dias.
    return render(request, "quiz/aluno_perfil.html", {
        "total_de_testes": len(historico),
        "total_na_lista": Interesse.objects.filter(usuario=request.user).count(),
        "historico": historico,
    })
```

> [!note] Por que `next(iter(...all()))` e não `.first()`
> O `.first()` faz uma consulta nova para cada tentativa e joga fora o `prefetch_related`. O `.all()` usa o que já veio.

### `templates/quiz/aluno_perfil.html` — substitua

```html
{% extends "base.html" %}

{% block title %}Meu perfil{% endblock %}

{% block content %}
<section>
    <p>Meu perfil</p>
    <h1>{{ user.first_name|default:user.email }}</h1>

    {# Só números que o sistema mede de verdade #}
    <ul class="perfil__numeros">
        <li><strong>{{ total_de_testes }}</strong> {{ total_de_testes|pluralize:"teste feito,testes feitos" }}</li>
        <li><strong>{{ total_na_lista }}</strong> {{ total_na_lista|pluralize:"curso na lista,cursos na lista" }}</li>
    </ul>

    <h2>Histórico de resultados</h2>
    {% for item in historico %}
    <article>
        <h3>
            <a href="{% url 'quiz-resultado' item.tentativa_id %}">
                {{ item.curso.nome_curso|default:"Resultado sem curso" }}
            </a>
        </h3>
        <p>
            {% if item.match is not None %}{{ item.match }}% de afinidade · {% endif %}
            {{ item.data|date:"d/m/Y" }} às {{ item.data|date:"H:i" }}
        </p>
    </article>
    {% empty %}
    <p>Você ainda não fez o teste com a conta logada.</p>
    {% endfor %}

    <a class="botao" href="{% url 'quiz-inicio' %}">Fazer o teste de novo</a>
</section>
{% endblock %}
```

E apague o template vazio que ninguém usa:

```bash
git rm accounts/templates/accounts/perfil.html
```

---

## 5️⃣ D-4 — "Meus testes" com o 1º curso

### `accounts/views.py` — `minhas_tentativas`

```python
@login_required
def minhas_tentativas(request):
    tentativas = Tentativa_de_resposta.objects.filter(user=request.user).prefetch_related(
        "recomendacoes__curso"
    )
    return render(request, "accounts/tentativas.html", {"tentativas": tentativas})
```

### `accounts/templates/accounts/tentativas.html` — substitua

```html
{% extends "base.html" %}

{% block title %}Meus testes{% endblock %}

{% block content %}
<section>
    <p>Sua conta</p>
    <h1>Meus testes</h1>

    {% for tentativa in tentativas %}
    {% with principal=tentativa.recomendacoes.all.0 %}
    <article>
        <h3>Teste de {{ tentativa.criado_em|date:"d/m/Y" }} às {{ tentativa.criado_em|date:"H:i" }}</h3>
        {% if principal %}
        <p>1º lugar: <strong>{{ principal.curso.nome_curso }}</strong></p>
        {% endif %}
        <a href="{% url 'quiz-resultado' tentativa.pk %}">
            Ver resultado <span aria-hidden="true">&rarr;</span>
        </a>
    </article>
    {% endwith %}
    {% empty %}
    <p>Você ainda não fez o teste com a conta logada.</p>
    <a class="botao" href="{% url 'quiz-inicio' %}">Fazer o teste</a>
    {% endfor %}
</section>
{% endblock %}
```

Commit do PR-7: `feat(telas): detalhe do curso, perfil sem numeros inventados e aviso de confianca`.

---

## 6️⃣ D-5 — o link de questionário da escola (PR-8)

```bash
git switch main && git pull
git switch -c feat/telas-acessibilidade
```

Hoje, token inexistente ou encerrado em `/questionario/<token>/` mostra o 404 padrão do Django, em inglês. E quem entra pelo link não fica sabendo.

### `quiz/web_views.py` — `acessar_questionario`

```python
# ANTES
def acessar_questionario(request, token):
    link = get_object_or_404(QuestionarioLink, token=token, ativo=True)
    request.session["questionario_link_token"] = str(link.token)
```

```python
# DEPOIS
def acessar_questionario(request, token):
    link = QuestionarioLink.objects.filter(token=token, ativo=True).first()
    if link is None:
        return render(request, "quiz/link_invalido.html", status=404)
    request.session["questionario_link_token"] = str(link.token)
```

E em `pagina_quiz`, no dicionário do `render` do GET, uma chave a mais:

```python
                "quiz_iniciado": bool(respondido_por or etapa),
                "via_link": bool(request.session.get("questionario_link_token")),
```

### `templates/quiz/link_invalido.html` (arquivo novo)

```html
{% extends "base.html" %}

{% block title %}Link encerrado{% endblock %}

{% block content %}
<section>
    <p>Link de questionário</p>
    <h1>Este link não existe ou foi encerrado</h1>
    <p>
        Confira com a sua escola se o endereço está certo. Você também pode fazer
        o teste por conta própria: o resultado é o mesmo, só não fica ligado à turma.
    </p>
    <a class="botao" href="{% url 'quiz-inicio' %}">Fazer o teste mesmo assim</a>
</section>
{% endblock %}
```

### A faixa "link da escola"

Em `templates/quiz/quiz.html`, logo depois de `{% block content %}`:

```html
{% if via_link %}
<p class="faixa-link" role="note">Você está respondendo pelo link da escola.</p>
{% endif %}
```

Em `templates/quiz/resultado.html`, logo depois de `<p>Resultado do seu perfil</p>`:

```html
    {% if tentativa.questionario_link_id %}
    <p class="faixa-link" role="note">Você respondeu pelo link da escola.</p>
    {% endif %}
```

---

## 7️⃣ D-6 — acessibilidade

### `static/css/style.css` — no fim do arquivo

Hoje o CSS **não tem nenhuma regra de foco**: quem navega pelo teclado não vê onde está.

```css
/* ---------- Acessibilidade ---------- */

/* Foco sempre visível para quem navega pelo teclado. Nunca "outline: none" sozinho. */
a:focus-visible,
button:focus-visible,
input:focus-visible,
summary:focus-visible,
.quiz-passo label:focus-within {
  outline: 3px solid var(--vermelho-escuro);
  outline-offset: 3px;
}

/* Alvos de toque de pelo menos 48px: o público responde pelo celular */
.botao,
button,
.quiz-passo label {
  min-height: 48px;
}

/* Quem pediu menos movimento no sistema não vê animação */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation: none !important;
    transition: none !important;
    scroll-behavior: auto !important;
  }
}

.faixa-link {
  background: var(--gelo);
  border-left: 4px solid var(--vermelho);
  padding: 0.6rem 1rem;
  border-radius: 8px;
}
```

### O que conferir no HTML (sem código novo, só não perder)

- [ ] Cada pergunta do `quiz.html` continua sendo um `<fieldset>` com `<legend>` (já é: não perca ao redesenhar). É o que faz o leitor de tela ler a pergunta junto com as opções
- [ ] O aviso "responda antes de avançar" do `quiz.js` e as mensagens de erro com `role="alert"` (o `{{ erro }}` do quiz já tem)
- [ ] A barra de progresso com um texto "Pergunta 3 de 6" (o `[data-contador]` já faz: não esconda com `display: none`)
- [ ] Contraste do texto de pelo menos 4,5:1 (confira as cores do guia num verificador de contraste)

### `static/js/quiz.js` — os comentários que saíram

No `a04c8e9` saíram os comentários que explicavam os trechos não óbvios. **Devolva estes quatro**: são eles que deixam outra pessoa do grupo mexer no arquivo sem quebrar.

```javascript
// Transforma o formulario (que funciona sem JS) num wizard de uma pergunta por vez.
const totalPerguntas = passos.length - 1; // o primeiro passo e a apresentacao
// Se o servidor devolveu erro, comeca na primeira pergunta sem resposta.
void passo.offsetWidth; // reinicia a animacao
// Marcou a resposta: segue sozinho, com uma pausa para o clique ser visto.
// Enter avanca em vez de enviar o formulario pela metade.
```

---

## 8️⃣ D-7 — a base de testes e os testes

### `quiz/tests/base.py` — os métodos que os testes de rota chamam e não existiam

Acrescente à `BaseEducMatch`, e faça o `responder_tudo` usar o `payload_do_quiz`:

```python
    def payload_do_quiz(self, nome="Visitante", coluna=0):
        """O POST do formulario do quiz, escolhendo sempre a alternativa `coluna`."""
        from quiz.models import Questao

        dados = {"respondido_por": nome}
        for questao in Questao.objects.filter(is_active=True).order_by("id"):
            alternativas = list(questao.alternativas.order_by("id"))
            dados[f"questao_{questao.id}"] = alternativas[coluna % len(alternativas)].id
        return dados

    def responder_tudo(self, nome="Visitante", coluna=0):
        """Responde o quiz inteiro pelo formulario. Devolve a resposta HTTP."""
        return self.client.post("/", self.payload_do_quiz(nome, coluna))

    def criar_tentativa(self, dono=None, coluna=0):
        """Uma tentativa ja calculada pela engine, com ou sem dono."""
        from quiz.engine import recomedacao
        from quiz.models import Questao, Resposta, Tentativa_de_resposta

        tentativa = Tentativa_de_resposta.objects.create(user=dono, respondido_por="Teste")
        for questao in Questao.objects.filter(is_active=True).order_by("id"):
            alternativas = list(questao.alternativas.order_by("id"))
            Resposta.objects.create(
                tentativa=tentativa, questao=questao,
                alternativa=alternativas[coluna % len(alternativas)],
            )
        recomedacao(tentativa)
        return tentativa

    def dados_de_cadastro(self, email="ana@exemplo.com"):
        return {
            "first_name": "Ana",
            "email": email,
            "password1": "afinidade-2026",
            "password2": "afinidade-2026",
        }
```

> [!warning] A `quiz/tests/base.py` é usada pelos quatro
> B e C herdam dela. Só **acrescente** métodos; não mude a assinatura dos que existem (`criar_usuario`, `responder_tudo`).

### `accounts/tests/test_c5_rotas.py` — o que muda

O arquivo inteiro dava `ImportError` (importava `accounts.tests_helpers`, que não existe) e usava nomes de rota errados:

| Estava | Fica | Por quê |
|---|---|---|
| `from accounts.tests_helpers import criar_usuario` + `TestCase` | `from quiz.tests.base import BaseEducMatch` | o módulo nunca existiu; a base já tem `criar_usuario` e `criar_tentativa` |
| `"interesse-lista"` | `"lista_interesse"` | é o `name` real em `accounts/urls.py` |
| `"sair"` | `"logout"` | idem |
| `assertIn(status, (405, 302))` | `assertEqual(status, 405)` | as duas rotas são só POST: aceitar 302 escondia um GET que funcionasse |

O `setUp` passa a chamar `super().setUp()` e `self.criar_usuario(...)`:

```python
class C5AutorizacaoTest(BaseEducMatch):
    ROTAS_PROTEGIDAS = [
        ("lista_interesse", {}),
        ("minhas-tentativas", {}),
        ("aluno-perfil", {}),
    ]

    def setUp(self):
        super().setUp()
        self.dono = self.criar_usuario("dono@exemplo.com")
        self.outro = self.criar_usuario("outro@exemplo.com")

    # ... os três testes do meio ficam iguais ...

    def test_toda_rota_de_escrita_recusa_GET(self):
        """Salvar interesse e sair sao POST. Link que faz GET e 405, nao acao."""
        self.client.force_login(self.dono)
        for nome in ("interesse-salvar", "logout"):
            with self.subTest(rota=nome):
                resposta = self.client.get(reverse(nome))
                self.assertEqual(resposta.status_code, 405)
```

### `accounts/tests/test_c6_claim.py` — o que muda

- `reverse("criar-conta")` → `reverse("cadastro_usuario")`, nas **quatro** ocorrências
- o dicionário de cadastro escrito à mão no primeiro teste vira `self.dados_de_cadastro()`
- `payload_do_quiz`, `dados_de_cadastro` e `criar_tentativa` passam a existir (vêm da base acima)

### `quiz/tests/test_telas.py` (arquivo novo)

```python
import uuid

from django.urls import reverse

from catalogo.models import Curso
from quiz.models import QuestionarioLink, Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch


class TelasDoAlunoTest(BaseEducMatch):
    def responder(self, **kwargs):
        self.responder_tudo(**kwargs)
        return Tentativa_de_resposta.objects.latest("id")

    def test_aviso_de_baixa_confianca_aparece(self):
        """O template testava `confidence_level`, que não existe: o aviso nunca aparecia."""
        tentativa = self.responder()
        Tentativa_de_resposta.objects.filter(pk=tentativa.pk).update(confidence_band="baixa")

        resposta = self.client.get(reverse("quiz-resultado", args=[tentativa.pk]))

        self.assertContains(resposta, "afinidade com os cursos disponiveis ficou baixa")

    def test_resultado_leva_ao_detalhe_do_curso(self):
        tentativa = self.responder()
        primeiro = tentativa.recomendacoes.get(rank=1).curso

        resposta = self.client.get(reverse("quiz-resultado", args=[tentativa.pk]))

        destino = reverse("curso-detalhe", args=[primeiro.pk]) + f"?tentativa={tentativa.pk}"
        self.assertContains(resposta, destino)

    def test_detalhe_do_curso_mostra_o_curso_e_volta_ao_resultado(self):
        curso = Curso.objects.first()

        resposta = self.client.get(reverse("curso-detalhe", args=[curso.pk]) + "?tentativa=7")

        self.assertContains(resposta, curso.nome_curso)
        self.assertContains(resposta, reverse("quiz-resultado", args=[7]))

    def test_curso_desativado_nao_tem_pagina(self):
        curso = Curso.objects.first()
        Curso.objects.filter(pk=curso.pk).update(is_active=False)

        resposta = self.client.get(reverse("curso-detalhe", args=[curso.pk]))

        self.assertEqual(resposta.status_code, 404)

    def test_perfil_so_mostra_numeros_que_o_sistema_mede(self):
        usuario = self.criar_usuario()
        self.client.force_login(usuario)
        self.responder()

        resposta = self.client.get(reverse("aluno-perfil"))

        self.assertNotIn("estatisticas", resposta.context)
        self.assertEqual(resposta.context["total_de_testes"], 1)
        self.assertEqual(resposta.context["total_na_lista"], 0)

    def test_link_de_questionario_inexistente_tem_pagina_propria(self):
        resposta = self.client.get(reverse("questionario-link", args=[uuid.uuid4()]))

        self.assertEqual(resposta.status_code, 404)
        self.assertContains(resposta, "não existe ou foi encerrado", status_code=404)

    def test_quem_entra_pelo_link_ve_o_aviso(self):
        link = QuestionarioLink.objects.create()

        self.client.get(reverse("questionario-link", args=[link.token]))
        resposta = self.client.get(reverse("quiz-inicio"))

        self.assertContains(resposta, "link da escola")
```

Os cinco primeiros entram no **PR-7**; os dois do link, no **PR-8**. Eles só respondem certo depois do PR-1 da pessoa A (o `ALLOWED_HOSTS`).

---

## 9️⃣ Verificação

```bash
python manage.py test quiz.tests.test_telas accounts.tests.test_c5_rotas accounts.tests.test_c6_claim -v 2
python manage.py test 2>&1 | tail -5       # nenhuma falha nova
```

E os cliques, que nenhum teste faz:

| # | O quê | Sinal de que passou |
|---|---|---|
| 1 | O caminho inteiro sem digitar URL: início → quiz → resultado → detalhe → salvar → Minha lista → Meus testes → abrir o resultado de novo | Nenhum beco sem saída |
| 2 | Responder tudo na mesma coluna | Aparece o aviso de baixa confiança |
| 3 | **Só com o teclado** (Tab, setas, Enter, Espaço), com o mouse longe | Responde o quiz inteiro, e sempre dá para ver onde está o foco |
| 4 | **JavaScript desligado** (DevTools → ⚙️ → Desativar JavaScript) | Responde o quiz inteiro, uma página por pergunta |
| 5 | `/questionario/00000000-0000-0000-0000-000000000000/` | A página "não existe ou foi encerrado", em português |
| 6 | Um colega faz o caminho no celular dele, sem ajuda | Consegue |

Commit do PR-8: `feat(telas): acessibilidade, link de questionario e testes de rota C5 e C6`.

---

## 🔟 Você também é quem conhece o front

- [ ] Revisar o template do painel da pessoa C (acessibilidade das tabelas, o `—` com explicação)
- [ ] Fazer o primeiro PR de cada colega junto, pelo Live Share, **com o colega como anfitrião** (a branch é dele)

## ⚠️ Armadilhas

> [!danger] Não troque formulário por `fetch`
> Vindo do React, a tentação é mandar as respostas por JavaScript. Não faça: é o formulário que mantém o quiz funcionando sem JS, e cada `fetch` reabre o problema de CSRF que o projeto acabou de eliminar. JavaScript aqui só **melhora** um HTML que já funciona.

> [!warning] CSS e JS não atualizam no navegador
> O navegador guarda os arquivos estáticos em cache. Se a mudança não aparece, `Ctrl+F5`.

> [!note] Todo `<form method="post">` precisa de `{% csrf_token %}`
> Sem ele, o erro é um 403 "CSRF verification failed", que parece bug do backend.

## ▶️ Próxima ação

Tirar o `settings.py` do PR-0 (§0), abrir o PR-0, e fazer o D-0 no `base.html` para a pessoa C.

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/tarefas-backend-por-pessoa|👥 Tarefas por pessoa]]
- [[Projetos/EducMatch(Secretária)/front-templates-django|🎨 Templates do Django]]
- [[contratos-c1-a-c6 🟢|📜 C5 e C6]] — o que os testes de rota provam
