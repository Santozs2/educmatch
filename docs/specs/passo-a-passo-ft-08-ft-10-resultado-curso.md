---
title: "Passo a passo — FT-08 a FT-10 (resultado, detalhe do curso e secretaria) · Pessoa B"
aliases: ["Passo a passo FT resultado", "Front do resultado", "PR-F3", "Anel de afinidade", "Detalhe do curso"]
tags: [tcc, front, css, django, templates, acessibilidade, contrato, execucao, passo-a-passo]
status: proposto
projeto: TCC
criado: 2026-09-22
---

> [!info] Spec: [[Projetos/EducMatch(Secretária)/spec-front-templates|🎨 Spec do front]] · Plano: [[Projetos/EducMatch(Secretária)/plano-execucao-front-templates|🗂️ Plano]] · Base: [[Projetos/EducMatch(Secretária)/passo-a-passo-ft-01-fundacao|🧱 Fundação (D)]] · Contrato: [[contratos-c1-a-c6 🟢|📜 C6]] · Mockups: `Alta fidelidade 09` e `10`

# 🎯 Passo a passo — resultado e detalhe do curso (pessoa B)

> [!abstract] O que esta nota é
> O **como** das telas 09 (resultado) e 10 (detalhe do curso), mais o cartão da secretaria. Um PR, o **PR-F3**. É a frente que mais mexe com dado: a afinidade vem da `Recomendacao`, as barras vêm do JSON `explicacao.top_areas` (a migração do seu PR-2) e o detalhe precisa respeitar a regra de quem vê qual tentativa (C6).

> [!success] O que já foi verificado (2026-09-22)
> Aplicado numa cópia da `main` junto com as outras notas: as telas batem com os mockups 09 e 10 em 1440 px e 390 px; os dois testes novos do detalhe passam, inclusive o que prova que a tentativa de **outro navegador** não vira link nem afinidade.

## 🧭 O mapa

| Tarefa | Arquivos |
|---|---|
| **FT-08** resultado | `templates/quiz/resultado.html` · `static/css/resultado.css` |
| **FT-09** detalhe do curso | `catalogo/views.py` · `quiz/permissoes.py` (novo) · `catalogo/templates/catalogo/curso_detalhe.html` · `static/css/curso.css` (novo) |
| **FT-10** secretaria | `core/contexto.py` (novo) · `core/settings.py` · `templates/componentes/_secretaria.html` (novo) |
| testes | `quiz/tests/test_telas.py` |

---

## 🚦 Antes de abrir o editor

```bash
git switch main && git pull          # já com o PR-F1 da pessoa D
git switch -c front/resultado-curso
```

Para ter um resultado para olhar: responda o quiz em `http://localhost:8000/` e anote o número em `/resultado/<id>/`.

---

## 1️⃣ FT-08 — o resultado

### `backend/templates/quiz/resultado.html` (substitua)

```django
{% extends "base.html" %}
{% load static %}

{% block title %}Seu resultado{% endblock %}

{% block estilos %}<link rel="stylesheet" href="{% static 'css/resultado.css' %}">{% endblock %}

{% block content %}
<section class="resultado">
    <h1>
        {% if tentativa.respondido_por %}{{ tentativa.respondido_por }}, esses{% else %}Esses{% endif %}
        são os cursos que mais combinam com você
    </h1>

    {% if tentativa.questionario_link_id %}
    <p class="aviso" role="note">Você respondeu pelo link da escola.</p>
    {% endif %}

    {% if tentativa.confidence_band == "baixa" %}
    <p class="aviso" role="note">
        Sua afinidade com os cursos disponíveis ficou baixa. Vale refazer o teste
        com calma ou conversar com a secretaria antes de decidir.
    </p>
    {% endif %}

    {% if curso_pendente %}
    <form class="aviso resultado__pendente" method="post" action="{% url 'interesse-salvar' %}">
        {% csrf_token %}
        <p>Você queria salvar <strong>{{ curso_pendente.nome_curso }}</strong>.</p>
        <input type="hidden" name="curso_id" value="{{ curso_pendente.id }}">
        <input type="hidden" name="tentativa_id" value="{{ tentativa.pk }}">
        <button class="botao" type="submit">Salvar agora</button>
    </form>
    {% endif %}

    {% if destaque %}
    {# Tela 09 · o 1º lugar em destaque #}
    <article class="destaque" aria-labelledby="destaque-nome">
        <div class="destaque__faixa">
            <span class="chip"><i class="fa-solid fa-check" aria-hidden="true"></i> Melhor combinação</span>
        </div>

        <div class="destaque__corpo">
            <div class="destaque__afinidade">
                {% include "componentes/_anel.html" with valor=destaque.match %}
                <span class="destaque__legenda">de afinidade</span>
            </div>

            <div class="destaque__info">
                <h2 id="destaque-nome">{{ destaque.curso.nome_curso }}</h2>
                <p class="subtitulo">{{ destaque.curso.descricao|truncatewords:30 }}</p>

                <ul class="chips">
                    <li class="chip chip--area">{{ destaque.curso.area_principal.nome }}</li>
                    <li class="chip"><i class="fa-regular fa-clock" aria-hidden="true"></i> {{ destaque.curso.duracao }} horas</li>
                </ul>

                {% if destaque.areas %}
                <div class="porque">
                    <h3>Por que este curso?</h3>
                    {% for area in destaque.areas %}
                    <div class="porque__linha">
                        <span>{{ area.area_name }}</span>
                        <span>{{ area.percentual|floatformat:0 }}%</span>
                        {% include "componentes/_barra.html" with valor=area.percentual %}
                    </div>
                    {% endfor %}
                </div>
                {% endif %}

                <a class="botao botao--bloco" href="{% url 'curso-detalhe' destaque.curso.id %}?tentativa={{ tentativa.pk }}">
                    Ver detalhes do curso
                </a>
            </div>
        </div>
    </article>

    {% if outros %}
    <h2 class="resultado__subtitulo">Também combinam com você</h2>
    <ol class="outros">
        {% for item in outros %}
        <li class="outro">
            <span class="outro__rank" aria-hidden="true">{{ item.rank }}</span>
            <div class="outro__info">
                {# O link cobre a linha inteira (ver .outro__link::after no CSS) #}
                <a class="outro__link" href="{% url 'curso-detalhe' item.curso.id %}?tentativa={{ tentativa.pk }}">
                    {{ item.curso.nome_curso }}
                </a>
                <p class="outro__descricao">{{ item.curso.descricao }}</p>
            </div>
            <span class="chip chip--area outro__area">{{ item.curso.area_principal.nome }}</span>
            <div class="outro__afinidade">
                <strong>{{ item.match }}%</strong>
                {% include "componentes/_barra.html" with valor=item.match escura=True %}
            </div>
            <i class="fa-solid fa-arrow-right outro__seta" aria-hidden="true"></i>
        </li>
        {% endfor %}
    </ol>
    {% endif %}

    {% else %}
    <p class="vazio">Não encontramos recomendações para esta tentativa.</p>
    {% endif %}

    <div class="resultado__acoes">
        <a class="botao botao--contorno" href="{% url 'quiz-inicio' %}">Refazer o teste</a>
        {# Só com JS: sem ele, o Ctrl+P do navegador faz o mesmo #}
        <button class="botao botao--texto" type="button" data-imprimir hidden>
            <i class="fa-solid fa-download" aria-hidden="true"></i> Salvar resultado em PDF
        </button>
    </div>
</section>
{% endblock %}

{% block scripts %}
<script>
    // "Salvar em PDF" = imprimir; o navegador oferece "Salvar como PDF".
    document.querySelectorAll("[data-imprimir]").forEach(function (botao) {
        botao.hidden = false;
        botao.addEventListener("click", function () { window.print(); });
    });
</script>
{% endblock %}
```

> [!note] A linha inteira clica, mas só o nome do curso é link
> Na lista "Também combinam", o link está só no nome, e um `::after` do CSS o estica por cima da linha inteira. Para quem clica, a linha toda funciona. Para o leitor de tela e para o Tab, é **um** link por curso, com o nome do curso como texto. Se a linha inteira fosse um `<a>`, o leitor leria nome, descrição, área e porcentagem de uma vez só.

> [!note] O botão "Salvar resultado em PDF" nasce escondido
> Ele tem `hidden` no HTML e o script tira. Sem JS, o botão não aparece, em vez de aparecer e não funcionar. O `Ctrl+P` do navegador continua imprimindo a página limpa (ver o `@media print`).

### `backend/static/css/resultado.css` (arquivo novo)

```css
/* Resultado (tela 09). Coluna central, como no protótipo. */

.resultado {
  display: grid;
  grid-template-columns: minmax(0, 1fr); /* sem isto, texto com nowrap alarga a página */
  gap: 20px;
  max-width: 760px;
  margin: 0 auto;
}

.resultado h1 {
  margin: 0;
  font-size: var(--h2);
}

.resultado__pendente {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.resultado__pendente p {
  margin: 0;
}

/* ---------- O 1º lugar ---------- */

.destaque {
  overflow: hidden;
  border: 2px solid var(--preto);
  border-radius: var(--raio);
  background: var(--superficie);
  box-shadow: var(--sombra);
}

.destaque__faixa {
  display: flex;
  justify-content: center;
  padding: 8px;
  background: var(--preto);
}

.destaque__faixa .chip {
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-size: 0.75rem;
}

.destaque__faixa .fa-check {
  color: var(--marca);
}

.destaque__corpo {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 28px;
  padding: 28px;
}

.destaque__afinidade {
  display: grid;
  justify-items: center;
  align-content: start;
  gap: 10px;
}

.destaque__legenda {
  color: var(--texto-3);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.destaque__info h2 {
  margin-bottom: 6px;
}

/* ---------- Por que este curso ---------- */

.porque {
  margin-bottom: 20px;
  padding: 16px;
  border: 1px solid var(--linha);
  border-radius: var(--raio-botao);
}

.porque h3 {
  margin-bottom: 12px;
}

.porque__linha {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 4px 12px;
  margin-bottom: 12px;
  font-size: var(--pequeno);
  font-weight: 600;
}

.porque__linha span:nth-child(2) {
  color: var(--marca);
}

.porque__linha .barra {
  grid-column: 1 / -1;
}

/* ---------- Também combinam ---------- */

.resultado__subtitulo {
  margin: 12px 0 0;
  font-size: 1.1rem;
}

.outros {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.outro {
  position: relative;
  display: grid;
  grid-template-columns: auto 1fr auto 90px auto;
  align-items: center;
  gap: 16px;
  padding: 16px 18px;
  border: 1px solid var(--linha);
  border-radius: var(--raio);
  background: var(--superficie);
  transition: border-color 0.15s;
}

.outro:hover {
  border-color: var(--marca);
}

.outro__rank {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--marca-claro);
  color: var(--marca);
  font-weight: 700;
}

.outro__info {
  min-width: 0;
}

.outro__link {
  font-weight: 700;
  text-decoration: none;
}

/* A linha inteira clica, mas só o nome do curso é o link (leitor de tela lê uma vez) */
.outro__link::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: var(--raio);
}

.outro__link:focus-visible {
  outline: none;
}

.outro:has(.outro__link:focus-visible) {
  outline: 3px solid var(--foco);
  outline-offset: 3px;
}

.outro__descricao {
  margin: 2px 0 0;
  overflow: hidden;
  color: var(--texto-2);
  font-size: var(--pequeno);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.outro__afinidade {
  display: grid;
  gap: 4px;
  text-align: right;
}

.outro__seta {
  color: var(--marca);
}

.resultado__acoes {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 12px;
}

/* ---------- Celular ---------- */

@media (max-width: 640px) {
  .destaque__corpo {
    grid-template-columns: 1fr;
    justify-items: center;
    padding: 20px;
  }

  .destaque__info {
    width: 100%;
  }

  .outro {
    grid-template-columns: auto 1fr auto;
  }

  .outro__area,
  .outro__seta {
    display: none;
  }
}

/* ---------- "Salvar em PDF": o que sai no papel ---------- */

@media print {
  .topo,
  .rodape,
  .resultado__acoes,
  .outro__seta {
    display: none !important;
  }

  body,
  .conteudo {
    background: var(--superficie);
  }

  .destaque,
  .outro {
    box-shadow: none;
    break-inside: avoid;
  }
}
```

> [!danger] O `minmax(0, 1fr)` na coluna do grid
> Por padrão, uma coluna de grid fica do tamanho do **maior texto que não quebra**. A descrição dos cursos tem `white-space: nowrap` (para cortar com "…"), e sem o `minmax(0, 1fr)` ela alargava a página inteira no celular. Vale para todo `display: grid` que tenha texto com `nowrap` dentro.

---

## 2️⃣ FT-09 — o detalhe do curso

### `backend/quiz/permissoes.py` (arquivo novo)

A regra de "quem vê qual tentativa" (C6) já existia dentro da view do resultado. O detalhe precisa da mesma regra, então ela ganha uma função própria:

```python
from quiz.models import Tentativa_de_resposta


def tentativa_visivel(request, pk):
    """A tentativa `pk`, se esta pessoa pode vê-la; senão None.

    Mesma regra do resultado (contrato C6): tentativa com dono só para o dono;
    tentativa anônima só no navegador que a respondeu (está na sessão).
    """
    tentativa = Tentativa_de_resposta.objects.filter(pk=pk).first()
    if tentativa is None:
        return None
    if tentativa.user_id is not None:
        return tentativa if tentativa.user_id == request.user.id else None
    return tentativa if tentativa.pk in request.session.get("minhas_tentativas", []) else None
```

> [!danger] Por que o detalhe precisa dessa regra
> O `?tentativa=` vem da URL, e qualquer um pode escrever `?tentativa=7`. Sem a regra, o detalhe mostraria a **afinidade de outra pessoa** com o curso e um link "Voltar para o meu resultado" apontando para o resultado dela. O teste `test_detalhe_nao_mostra_tentativa_de_outro_navegador` prova que isso não acontece.

### `backend/catalogo/views.py` (substitua)

```python
from django.shortcuts import get_object_or_404, render

from accounts.models import Interesse
from catalogo.models import Curso
from quiz.permissoes import tentativa_visivel


def curso_detalhe(request, pk):
    curso = get_object_or_404(
        Curso.objects.select_related("area_principal"), pk=pk, is_active=True
    )

    # De onde a pessoa veio: permite "voltar para o meu resultado", mostrar a
    # afinidade dela com este curso e salvar o interesse com o snapshot certo.
    tentativa_id = request.GET.get("tentativa", "")
    tentativa = tentativa_visivel(request, int(tentativa_id)) if tentativa_id.isdigit() else None

    afinidade = None
    if tentativa:
        rec = tentativa.recomendacoes.filter(curso=curso).first()
        afinidade = round(rec.score * 100) if rec else None

    salvo = (
        request.user.is_authenticated
        and Interesse.objects.filter(usuario=request.user, curso=curso).exists()
    )
    return render(request, "catalogo/curso_detalhe.html", {
        "curso": curso,
        "tentativa_id": tentativa.pk if tentativa else "",
        "afinidade": afinidade,
        "salvo": salvo,
    })
```

### `backend/catalogo/templates/catalogo/curso_detalhe.html` (substitua)

```django
{% extends "base.html" %}
{% load static %}

{% block title %}{{ curso.nome_curso }}{% endblock %}

{% block estilos %}<link rel="stylesheet" href="{% static 'css/curso.css' %}">{% endblock %}

{# Tela 10 · o topo vira só o "Voltar", como no protótipo #}
{% block topo %}
<header class="topo">
    <div class="topo__inner curso-topo">
        {% if tentativa_id %}
        <a class="voltar" href="{% url 'quiz-resultado' tentativa_id %}">Voltar para o meu resultado</a>
        {% else %}
        <a class="voltar" href="{% url 'quiz-inicio' %}">Voltar</a>
        {% endif %}
    </div>
</header>
{% endblock %}

{% block content %}
<div class="curso">
    <article class="curso__cartao" aria-labelledby="curso-nome">
        <header class="curso__cabeca">
            <ul class="chips">
                <li class="chip chip--marca">{{ curso.area_principal.nome }}</li>
                <li class="chip chip--escuro">{{ curso.duracao }} horas</li>
                {% if curso.inicio_dia %}<li class="chip chip--escuro">Início em {{ curso.inicio_dia|date:"d/m/Y" }}</li>{% endif %}
            </ul>
            <h1 id="curso-nome">{{ curso.nome_curso }}</h1>
            <p>{{ curso.descricao|linebreaksbr }}</p>
        </header>

        <div class="curso__corpo">
            {% if afinidade is not None %}
            <div class="curso__afinidade">
                <div>
                    <strong>Sua afinidade</strong>
                    <span>Baseado nas suas respostas</span>
                </div>
                <span class="curso__afinidade-valor">{{ afinidade }}%</span>
            </div>
            {% endif %}

            <form method="post" action="{% url 'interesse-salvar' %}">
                {% csrf_token %}
                <input type="hidden" name="curso_id" value="{{ curso.id }}">
                {% if tentativa_id %}<input type="hidden" name="tentativa_id" value="{{ tentativa_id }}">{% endif %}
                {% if salvo %}
                <button class="botao botao--contorno botao--bloco" type="submit">Remover da minha lista</button>
                {% else %}
                <button class="botao botao--bloco" type="submit">Manifestar interesse neste curso</button>
                {% endif %}
            </form>
        </div>
    </article>

    {% include "componentes/_secretaria.html" %}
</div>
{% endblock %}
```

> [!warning] "O que você vai aprender" ficou de fora, de propósito
> O mockup 10 tem uma lista de quatro itens, mas o `Curso` não tem esse campo, e os itens do mockup são iguais para todo curso. Mostrar o mesmo texto em todo curso seria informação inventada. A seção volta quando o catálogo (frente F3) tiver o conteúdo (ver V2 na spec).

### `backend/static/css/curso.css` (arquivo novo)

```css
/* Detalhe do curso (tela 10). */

.curso-topo {
  max-width: 800px;
}

.curso {
  display: grid;
  grid-template-columns: minmax(0, 1fr); /* sem isto, texto com nowrap alarga a página */
  gap: 24px;
  max-width: 740px;
  margin: 0 auto;
}

.curso__cartao {
  overflow: hidden;
  border: 1px solid var(--linha);
  border-radius: var(--raio);
  background: var(--superficie);
  box-shadow: var(--sombra);
}

.curso__cabeca {
  padding: 28px;
  background: var(--preto);
  color: var(--branco);
}

.curso__cabeca h1 {
  color: var(--branco);
  font-size: var(--h2);
}

.curso__cabeca p {
  margin: 0;
  color: var(--gelo);
}

.curso__cabeca .chip--escuro {
  border-color: var(--preto-2);
  background: var(--preto-2);
}

.curso__corpo {
  display: grid;
  gap: 20px;
  padding: 28px;
}

.curso__afinidade {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 20px;
  border: 1px solid var(--marca-claro);
  border-radius: var(--raio-botao);
  background: var(--marca-clarinho);
  color: var(--titulo);
}

.curso__afinidade strong,
.curso__afinidade span {
  display: block;
}

.curso__afinidade span {
  font-size: var(--pequeno);
}

.curso__afinidade-valor {
  font-size: 1.6rem !important;
  font-weight: 700;
}

/* ---------- Secretaria ---------- */

.secretaria h2 {
  font-size: 1.1rem;
}

.secretaria__dados {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin: 0;
}

.secretaria__dados dt {
  font-weight: 700;
}

.secretaria__dados dt i {
  color: var(--marca);
}

.secretaria__dados dd {
  margin: 4px 0 0;
  color: var(--texto-2);
  font-size: var(--pequeno);
}
```

---

## 3️⃣ FT-10 — o cartão da secretaria

### `backend/core/contexto.py` (arquivo novo)

```python
from django.conf import settings


def escola(request):
    """Os dados da escola em todo template: {{ escola.nome }}, {{ escola.telefone }}..."""
    return {"escola": settings.ESCOLA}
```

### `backend/core/settings.py` — dois acréscimos

Na lista `context_processors` do `TEMPLATES`, depois do `messages`:

```python
                'django.contrib.messages.context_processors.messages',
                'core.contexto.escola',
```

E no fim do arquivo:

```python
# Contato da secretaria (detalhe do curso). Endereço e telefone vêm do .env:
# sem eles, o cartão mostra só o nome da escola.
ESCOLA = {
    "nome": os.environ.get("ESCOLA_NOME", "SENAI São José do Rio Preto · CFP 8.01 Antonio Devisate"),
    "endereco": os.environ.get("ESCOLA_ENDERECO", ""),
    "telefone": os.environ.get("ESCOLA_TELEFONE", ""),
}
```

E no `backend/.env.example`, para todo mundo saber que existem:

```bash
ESCOLA_NOME=SENAI São José do Rio Preto · CFP 8.01 Antonio Devisate
ESCOLA_ENDERECO=
ESCOLA_TELEFONE=
```

> [!warning] Não copie o endereço e o telefone do mockup
> "Rua da Escola Técnica, 1000" e "(11) 99999-0000" são de exemplo. Um telefone falso na tela de um sistema de matrícula é pior do que nenhum. Peça os dados verdadeiros à secretaria e coloque no `.env` de quem vai apresentar.

### `backend/templates/componentes/_secretaria.html` (arquivo novo)

```django
{# Cartão "Falar com a secretaria". Os dados vêm do settings (ESCOLA), via core.contexto.escola. #}
<section class="cartao secretaria" aria-labelledby="secretaria-titulo">
    <h2 id="secretaria-titulo">Falar com a secretaria da escola</h2>
    <p class="subtitulo">As matrículas estão abertas. Entre em contato para saber sobre turmas e horários.</p>

    <dl class="secretaria__dados">
        <div>
            <dt><i class="fa-solid fa-location-dot" aria-hidden="true"></i> Escola</dt>
            <dd>{{ escola.nome }}{% if escola.endereco %}<br>{{ escola.endereco }}{% endif %}</dd>
        </div>
        {% if escola.telefone %}
        <div>
            <dt><i class="fa-solid fa-phone" aria-hidden="true"></i> Telefone / WhatsApp</dt>
            <dd><a href="tel:{{ escola.telefone|cut:' '|cut:'('|cut:')'|cut:'-' }}">{{ escola.telefone }}</a></dd>
        </div>
        {% endif %}
    </dl>
</section>
```

---

## 4️⃣ Os testes — `backend/quiz/tests/test_telas.py`

Duas mudanças.

**O texto do aviso ganhou acento.** Em `test_aviso_de_baixa_confianca_aparece`:

```python
        self.assertContains(resposta, "afinidade com os cursos disponíveis ficou baixa")
```

**O teste do detalhe muda, e ganha um irmão.** O antigo aceitava `?tentativa=7` de qualquer um. Substitua `test_detalhe_do_curso_mostra_o_curso_e_volta_ao_resultado` por estes dois:

```python
    def test_detalhe_do_curso_mostra_a_afinidade_e_volta_ao_resultado(self):
        tentativa = self.responder()
        rec = tentativa.recomendacoes.get(rank=1)

        resposta = self.client.get(reverse("curso-detalhe", args=[rec.curso_id]) + f"?tentativa={tentativa.pk}")

        self.assertContains(resposta, rec.curso.nome_curso)
        self.assertContains(resposta, reverse("quiz-resultado", args=[tentativa.pk]))
        self.assertEqual(resposta.context["afinidade"], round(rec.score * 100))

    def test_detalhe_nao_mostra_tentativa_de_outro_navegador(self):
        """C6 no detalhe: ?tentativa= de outra pessoa não vira link nem afinidade."""
        outro = self.client_class(SERVER_NAME="localhost")
        outro.post("/", self.payload_do_quiz())
        alheia = Tentativa_de_resposta.objects.latest("id")
        curso = alheia.recomendacoes.get(rank=1).curso

        resposta = self.client.get(reverse("curso-detalhe", args=[curso.pk]) + f"?tentativa={alheia.pk}")

        self.assertIsNone(resposta.context["afinidade"])
        self.assertNotContains(resposta, reverse("quiz-resultado", args=[alheia.pk]))
```

---

## 5️⃣ Verificação

```bash
python manage.py test quiz.tests.test_telas quiz.tests.test_paginas -v 2
python manage.py test 2>&1 | tail -3
```

| # | O quê | Sinal de que passou |
|---|---|---|
| 1 | `/resultado/<id>/` em 1440 px | Igual ao mockup 09: faixa preta "✓ Melhor combinação", anel, chips, "Por que este curso?", botão vermelho |
| 2 | O mesmo em 390 px | O anel sobe para cima do nome; sem rolagem lateral |
| 3 | "Ver detalhes do curso" | Mockup 10: topo só com "‹ Voltar para o meu resultado", "Sua afinidade 87%" |
| 4 | O mesmo detalhe numa **janela anônima** | Sem "Sua afinidade" e com "‹ Voltar" genérico |
| 5 | "Manifestar interesse" deslogado | Vai para o login; depois de entrar, o resultado mostra "Você queria salvar… Salvar agora" |
| 6 | "Salvar resultado em PDF" | Abre a impressão; a prévia **não** tem o topo nem os botões |
| 7 | Tab pela lista "Também combinam" | Uma parada por curso, com o contorno na linha inteira |

## 6️⃣ Commit e PR

```bash
git add -A
git status --short
git commit -m "feat(front): resultado e detalhe do curso nas telas 09 e 10 (FT-08 a FT-10)"
git push -u origin front/resultado-curso
```

No PR: prints das telas 09 e 10 ao lado dos mockups, e o resultado do item 4.

## ▶️ Próxima ação

Criar a branch `front/resultado-curso` e começar pelo `resultado.html`.

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/spec-front-templates|🎨 Spec do front]] — V2, V3, V4 e V5
- [[contratos-c1-a-c6 🟢|📜 C6]] — a regra de quem vê qual tentativa
