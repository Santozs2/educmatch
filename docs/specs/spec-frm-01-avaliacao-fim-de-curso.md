---
title: "Spec FRM-01 — avaliação de fim de curso: app, perguntas e página do aluno"
aliases: ["FRM-01", "Avaliação de fim de curso", "app avaliacao"]
tags: [tcc, spec, avaliacao, formulario, lgpd, privacidade, migracao]
status: proposto
projeto: TCC
branch: feature/avaliacao-fim-de-curso
criado: 2026-10-01
---

> [!info] Plano: [[plano-dashboard-git-flow|🖥️ Dashboard novo e Git Flow]] · Anterior: [[spec-dsh-03-conclusao-e-tempo|DSH-03]] · Próxima: [[spec-frm-02-painel-avaliacoes|FRM-02 — avaliações no painel]]

# 📝 FRM-01: avaliação de fim de curso

**Branch:** `feature/avaliacao-fim-de-curso`, saindo da `develop` **com a DSH-03 já mesclada**
**Risco:** baixo. App novo, com migração própria (`avaliacao.0001`). Não toca no quiz nem no painel.
**Testes ao final:** 125 (114 + 11 novos)

> [!abstract] O que esta branch faz
> Cria o app `avaliacao`, que é o "formulário" do design, já com o escopo decidido:
> 1. **Perguntas fixas**, vindas de um seed (`seed_avaliacao`) e editáveis no admin. Não tem construtor.
> 2. **Um link por turma** de um curso (`LinkDeAvaliacao`), igual em espírito ao link do quiz.
> 3. A **página do aluno** em `/avaliacao/<token>/`, sem login, que grava uma resposta **anônima por construção**.
>
> O painel (gerar link pela tela, resultados, CSV) é a [[spec-frm-02-painel-avaliacoes|FRM-02]]. Até lá, o link pode ser criado pelo admin.

---

## 1️⃣ As decisões de 2026-10-01

| Pergunta | Decisão | O que isso muda no código |
|---|---|---|
| Algum formulário aparece no fim do quiz? | **Não.** A avaliação é aplicada **no fim do curso técnico** | A tela de resultado do aluno não muda. O app não depende do `quiz` |
| Como o aluno chega? | **Link por turma** | `LinkDeAvaliacao` com `curso` + `turma`, aberto sem login |
| As respostas são anônimas? | **Sempre** | Nenhum model guarda usuário, nome, e-mail, IP ou horário |
| Ligado a um curso do catálogo? | **Sim** | O link aponta para `catalogo.Curso`; os resultados comparam cursos |
| Construtor de formulários? | **Não. Avaliação fixa** | `Pergunta` com 4 tipos, criada por seed. Os 8 tipos e o construtor do design ficam para depois, se houver demanda |

## 2️⃣ Registrar o app

Crie o app (`python manage.py startapp avaliacao`), apague o `avaliacao/tests.py` que ele gera (os testes vão numa pasta) e registre:

```diff
@@ -48,6 +48,7 @@ INSTALLED_APPS = [
     'catalogo',
     'accounts',
     'painel',
+    'avaliacao',
 ]
 
 AUTH_USER_MODEL = 'accounts.User'
```

```diff
@@ -7,4 +7,5 @@ urlpatterns = [
     path("", include("accounts.urls")),
     path("", include("quiz.web_urls")),
     path("cursos/", include("catalogo.urls")),
+    path("avaliacao/", include("avaliacao.urls")),
 ]
\ No newline at end of file
```

## 3️⃣ `avaliacao/models.py`

```python
"""Avaliação de fim de curso: perguntas fixas, um link por turma, respostas anônimas.

Nenhum model deste app guarda usuário, nome, e-mail, IP ou horário. A resposta
sabe só o link (e por ele o curso e a turma) e o DIA em que chegou. É isso que
permite dizer à turma "é anônimo" sem precisar de promessa: não há onde guardar.
"""
import uuid

from django.conf import settings
from django.db import models


class Pergunta(models.Model):
    TIPOS = [
        ("nps", "Nota de 0 a 10"),
        ("escala", "Escala de 1 a 5"),
        ("escolha", "Escolha única"),
        ("texto", "Texto livre"),
    ]

    texto = models.CharField(max_length=200)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    # Só para "escolha": a lista de opções, na ordem em que aparecem.
    opcoes = models.JSONField(default=list, blank=True)
    obrigatoria = models.BooleanField(default=True)
    ordem = models.PositiveSmallIntegerField(unique=True)
    ativa = models.BooleanField(default=True)

    class Meta:
        ordering = ["ordem"]

    def __str__(self):
        return f"{self.ordem}. {self.texto}"


class LinkDeAvaliacao(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    curso = models.ForeignKey("catalogo.Curso", on_delete=models.PROTECT, related_name="links_de_avaliacao")
    turma = models.CharField(max_length=60, help_text='Como a escola chama a turma. Ex.: "2026/1 · Noite"')
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "link de avaliação"
        verbose_name_plural = "links de avaliação"

    def __str__(self):
        return f"{self.curso} · {self.turma}"


class RespostaDeAvaliacao(models.Model):
    link = models.ForeignKey(LinkDeAvaliacao, on_delete=models.PROTECT, related_name="respostas")
    # Data e não data e hora: "respondeu às 10h14" junto com a turma aponta para uma pessoa.
    respondido_em = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "resposta de avaliação"
        verbose_name_plural = "respostas de avaliação"


class ItemDeResposta(models.Model):
    resposta = models.ForeignKey(RespostaDeAvaliacao, on_delete=models.CASCADE, related_name="itens")
    pergunta = models.ForeignKey(Pergunta, on_delete=models.PROTECT, related_name="itens")
    numero = models.PositiveSmallIntegerField(null=True, blank=True)  # nps e escala
    texto = models.TextField(blank=True)  # escolha e texto

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["resposta", "pergunta"], name="uma_resposta_por_pergunta"),
        ]
```

> [!danger] Anônimo **por construção**, e não por promessa
> | Escolha | Por quê |
> |---|---|
> | `RespostaDeAvaliacao` **sem** `user`, mesmo quando o aluno está logado | Se o campo existisse, alguém um dia o preencheria "só para conferir". Sem o campo, não há como |
> | `respondido_em` é **`DateField`**, e não `DateTimeField` | Numa turma de 20, "respondeu às 10h14" junto com a turma aponta para uma pessoa. O dia não aponta |
> | Nada de IP nem `session_key` | Os dois identificam o aparelho |
> | `PROTECT` em `link` e `pergunta` | Apagar um link ou uma pergunta não pode apagar respostas em silêncio. Para tirar uma pergunta, desligue `ativa` |
>
> Os testes `AnonimatoTest` travam os dois primeiros itens. Isso é o que permite escrever na tela do aluno "é anônimo" sem mentir, e é um bom argumento de LGPD para a banca.

### A migração

```bash
cd backend
python manage.py makemigrations avaliacao
```

A saída tem de ser:

```
Migrations for 'avaliacao':
  avaliacao\migrations\0001_initial.py
    + Create model Pergunta
    + Create model LinkDeAvaliacao
    + Create model RespostaDeAvaliacao
    + Create model ItemDeResposta
```

## 4️⃣ As perguntas: `avaliacao/management/commands/seed_avaliacao.py`

Crie também os `__init__.py` vazios em `avaliacao/management/` e `avaliacao/management/commands/`.

```python
from django.core.management.base import BaseCommand
from django.db import transaction

from avaliacao.models import Pergunta

# A avaliação de fim de curso. É uma PROPOSTA: a coordenação revisa o texto aqui
# (ou no admin) antes da primeira turma. Rodar de novo atualiza pela "ordem".
PERGUNTAS = [
    {
        "ordem": 1,
        "tipo": "nps",
        "texto": "De 0 a 10, quanto você recomendaria este curso a um amigo?",
    },
    {
        "ordem": 2,
        "tipo": "escala",
        "texto": "O curso atendeu às suas expectativas?",
    },
    {
        "ordem": 3,
        "tipo": "escala",
        "texto": "Como você avalia os instrutores?",
    },
    {
        "ordem": 4,
        "tipo": "escala",
        "texto": "Como você avalia a estrutura (laboratórios, equipamentos e materiais)?",
    },
    {
        "ordem": 5,
        "tipo": "escala",
        "texto": "O que você aprendeu vai ajudar no seu próximo passo profissional?",
    },
    {
        # A pergunta que liga a avaliação ao TCC: a recomendação do quiz acertou?
        "ordem": 6,
        "tipo": "escolha",
        "texto": "O curso combinou com o que o quiz do EducMatch tinha mostrado para você?",
        "opcoes": ["Sim", "Em parte", "Não", "Não fiz o quiz"],
    },
    {
        "ordem": 7,
        "tipo": "texto",
        "texto": "O que poderia melhorar no curso?",
        "obrigatoria": False,
    },
]


class Command(BaseCommand):
    help = "Cria ou atualiza as perguntas da avaliação de fim de curso."

    @transaction.atomic
    def handle(self, *args, **options):
        for dados in PERGUNTAS:
            padrao = {"opcoes": [], "obrigatoria": True, "ativa": True, **dados}
            ordem = padrao.pop("ordem")
            Pergunta.objects.update_or_create(ordem=ordem, defaults=padrao)
        self.stdout.write(self.style.SUCCESS(f"{len(PERGUNTAS)} perguntas da avaliação"))
```

> [!warning] As perguntas são uma **proposta**
> Elas foram escritas para esta spec, e não vieram da coordenação. Antes da primeira turma, revise o texto **aqui no seed** (e rode de novo) ou direto no admin. Como o formulário é montado a partir do banco (seção 5️⃣), trocar uma pergunta não mexe em nenhuma linha de código.
>
> A **pergunta 6** ("o curso combinou com o que o quiz tinha mostrado?") é a ponte com o TCC: é a primeira medida, vinda do próprio aluno, de se a recomendação acertou.

## 5️⃣ `avaliacao/forms.py` (novo)

```python
from django import forms


def _campo(pergunta):
    """Um campo do Django para cada tipo de pergunta."""
    comum = {"label": pergunta.texto, "required": pergunta.obrigatoria}
    if pergunta.tipo == "nps":
        return forms.TypedChoiceField(
            choices=[(n, n) for n in range(11)], coerce=int, widget=forms.RadioSelect, **comum
        )
    if pergunta.tipo == "escala":
        return forms.TypedChoiceField(
            choices=[(n, n) for n in range(1, 6)], coerce=int, widget=forms.RadioSelect, **comum
        )
    if pergunta.tipo == "escolha":
        return forms.ChoiceField(
            choices=[(opcao, opcao) for opcao in pergunta.opcoes], widget=forms.RadioSelect, **comum
        )
    return forms.CharField(max_length=1000, widget=forms.Textarea(attrs={"rows": 4}), **comum)


class FormularioDeAvaliacao(forms.Form):
    """Montado na hora a partir das perguntas ativas: trocar o seed troca o formulário."""

    def __init__(self, perguntas, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.perguntas = list(perguntas)
        for pergunta in self.perguntas:
            self.fields[f"pergunta_{pergunta.id}"] = _campo(pergunta)

    def campos_por_pergunta(self):
        """(pergunta, campo do form) na ordem, para o template saber o tipo de cada um."""
        return [(pergunta, self[f"pergunta_{pergunta.id}"]) for pergunta in self.perguntas]
```

## 6️⃣ `avaliacao/views.py` e `avaliacao/urls.py`

```python
from django.db import transaction
from django.shortcuts import redirect, render

from .forms import FormularioDeAvaliacao
from .models import ItemDeResposta, LinkDeAvaliacao, Pergunta, RespostaDeAvaliacao

# Os links que este navegador já respondeu. É uma trava leve: impede o envio
# repetido sem querer (duplo clique, voltar e reenviar), mas não é um controle
# forte. Um controle forte exigiria saber quem respondeu, e aí não seria anônimo.
CHAVE_SESSAO = "avaliacoes_respondidas"


def _link_ativo(token):
    return LinkDeAvaliacao.objects.select_related("curso").filter(token=token, ativo=True).first()


def responder(request, token):
    link = _link_ativo(token)
    if link is None:
        return render(request, "avaliacao/link_invalido.html", status=404)
    if link.pk in request.session.get(CHAVE_SESSAO, []):
        return redirect("avaliacao-obrigado", token=token)

    perguntas = Pergunta.objects.filter(ativa=True)
    form = FormularioDeAvaliacao(perguntas, request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            resposta = RespostaDeAvaliacao.objects.create(link=link)
            itens = []
            for pergunta in form.perguntas:
                valor = form.cleaned_data.get(f"pergunta_{pergunta.id}")
                if valor in (None, ""):
                    continue  # pergunta opcional deixada em branco
                if pergunta.tipo in ("nps", "escala"):
                    itens.append(ItemDeResposta(resposta=resposta, pergunta=pergunta, numero=valor))
                else:
                    itens.append(ItemDeResposta(resposta=resposta, pergunta=pergunta, texto=valor.strip()))
            ItemDeResposta.objects.bulk_create(itens)

        respondidas = request.session.get(CHAVE_SESSAO, [])
        request.session[CHAVE_SESSAO] = respondidas + [link.pk]
        return redirect("avaliacao-obrigado", token=token)

    return render(request, "avaliacao/responder.html", {"link": link, "form": form})


def obrigado(request, token):
    link = LinkDeAvaliacao.objects.select_related("curso").filter(token=token).first()
    return render(request, "avaliacao/obrigado.html", {"link": link})
```

> [!note] A trava de "já respondeu" é leve de propósito
> Ela usa a sessão do navegador. Segura o duplo clique e o "voltar e reenviar", mas um aluno com outro navegador consegue responder de novo. Uma trava forte exigiria saber **quem** respondeu, e isso desfaria o anonimato. Para uma avaliação de turma, esse é o equilíbrio certo, e vale dizer isso na banca se perguntarem.

```python
from django.urls import path

from . import views

urlpatterns = [
    path("<uuid:token>/", views.responder, name="avaliacao-responder"),
    path("<uuid:token>/obrigado/", views.obrigado, name="avaliacao-obrigado"),
]
```

## 7️⃣ `avaliacao/admin.py`

```python
from django.contrib import admin

from .models import LinkDeAvaliacao, Pergunta


@admin.register(Pergunta)
class PerguntaAdmin(admin.ModelAdmin):
    list_display = ["ordem", "texto", "tipo", "obrigatoria", "ativa"]
    list_display_links = ["texto"]
    list_filter = ["tipo", "ativa"]


@admin.register(LinkDeAvaliacao)
class LinkDeAvaliacaoAdmin(admin.ModelAdmin):
    list_display = ["curso", "turma", "criado_em", "ativo"]
    list_filter = ["ativo", "curso"]
    readonly_fields = ["token", "criado_em", "criado_por"]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)

# As respostas não entram no admin de propósito: o lugar delas é o painel,
# agregado e com supressão. Uma lista resposta a resposta no admin desfaria isso.
```

## 8️⃣ Telas do aluno

Ficam em `avaliacao/templates/avaliacao/`.

### `responder.html`

```html
{% extends "base.html" %}
{% load static %}

{% block title %}Avaliação do curso{% endblock %}
{% block estilos %}<link rel="stylesheet" href="{% static 'css/avaliacao.css' %}">{% endblock %}

{% block content %}
<form class="cartao avaliacao entrada" method="post" novalidate>
    {% csrf_token %}
    <header class="avaliacao__topo">
        <p class="chip">Avaliação de fim de curso</p>
        <h1>{{ link.curso.nome_curso }}</h1>
        <p class="subtitulo">Turma {{ link.turma }} · leva uns 3 minutos.</p>
        <p class="aviso avaliacao__anonimo" role="note">
            <i class="fa-solid fa-lock" aria-hidden="true"></i>
            É anônimo: não pedimos nome nem e-mail, e a escola só vê os resultados somados da turma.
        </p>
    </header>

    {% if form.errors %}
    <p class="campo__erro avaliacao__resumo-erro" role="alert">Faltou responder algumas perguntas. Elas estão marcadas abaixo.</p>
    {% endif %}

    {% for pergunta, campo in form.campos_por_pergunta %}
    <fieldset class="avaliacao__pergunta{% if campo.errors %} avaliacao__pergunta--erro{% endif %}">
        <legend>
            {{ forloop.counter }}. {{ pergunta.texto }}
            {% if not pergunta.obrigatoria %}<span class="campo__opcional">(opcional)</span>{% endif %}
        </legend>

        {% if pergunta.tipo == "texto" %}
        <label class="visualmente-oculto" for="{{ campo.id_for_label }}">{{ pergunta.texto }}</label>
        {{ campo }}
        {% else %}
        <div class="avaliacao__opcoes avaliacao__opcoes--{{ pergunta.tipo }}">
            {% for opcao in campo %}
            <label class="avaliacao__opcao">{{ opcao.tag }}<span>{{ opcao.choice_label }}</span></label>
            {% endfor %}
        </div>
        {% if pergunta.tipo == "nps" %}
        <p class="avaliacao__legenda"><span>0 = nada provável</span><span>10 = com certeza</span></p>
        {% elif pergunta.tipo == "escala" %}
        <p class="avaliacao__legenda"><span>1 = muito ruim</span><span>5 = excelente</span></p>
        {% endif %}
        {% endif %}

        {% for erro in campo.errors %}<p class="campo__erro" role="alert">{{ erro }}</p>{% endfor %}
    </fieldset>
    {% endfor %}

    <button class="botao botao--bloco" type="submit">Enviar avaliação</button>
</form>
{% endblock %}
```

### `obrigado.html`

```html
{% extends "base.html" %}

{% block title %}Avaliação enviada{% endblock %}

{% block content %}
<section class="cartao cartao--centro entrada">
    <h1>Obrigado pela avaliação!</h1>
    <p class="subtitulo">
        {% if link %}Suas respostas sobre {{ link.curso.nome_curso }} foram registradas.{% else %}Suas respostas foram registradas.{% endif %}
        Elas ajudam a escola a melhorar o curso para as próximas turmas.
    </p>
</section>
{% endblock %}
```

### `link_invalido.html`

```html
{% extends "base.html" %}

{% block title %}Link encerrado{% endblock %}

{% block content %}
<section class="cartao cartao--centro entrada">
    <h1>Este link de avaliação não existe ou foi encerrado</h1>
    <p class="subtitulo">Confira o endereço com a coordenação do curso.</p>
</section>
{% endblock %}
```

### `static/css/avaliacao.css` (novo)

```css
/* Avaliação de fim de curso (página do aluno). */

.avaliacao {
  display: grid;
  gap: 22px;
  max-width: 720px;
  margin: 0 auto;
}

.avaliacao__topo h1 {
  margin-bottom: 4px;
}

.avaliacao__anonimo {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.avaliacao__pergunta {
  margin: 0;
  padding: 18px 0 0;
  border: 0;
  border-top: 1px solid var(--linha);
}

.avaliacao__pergunta legend {
  padding: 0;
  margin-bottom: 12px;
  font-weight: 700;
}

.avaliacao__pergunta--erro legend {
  color: var(--erro);
}

.avaliacao__opcoes {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.avaliacao__opcoes--nps {
  display: grid;
  grid-template-columns: repeat(11, minmax(0, 1fr));
  gap: 6px;
}

/* O rádio continua no lugar (teclado e leitor de tela), só fica invisível. */
.avaliacao__opcao {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: var(--alvo);
  min-height: var(--alvo);
  padding: 0 14px;
  border-radius: var(--raio-botao);
  background: var(--gelo);
  color: var(--tinta);
  font-weight: 600;
  cursor: pointer;
  transition: background var(--dur-rapida) var(--ease-padrao);
}

.avaliacao__opcao input {
  position: absolute;
  inset: 0;
  margin: 0;
  opacity: 0;
  cursor: pointer;
}

.avaliacao__opcao:hover {
  background: #e4deda;
}

.avaliacao__opcao:has(input:checked) {
  background: var(--marca);
  color: var(--branco);
}

.avaliacao__opcao:has(input:focus-visible) {
  outline: 3px solid var(--foco);
  outline-offset: 2px;
}

.avaliacao__opcoes--nps .avaliacao__opcao {
  min-width: 0;
  padding: 0;
}

.avaliacao__legenda {
  display: flex;
  justify-content: space-between;
  margin: 6px 0 0;
  color: var(--texto-3);
  font-size: var(--pequeno);
}

.avaliacao textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--linha);
  border-radius: var(--raio-botao);
  font: inherit;
}

@media (max-width: 560px) {
  /* 11 botões não cabem numa linha de celular: 0 a 5 em cima, 6 a 10 embaixo. */
  .avaliacao__opcoes--nps {
    grid-template-columns: repeat(6, minmax(0, 1fr));
  }
}
```

> [!tip] Rádio de verdade, com cara de botão
> As notas são `<input type="radio">` nativos, só invisíveis por cima do rótulo. Assim, setas do teclado, Tab e leitor de tela funcionam sem nenhuma linha de JS, e a página funciona até com o JS desligado.

---

## 9️⃣ Testes

Crie `avaliacao/tests/__init__.py` vazio.

### `avaliacao/tests/base.py`

```python
from io import StringIO

from django.core.management import call_command
from django.urls import reverse

from avaliacao.models import LinkDeAvaliacao, Pergunta
from catalogo.models import Curso
from quiz.tests.base import BaseEducMatch


class BaseAvaliacao(BaseEducMatch):
    """Catálogo real + as perguntas do seed_avaliacao."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command("seed_avaliacao", stdout=StringIO())

    def criar_link(self, curso=None, turma="2026/1 · Noite", **extra):
        return LinkDeAvaliacao.objects.create(curso=curso or Curso.objects.first(), turma=turma, **extra)

    def respostas_validas(self, nota=9, escala=4, escolha="Sim", texto=""):
        dados = {}
        for pergunta in Pergunta.objects.filter(ativa=True):
            chave = f"pergunta_{pergunta.id}"
            dados[chave] = {"nps": nota, "escala": escala, "escolha": escolha, "texto": texto}[pergunta.tipo]
        return dados

    def enviar(self, link, dados):
        return self.client.post(reverse("avaliacao-responder", args=[link.token]), dados)
```

### `avaliacao/tests/test_resposta.py`

```python
from io import StringIO

from django.core.management import call_command
from django.db import models
from django.urls import reverse

from avaliacao.models import ItemDeResposta, Pergunta, RespostaDeAvaliacao
from avaliacao.tests.base import BaseAvaliacao


class RespostaDoAlunoTest(BaseAvaliacao):
    """FRM-01: o aluno responde pelo link da turma, sem conta e sem se identificar."""

    def test_seed_cria_sete_perguntas_e_pode_rodar_de_novo(self):
        call_command("seed_avaliacao", stdout=StringIO())

        self.assertEqual(Pergunta.objects.count(), 7)

    def test_pagina_mostra_curso_e_turma(self):
        link = self.criar_link()

        resposta = self.client.get(reverse("avaliacao-responder", args=[link.token]))

        self.assertContains(resposta, link.curso.nome_curso)
        self.assertContains(resposta, "2026/1 · Noite")

    def test_resposta_completa_e_gravada(self):
        link = self.criar_link()

        resposta = self.enviar(link, self.respostas_validas(texto="Mais aulas práticas"))

        self.assertRedirects(resposta, reverse("avaliacao-obrigado", args=[link.token]))
        gravada = RespostaDeAvaliacao.objects.get()
        self.assertEqual(gravada.link, link)
        self.assertEqual(gravada.itens.count(), 7)
        self.assertEqual(gravada.itens.get(pergunta__tipo="nps").numero, 9)
        self.assertEqual(gravada.itens.get(pergunta__tipo="texto").texto, "Mais aulas práticas")

    def test_opcional_em_branco_nao_vira_item(self):
        link = self.criar_link()

        self.enviar(link, self.respostas_validas(texto=""))

        self.assertEqual(ItemDeResposta.objects.count(), 6)

    def test_falta_obrigatoria_nao_grava(self):
        link = self.criar_link()
        dados = self.respostas_validas()
        dados.pop(f"pergunta_{Pergunta.objects.get(ordem=1).id}")

        resposta = self.enviar(link, dados)

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Faltou responder")
        self.assertFalse(RespostaDeAvaliacao.objects.exists())

    def test_nota_fora_da_escala_e_recusada(self):
        link = self.criar_link()

        self.enviar(link, self.respostas_validas(nota=11))

        self.assertFalse(RespostaDeAvaliacao.objects.exists())

    def test_link_fechado_da_404(self):
        link = self.criar_link(ativo=False)

        resposta = self.client.get(reverse("avaliacao-responder", args=[link.token]))

        self.assertEqual(resposta.status_code, 404)

    def test_mesmo_navegador_nao_envia_duas_vezes(self):
        link = self.criar_link()
        self.enviar(link, self.respostas_validas())

        resposta = self.enviar(link, self.respostas_validas())

        self.assertRedirects(resposta, reverse("avaliacao-obrigado", args=[link.token]))
        self.assertEqual(RespostaDeAvaliacao.objects.count(), 1)

    def test_pergunta_inativa_some_do_formulario(self):
        link = self.criar_link()
        Pergunta.objects.filter(ordem=5).update(ativa=False)

        resposta = self.client.get(reverse("avaliacao-responder", args=[link.token]))

        self.assertNotContains(resposta, Pergunta.objects.get(ordem=5).texto)


class AnonimatoTest(BaseAvaliacao):
    def test_resposta_nao_tem_onde_guardar_quem_respondeu(self):
        for model in (RespostaDeAvaliacao, ItemDeResposta):
            with self.subTest(model=model.__name__):
                ligados_a_usuario = [
                    campo.name for campo in model._meta.get_fields()
                    if campo.is_relation and campo.related_model and campo.related_model._meta.label == "accounts.User"
                ]
                self.assertEqual(ligados_a_usuario, [])

    def test_resposta_guarda_o_dia_e_nao_a_hora(self):
        campo = RespostaDeAvaliacao._meta.get_field("respondido_em")

        self.assertIs(type(campo), models.DateField)
```

---

## ✅ Verificação

```bash
cd backend
python manage.py makemigrations --check --dry-run   # No changes detected (depois da 0001)
python manage.py migrate
python manage.py seed_avaliacao                      # 7 perguntas da avaliação
python manage.py test                                # 125 testes
python manage.py runserver
```

- [ ] No admin, crie um **Link de avaliação** para um curso e uma turma, e copie o token
- [ ] Abra `/avaliacao/<token>/` no **celular** (DevTools, 375px): curso e turma no topo, o aviso de anonimato, e a nota de 0 a 10 em duas linhas
- [ ] Envie sem responder nada: as obrigatórias ficam vermelhas e nada é gravado
- [ ] Responda tudo: cai na tela de agradecimento; abrir o link de novo no mesmo navegador volta para o agradecimento
- [ ] Feche o link no admin (`ativo` desmarcado): o endereço mostra "link encerrado" com status 404

## 📦 Commit e PR

```bash
git add -A
git commit -m "feat(avaliacao): avaliacao de fim de curso anonima por link de turma

- app avaliacao: Pergunta, LinkDeAvaliacao, RespostaDeAvaliacao, ItemDeResposta
- resposta sem usuario, sem hora e sem IP: anonima por construcao
- seed_avaliacao com 7 perguntas (proposta a revisar pela coordenacao)
- pagina do aluno sem login, com trava leve de envio repetido"
git push -u origin feature/avaliacao-fim-de-curso
gh pr create --base develop --fill
```

> [!success] Definition of Done
> 125 testes, CI verde, `seed_avaliacao` rodado no banco local e o checklist acima conferido. As perguntas do seed revisadas pela coordenação **antes da primeira turma real**, e não antes do merge.
