---
title: "Passo a passo — FT-11 a FT-14 (entrar, criar conta, lista, testes, perfil, link e painel) · Pessoa C"
aliases: ["Passo a passo FT conta", "Front da conta", "PR-F4", "Telas da conta", "Painel nos tokens"]
tags: [tcc, front, css, django, templates, acessibilidade, execucao, passo-a-passo]
status: proposto
projeto: TCC
criado: 2026-09-22
---

> [!info] Spec: [[Projetos/EducMatch(Secretária)/spec-front-templates|🎨 Spec do front]] · Plano: [[Projetos/EducMatch(Secretária)/plano-execucao-front-templates|🗂️ Plano]] · Base: [[Projetos/EducMatch(Secretária)/passo-a-passo-ft-01-fundacao|🧱 Fundação (D)]] · Mockups: `Alta fidelidade 11` e `12`

# 👤 Passo a passo — conta e painel (pessoa C)

> [!abstract] O que esta nota é
> O **como** de todas as telas de quem tem conta (entrar, criar conta, minha lista, meus testes, perfil), da página de link encerrado e do ajuste do painel às cores novas. Um PR, o **PR-F4**. São muitas telas, mas todas usam as mesmas peças: o cartão central, o `_campo.html` e a "linha" de lista.

> [!success] O que já foi verificado (2026-09-22)
> Aplicado numa cópia da `main` junto com as outras notas: entrar e minha lista batem com os mockups 11 e 12; todas as telas abrem no `test_paginas.py`; nenhuma rola para o lado em 390 px, inclusive o painel.

## 🧭 O mapa

| Tarefa | Arquivos |
|---|---|
| **FT-11** entrar e criar conta | `templates/componentes/_campo.html` (novo) · `accounts/templates/accounts/entrar.html` · `criar_conta.html` · `static/css/conta.css` (novo) |
| **FT-12** lista, testes e perfil | `accounts/templates/accounts/lista.html` · `tentativas.html` · `templates/quiz/aluno_perfil.html` |
| **FT-13** link encerrado | `templates/quiz/link_invalido.html` |
| **FT-14** painel nos tokens | `static/css/painel.css` · `painel/templates/painel/dashboard.html` |

---

## 🚦 Antes de abrir o editor

```bash
git switch main && git pull          # já com o PR-F1 da pessoa D
git switch -c front/conta-painel
```

---

## 1️⃣ FT-11 — entrar e criar conta

### `backend/templates/componentes/_campo.html` (arquivo novo)

Um campo de formulário do Django, sempre do mesmo jeito: rótulo, "(opcional)" quando for o caso, ajuda e erro.

```django
{# Um campo de formulário no padrão do projeto. Uso: {% include "componentes/_campo.html" with campo=form.email %} #}
<div class="campo{% if campo.errors %} campo--com-erro{% endif %}">
    <label for="{{ campo.id_for_label }}">
        {{ campo.label }}
        {% if not campo.field.required %}<span class="campo__opcional">(opcional)</span>{% endif %}
    </label>
    {{ campo }}
    {% if campo.help_text %}<p class="campo__ajuda" id="{{ campo.id_for_label }}-ajuda">{{ campo.help_text|safe }}</p>{% endif %}
    {% for erro in campo.errors %}<p class="campo__erro" role="alert">{{ erro }}</p>{% endfor %}
</div>
```

> [!danger] O comentário da primeira linha **tem** de ficar numa linha só
> `{# ... #}` só funciona numa linha. Na verificação, este mesmo comentário escrito em duas linhas fez o Django executar o `{% include %}` do exemplo, e o template incluiu a si mesmo até dar `RecursionError` na tela de login.

### `backend/accounts/templates/accounts/entrar.html` (substitua)

```django
{% extends "base.html" %}
{% load static %}

{% block title %}Entrar{% endblock %}

{% block estilos %}<link rel="stylesheet" href="{% static 'css/conta.css' %}">{% endblock %}

{% block topo %}{% url 'quiz-inicio' as inicio %}{% include "componentes/_topo_voltar.html" with destino=next|default:inicio %}{% endblock %}

{# Tela 11 #}
{% block content %}
<section class="cartao cartao--centro cartao--estreito conta">
    <h1>Entre na sua conta</h1>
    <p class="subtitulo">Para salvar seu interesse, precisamos saber quem é você.</p>

    {% for erro in form.non_field_errors %}
    <p class="aviso" role="alert">{{ erro }}</p>
    {% endfor %}

    <form method="post" novalidate>
        {% csrf_token %}
        {% if next %}<input type="hidden" name="next" value="{{ next }}">{% endif %}

        {% include "componentes/_campo.html" with campo=form.username %}
        {% include "componentes/_campo.html" with campo=form.password %}

        <button class="botao botao--bloco" type="submit">Entrar</button>
    </form>

    <p class="conta__troca">
        Ainda não tem conta?
        <a href="{% url 'cadastro_usuario' %}{% if next %}?next={{ next|urlencode }}{% endif %}">Criar conta</a>
    </p>
</section>
{% endblock %}
```

> [!note] "E-mail", e não "E-mail ou CPF"
> O mockup 11 diz "E-mail ou CPF", mas o sistema entra por e-mail e não guarda CPF (ver V1 na spec).

> [!note] O "Voltar" do topo leva para onde a pessoa estava
> O `LoginView` do Django passa o `next` para o template. Quem veio de "Manifestar interesse" volta para o resultado; quem abriu `/entrar/` direto volta para o início.

### `backend/accounts/templates/accounts/criar_conta.html` (substitua)

```django
{% extends "base.html" %}
{% load static %}

{% block title %}Criar conta{% endblock %}

{% block estilos %}<link rel="stylesheet" href="{% static 'css/conta.css' %}">{% endblock %}

{% block topo %}{% url 'entrar' as entrar %}{% include "componentes/_topo_voltar.html" with destino=entrar %}{% endblock %}

{% block content %}
<section class="cartao cartao--centro cartao--estreito conta">
    <h1>Criar conta</h1>
    <p class="subtitulo">Salve os cursos que combinam com você e veja seus testes anteriores.</p>

    <form method="post" novalidate>
        {% csrf_token %}
        {% if request.GET.next %}<input type="hidden" name="next" value="{{ request.GET.next }}">{% endif %}

        {% for campo in form %}
        {% include "componentes/_campo.html" %}
        {% endfor %}

        <button class="botao botao--bloco" type="submit">Criar conta</button>
    </form>

    <p class="conta__troca">
        Já tem conta?
        <a href="{% url 'entrar' %}{% if request.GET.next %}?next={{ request.GET.next|urlencode }}{% endif %}">Entrar</a>
    </p>
</section>
{% endblock %}
```

### `backend/static/css/conta.css` (arquivo novo)

```css
/* Telas da conta: entrar (11), criar conta, minha lista (12), meus testes e perfil. */

/* ---------- Entrar e criar conta ---------- */

.conta {
  margin-top: clamp(0px, 6vh, 64px);
}

.conta h1 {
  font-size: var(--h2);
}

.conta form {
  margin-top: 24px;
}

.conta__troca {
  margin: 20px 0 0;
  color: var(--texto-2);
  text-align: center;
}

.conta__troca a {
  color: var(--marca);
  font-weight: 700;
}

/* ---------- Páginas de lista (lista, testes, perfil) ---------- */

.pagina-conta {
  display: grid;
  grid-template-columns: minmax(0, 1fr); /* sem isto, texto com nowrap alarga a página */
  gap: 20px;
  max-width: 740px;
  margin: 0 auto;
}

.pagina-conta__titulo {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 24px;
}

.pagina-conta__titulo h1 {
  margin: 0;
  font-size: var(--h2);
}

.linhas {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.linha {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 16px;
  padding: 18px 20px;
  border: 1px solid var(--linha);
  border-radius: var(--raio);
  background: var(--superficie);
}

.linha__info {
  flex: 1 1 260px;
  min-width: 0;
}

.linha__titulo {
  font-size: 1.05rem;
  font-weight: 700;
  text-decoration: none;
}

.linha__titulo:hover {
  color: var(--marca);
}

.linha__descricao {
  margin: 2px 0 0;
  overflow: hidden;
  color: var(--texto-2);
  font-size: var(--pequeno);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.linha__chips {
  margin: 0;
}

/* ---------- Perfil ---------- */

.perfil__numeros {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.perfil__numero {
  padding: 20px;
  text-decoration: none;
}

.perfil__numero strong {
  display: block;
  color: var(--marca);
  font-size: 2rem;
  line-height: 1.1;
}

.perfil__numero:hover {
  border-color: var(--marca);
}
```

---

## 2️⃣ FT-12 — minha lista, meus testes e perfil

### `backend/accounts/templates/accounts/lista.html` (substitua)

```django
{% extends "base.html" %}
{% load static %}

{% block title %}Minha lista{% endblock %}

{% block estilos %}<link rel="stylesheet" href="{% static 'css/conta.css' %}">{% endblock %}

{# Tela 12 #}
{% block content %}
<section class="pagina-conta">
    <div class="pagina-conta__titulo">
        {% if ultima_tentativa %}
        <a class="voltar" href="{% url 'quiz-resultado' ultima_tentativa.pk %}">Voltar</a>
        {% else %}
        <a class="voltar" href="{% url 'quiz-inicio' %}">Voltar</a>
        {% endif %}
        <h1>Minha Lista de Interesse</h1>
    </div>

    {% if interesses %}
    <ul class="linhas">
        {% for item in interesses %}
        <li class="linha">
            <div class="linha__info">
                <a class="linha__titulo" href="{% url 'curso-detalhe' item.curso.id %}">{{ item.curso.nome_curso }}</a>
                <p class="linha__descricao">{{ item.curso.descricao }}</p>
            </div>
            <ul class="chips linha__chips">
                <li class="chip chip--area">{{ item.curso.area_principal.nome }}</li>
                <li class="chip">{{ item.curso.duracao }} horas</li>
            </ul>
            <form method="post" action="{% url 'remover_interesse' item.pk %}">
                {% csrf_token %}
                <button class="botao botao--texto" type="submit">
                    Remover<span class="visualmente-oculto"> {{ item.curso.nome_curso }}</span>
                </button>
            </form>
        </li>
        {% endfor %}
    </ul>
    {% else %}
    <div class="vazio">
        <p>Você ainda não salvou nenhum curso.</p>
        <a class="botao" href="{% url 'quiz-inicio' %}">Fazer o teste</a>
    </div>
    {% endif %}
</section>
{% endblock %}
```

> [!note] "Remover" com nome para o leitor de tela
> Numa lista com cinco cursos, cinco botões "Remover" iguais não dizem nada para quem usa leitor de tela. O `<span class="visualmente-oculto">` faz ele ouvir "Remover Costura Industrial".

### `backend/accounts/templates/accounts/tentativas.html` (substitua)

```django
{% extends "base.html" %}
{% load static %}

{% block title %}Meus testes{% endblock %}

{% block estilos %}<link rel="stylesheet" href="{% static 'css/conta.css' %}">{% endblock %}

{% block content %}
<section class="pagina-conta">
    <div class="pagina-conta__titulo">
        <a class="voltar" href="{% url 'quiz-inicio' %}">Voltar</a>
        <h1>Meus testes</h1>
    </div>

    {% if tentativas %}
    <ul class="linhas">
        {% for tentativa in tentativas %}
        {% with principal=tentativa.recomendacoes.all.0 %}
        <li class="linha">
            <div class="linha__info">
                <a class="linha__titulo" href="{% url 'quiz-resultado' tentativa.pk %}">
                    Teste de {{ tentativa.criado_em|date:"d/m/Y" }} às {{ tentativa.criado_em|date:"H:i" }}
                </a>
                {% if principal %}
                <p class="linha__descricao">1º lugar: <strong>{{ principal.curso.nome_curso }}</strong></p>
                {% endif %}
            </div>
            {% if principal %}
            <span class="chip chip--area">{% widthratio principal.score 1 100 %}% de afinidade</span>
            {% endif %}
        </li>
        {% endwith %}
        {% endfor %}
    </ul>
    {% else %}
    <div class="vazio">
        <p>Você ainda não fez o teste com a conta logada.</p>
        <a class="botao" href="{% url 'quiz-inicio' %}">Fazer o teste</a>
    </div>
    {% endif %}
</section>
{% endblock %}
```

### `backend/templates/quiz/aluno_perfil.html` (substitua)

```django
{% extends "base.html" %}
{% load static %}

{% block title %}Meu perfil{% endblock %}

{% block estilos %}<link rel="stylesheet" href="{% static 'css/conta.css' %}">{% endblock %}

{% block content %}
<section class="pagina-conta">
    <div class="pagina-conta__titulo">
        <a class="voltar" href="{% url 'quiz-inicio' %}">Voltar</a>
        <h1>{{ user.first_name|default:user.email }}</h1>
    </div>

    {# Só números que o sistema mede de verdade #}
    <div class="perfil__numeros">
        <a class="cartao perfil__numero" href="{% url 'minhas-tentativas' %}">
            <strong>{{ total_de_testes }}</strong>
            {{ total_de_testes|pluralize:"teste feito,testes feitos" }}
        </a>
        <a class="cartao perfil__numero" href="{% url 'lista_interesse' %}">
            <strong>{{ total_na_lista }}</strong>
            {{ total_na_lista|pluralize:"curso na lista,cursos na lista" }}
        </a>
    </div>

    <h2>Histórico de resultados</h2>
    {% if historico %}
    <ul class="linhas">
        {% for item in historico %}
        <li class="linha">
            <div class="linha__info">
                <a class="linha__titulo" href="{% url 'quiz-resultado' item.tentativa_id %}">
                    {{ item.curso.nome_curso|default:"Resultado sem curso" }}
                </a>
                <p class="linha__descricao">{{ item.data|date:"d/m/Y" }} às {{ item.data|date:"H:i" }}</p>
            </div>
            {% if item.match is not None %}<span class="chip chip--area">{{ item.match }}% de afinidade</span>{% endif %}
        </li>
        {% endfor %}
    </ul>
    {% else %}
    <div class="vazio">
        <p>Você ainda não fez o teste com a conta logada.</p>
        <a class="botao" href="{% url 'quiz-inicio' %}">Fazer o teste</a>
    </div>
    {% endif %}
</section>
{% endblock %}
```

> [!important] Os dois números do perfil são clicáveis
> "1 teste feito" leva a "Meus testes", e "2 cursos na lista" leva a "Minha lista". Número que não leva a lugar nenhum é enfeite; e esses dois são **os únicos** que o sistema mede de verdade sobre a pessoa.

---

## 3️⃣ FT-13 — `backend/templates/quiz/link_invalido.html` (substitua)

```django
{% extends "base.html" %}

{% block title %}Link encerrado{% endblock %}

{% block content %}
<section class="cartao cartao--centro">
    <h1>Este link não existe ou foi encerrado</h1>
    <p class="subtitulo">
        Confira com a sua escola se o endereço está certo. Você também pode fazer
        o teste por conta própria: o resultado é o mesmo, só não fica ligado à turma.
    </p>
    <a class="botao botao--bloco" href="{% url 'quiz-inicio' %}">Fazer o teste mesmo assim</a>
</section>
{% endblock %}
```

---

## 4️⃣ FT-14 — o painel nas cores novas

O `painel.css` foi escrito antes dos tokens. Quatro ajustes:

**1. A caixa de aviso tinha cores escritas direto.** Troque:

```css
/* ANTES */
  background: #fff8e1;
  border-left: 4px solid #b26a00;

/* DEPOIS */
  background: var(--marca-clarinho);
  border-left: 4px solid var(--alerta);
```

**2. A coluna do grid, e os botões de período quebrando linha.** Em `.painel` e `.painel__periodos`:

```css
.painel {
  display: grid;
  grid-template-columns: minmax(0, 1fr); /* sem isto, texto com nowrap alarga a página */
  gap: 1.5rem;
}

.painel__periodos {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
```

**3. A tabela de conversão tem quatro colunas e não cabe em 390 px.** Ela rola **dentro do cartão**, nunca a página inteira. Depois de `.painel__cartao--largo`:

```css
/* Tabela larga rola dentro do cartão, nunca a página inteira (celular) */
.painel__cartao {
  min-width: 0;
  overflow-x: auto;
}
```

**4. A classe `botao--ghost` não existe mais.** No `painel/templates/painel/dashboard.html`, o botão "Copiar":

```html
<button type="button" class="botao botao--texto" data-copiar>Copiar</button>
```

Por fim, troque no `painel.css` os nomes antigos pelos novos: `--vermelho` → `--marca`, `--vermelho-escuro` → `--marca-escuro`, `--cinza` → `--texto-3`. Depois disso, avise a pessoa D: as três linhas de "nomes antigos" do `tokens.css` podem sair.

---

## 5️⃣ Verificação

```bash
python manage.py test quiz.tests.test_paginas accounts painel -v 2
python manage.py test 2>&1 | tail -3
grep -n "#[0-9a-fA-F]\{3,6\}\|--vermelho\|--cinza" backend/static/css/painel.css      # tem de voltar vazio
```

| # | O quê | Sinal de que passou |
|---|---|---|
| 1 | `/entrar/` | Igual ao mockup 11 |
| 2 | Entrar com senha errada | A mensagem aparece em vermelho, acima dos campos |
| 3 | Criar conta com senha fraca | O erro aparece embaixo do campo da senha |
| 4 | `/lista_interesse/` com dois cursos | Igual ao mockup 12, mais o "Remover" |
| 5 | Lista vazia | "Você ainda não salvou nenhum curso" + "Fazer o teste" |
| 6 | `/meu-perfil/` | Dois números clicáveis e o histórico com links |
| 7 | `/questionario/00000000-0000-0000-0000-000000000000/` | "Este link não existe ou foi encerrado" |
| 8 | `/painel/` como staff, em 390 px | A tabela de conversão rola dentro do cartão; a página não rola para o lado |

## 6️⃣ Commit e PR

```bash
git add -A
git status --short
git commit -m "feat(front): telas da conta e painel nos tokens (FT-11 a FT-14)"
git push -u origin front/conta-painel
```

No PR: prints das telas 11 e 12 ao lado dos mockups, e o painel em 390 px.

## ▶️ Próxima ação

Criar a branch `front/conta-painel` e começar pelo `_campo.html`.

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/spec-front-templates|🎨 Spec do front]] — V1 (e-mail, não CPF)
- [[Projetos/EducMatch(Secretária)/passo-a-passo-pnl-01-pnl-05|📊 PNL]] — as regras de privacidade do painel, que não mudam
