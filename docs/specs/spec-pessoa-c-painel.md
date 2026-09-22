---
title: "Spec — Pessoa C · Painel administrativo (template, métricas e privacidade)"
aliases: ["Spec pessoa C", "Spec painel", "PR-4 painel", "PR-5 métricas"]
tags: [tcc, painel, django, templates, metricas, privacidade, spec]
status: proposto
projeto: TCC
criado: 2026-09-22
---

> [!info] Visão geral: [[Projetos/EducMatch(Secretária)/tarefas-backend-por-pessoa|👥 Tarefas por pessoa]] · Código de referência: [[Projetos/EducMatch(Secretária)/passo-a-passo-pnl-01-pnl-05|📊 PNL-01 a PNL-05]] · [[Projetos/EducMatch(Secretária)/passo-a-passo-bk-01-bk-08|🔧 BK]] §4 e §5 (só o que for de métrica e privacidade) · [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|📊 Spec do painel]] · Colegas: [[Projetos/EducMatch(Secretária)/spec-pessoa-a-infra|🧱 A]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-b-dados-motor|🧮 B]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-d-telas|🎨 D]]

# 📊 Spec — Pessoa C · Painel administrativo

> [!abstract] Sua missão em uma frase
> Entregar **um painel só**, em `/painel/`, que mostra para a coordenação **o que o catálogo e a demanda estão dizendo**, sem nunca deixar identificar uma pessoa.

> [!important] A frase que decide cada tela
> O painel responde perguntas sobre **cursos e demanda**, nunca sobre **pessoas**. Se um número, somado a qualquer contexto de fora ("quem faltou hoje", "o único aluno do turno da noite"), identifica alguém, ele não aparece.

| PR | Branch | Quando | Depende de |
|---|---|---|---|
| **PR-4** | `feat/painel-template` | Rodadas 1 e 2 | nada |
| **PR-5** | `feat/painel-metricas` | Rodada 3 | PR-2 da **pessoa B** (demanda por área e aderência) |

---

## 1️⃣ O estado de hoje

Existem **dois dashboards**, e nenhum está certo:

| | `/quiz/dashboard/` (o que está no ar) | App `painel/` (o que foi planejado) |
|---|---|---|
| Onde está | `dashboard_view` em `quiz/views.py` + `templates/quiz/dashboard.html` | `painel/metricas.py`, `privacidade.py` e `views.py` |
| Funciona? | Sim | **Não**: a URL não está montada em `core/urls.py` e o template `painel/dashboard.html` não existe |
| Privacidade | **Nenhuma**: mostra contagem de resposta por alternativa, mesmo que seja 1 pessoa | k-anonimato pronto em `privacidade.py` |
| Gera link de questionário | Sim | Não |

**O seu trabalho é juntar os dois:** o `painel/` vira o único painel, com a privacidade dele e o gerador de link do dashboard antigo. No fim, `/quiz/dashboard/` redireciona para `/painel/`.

---

## 2️⃣ As regras de privacidade (valem para todo número que você mostrar)

| Regra | Como aparece no código |
|---|---|
| Nenhuma consulta usa `user` nem `respondido_por` | `metricas.py`: nenhuma função recebe usuário |
| Nenhum número é clicável (sem *drill-down*) | Zero `<a>` em número no template |
| **k = 5**: célula com menos de 5 respondentes mostra `—` | `privacidade.suprimir_pequenos` |
| Conta por **tentativa**, não por usuário | `distinct=True` sobre `tentativa_id` |
| Período com menos de 5 tentativas → só o total | `privacidade.periodo_tem_massa_suficiente` |

> [!danger] A supressão é feita no servidor, nunca no template
> Se o número real chegar no contexto e o template só "não mostrar", ele está no HTML: basta um *ver código-fonte*. Suprima **na view**, antes de montar o contexto.

> [!danger] A taxa denuncia o número escondido
> Na conversão, se `interessados` vira `—` mas a `taxa` e o `recomendado` continuam na linha, `taxa × recomendado ÷ 100` devolve o número escondido. **Linha suprimida perde a taxa também.**

> [!note] Suprimir o valor, não a linha
> Se a tabela mostra 17 cursos e todos sabem que o catálogo tem 20, os 3 que sumiram têm entre 1 e 4 respondentes: a informação vazou pela ausência. Mantenha as 20 linhas e troque o valor por `—`.

---

## 3️⃣ O que é seu (e o que não é)

| ✅ Você pode mexer | ❌ Não mexa |
|---|---|
| `painel/` inteiro: `metricas.py`, `privacidade.py`, `views.py`, `urls.py`, `templates/painel/`, `tests/` | `models.py` e migrações → **B** (os índices do painel são dela, no PR-3) |
| `static/css/painel.css` (novo) e `static/js/painel.js` (novo, se precisar) | `static/css/style.css`, `static/js/quiz.js` e `templates/base.html` → **D** |
| Em `quiz/views.py`: `dashboard_view`, `gerar_questionario_link` e `superuser_required` | `core/settings.py` → **A** |
| `templates/quiz/dashboard.html` (você vai aposentar) | |
| Uma linha em `core/urls.py` (`painel/`) e as duas linhas do dashboard em `quiz/web_urls.py` | O resto de `quiz/web_urls.py` → **D** |

> [!warning] O CSS do painel fica num arquivo seu
> O `style.css` é da pessoa D, e ela está mexendo nele. Para vocês não brigarem no mesmo arquivo, o painel usa `static/css/painel.css`. Peça para a D criar, **no primeiro dia**, um bloco no `<head>` do `base.html`:
> ```html
> {% block estilos %}{% endblock %}
> ```
> No seu template: `{% block estilos %}<link rel="stylesheet" href="{% static 'css/painel.css' %}">{% endblock %}`.

---

## 4️⃣ Antes de começar

```bash
cd educmatch
git switch main
git pull
git switch -c feat/painel-template
cd backend
source .venv/Scripts/activate
python manage.py test painel 2>&1 | tail -5      # anote: é a sua linha de base
```

> [!note] Os testes do painel estão quebrados antes de você começar
> Os testes em `painel/tests/` chamam métodos que nunca foram escritos (`criar_curso_com`, `criar_curso`, `criar_tentativa_com_explicacao`, `criar_tentativas`) e a rota `painel-dashboard`, que não está montada. Faz parte do seu trabalho fazê-los rodar.

Para ter dado para olhar, crie um superusuário e responda o quiz algumas vezes:

```bash
python manage.py createsuperuser
```

Para testar a supressão, você precisa de **mais de 5 tentativas** no período. Responda o quiz 6 ou 7 vezes em `http://localhost:8000/` (numa janela anônima, cada envio é uma tentativa).

---

## 5️⃣ PR-4 — o painel no ar, com privacidade

### Passo 1 · montar a URL

- [ ] Em `core/urls.py`, antes das rotas `""`: `path("painel/", include("painel.urls")),`
- [ ] Confira `painel/urls.py`: `path("", dashboard, name="painel-dashboard")`

### Passo 2 · os métodos que os testes esperam

- [ ] Crie os helpers que faltam (`criar_curso`, `criar_curso_com`, `criar_tentativas`, `criar_tentativa_com_explicacao`) numa base de testes do painel (`painel/tests/base.py`), herdando de `quiz.tests.base.BaseEducMatch`
- [ ] Rode `python manage.py test painel` e veja quais ficam vermelhos **pelo motivo certo** (a regra ainda não existe), não por erro de nome

### Passo 3 · métricas que não rodam hoje (as que não dependem da pessoa B)

A tabela está na [[Projetos/EducMatch(Secretária)/passo-a-passo-bk-01-bk-08|BK]] §4 ("seis consertos"). Destas, **quatro** você faz já:

- [ ] `conversao_por_curso` dá `ValueError` (anota com o nome `interessados`, que já é um `related_name`) → anotar como `n_interessados` e devolver a chave `interessados` no dicionário
- [ ] `top_cursos_com_manifestacoes` conta recomendação, e não interesse → contar `Interesse`
- [ ] `distribuicao_de_confianca` usa `confidence_level` → `confidence_band`
- [ ] Nas funções com `values("curso_id", "curso__nome_curso")`, troque por `nome=F("curso__nome_curso")`, para o template ler `linha.nome`

As outras duas (demanda por área e aderência) dependem dos dados novos da pessoa B: ficam para o PR-5.

### Passo 4 · a view, com a privacidade completa

A view atual (`painel/views.py`) já aplica quase tudo. Faltam três coisas, todas descritas na BK §5 (as notas `[!danger]` e `[!important]` logo depois do código do painel):

- [ ] **Taxa da linha suprimida:** depois do `suprimir_pequenos` da conversão, zere a `taxa` das linhas com `suprimido`
- [ ] **Confiança suprimida:** `distribuicao_de_confianca` também passa por `suprimir_pequenos` ("1 tentativa de confiança baixa" num período de 6 é número individual)
- [ ] **Aderência por posição suprimida:** `aderencia["por_posicao"]` passa por `suprimir_pequenos`

### Passo 5 · o gerador de link de questionário

A coordenação usa o dashboard antigo para gerar o link que manda para a turma. Isso vem para o painel:

- [ ] Uma view `gerar_link` em `painel/views.py` (POST, só staff) que cria um `QuestionarioLink` e volta para `/painel/`. Use o `gerar_questionario_link` de `quiz/views.py` como modelo
- [ ] Rota `path("gerar-link/", gerar_link, name="painel-gerar-link")`
- [ ] No painel, a lista dos 5 links ativos com a URL completa e um botão "copiar"

> [!note] Staff ou superusuário?
> O dashboard antigo exige **superusuário**; o `painel/` usa `@staff_member_required` (qualquer *staff*). Fique com `@staff_member_required`: é o que o `/admin` já usa. E peça à pessoa D para trocar, no `base.html`, o `{% if user.is_superuser %}` do link "Dashboard" por `{% if user.is_staff %}`, apontando para `{% url 'painel-dashboard' %}`.

### Passo 6 · o template `painel/templates/painel/dashboard.html`

O código base está na [[Projetos/EducMatch(Secretária)/passo-a-passo-pnl-01-pnl-05|PNL]] §5 (PNL-04). O que a tela precisa ter:

- [ ] `{% extends "base.html" %}` e o `painel.css` no bloco `estilos`
- [ ] Seletor de período **30 · 90 · 365 dias** (links `?periodo=30` etc., com o atual marcado)
- [ ] Total de tentativas no período, sempre visível
- [ ] Se `tem_massa` for falso: **só** o total e um aviso "Menos de {{ k_minimo }} tentativas no período: os números detalhados ficam escondidos para proteger quem respondeu"
- [ ] Tabelas: top cursos em 1º lugar, top cursos no top 5, manifestações de interesse, conversão por curso (recomendado · interessados · taxa), distribuição de confiança, cursos nunca recomendados e cobertura de áreas
- [ ] Célula com `suprimido` mostra **`—`**, nunca `0`
- [ ] Nenhum número é link
- [ ] Barras simples em CSS (uma `<div>` com `width: {{ percentual }}%`) no lugar de biblioteca de gráfico. Opcional, mas fica bonito na defesa
- [ ] Tabelas acessíveis: `<caption>`, `<th scope="col">`, e o `—` com `<abbr title="menos de 5 respondentes">—</abbr>`

### Passo 7 · aposentar o dashboard antigo

- [ ] Em `quiz/web_urls.py`, `quiz/dashboard/` vira um redirecionamento permanente para `/painel/`, para nenhum favorito quebrar:
  ```python
  from django.views.generic import RedirectView
  path("quiz/dashboard/", RedirectView.as_view(pattern_name="painel-dashboard", permanent=True), name="dashboard"),
  ```
- [ ] Apague `dashboard_view`, `gerar_questionario_link` e `superuser_required` de `quiz/views.py`, a rota `gerar-link` antiga e `templates/quiz/dashboard.html`
- [ ] Ajuste `quiz/tests/test_rotas_web.py::test_dashboard_continua_na_mesma_url`: agora `/quiz/dashboard/` responde **301** para `/painel/`

## 6️⃣ PR-4 — pronto quando

```bash
python manage.py test painel -v 2
python manage.py test 2>&1 | tail -5       # nenhuma falha nova
```

- [ ] Anônimo em `/painel/` → vai para o login; usuário comum → **não** vê o painel; staff → vê
- [ ] Com menos de 5 tentativas no período: só o total aparece
- [ ] Com 6 ou 7 tentativas: aparecem números, e toda célula abaixo de 5 é `—`
- [ ] Linha de conversão suprimida **sem** taxa
- [ ] Nenhum nome de respondente no HTML (*ver código-fonte* e `Ctrl+F` pelo nome que você digitou no quiz)
- [ ] Gerar um link no painel → abrir o link numa janela anônima → cai no quiz
- [ ] `/quiz/dashboard/` redireciona para `/painel/`

### Como abrir o PR

```bash
git add -A
git status --short
git commit -m "feat(painel): painel unico em /painel/ com k-anonimato e gerador de link"
git push -u origin feat/painel-template
```

```markdown
## O que muda
- /painel/ no ar: um painel só, com k-anonimato (k = 5)
- Supressão também na taxa de conversão, na confiança e na aderência por posição
- Gerador de link de questionário dentro do painel
- /quiz/dashboard/ redireciona para /painel/; o dashboard antigo foi removido

## Toca contrato de outra frente?
Não: o painel só lê.

## Como testar
1. Responder o quiz 6 vezes numa janela anônima
2. Entrar como staff → /painel/ → conferir os "—"
3. Ver código-fonte: nenhum nome de respondente
```

---

## 7️⃣ PR-5 — as métricas que dependem da pessoa B

Comece **depois** que a pessoa B avisar que o PR-2 entrou:

```bash
git switch main
git pull
git switch -c feat/painel-metricas
python manage.py migrate
```

- [ ] `demanda_por_area`: hoje conta a string `"top_areas"`. Passa a ler a área dominante de cada 1º lugar: `(explicacao or {}).get("top_areas")[0]["area"]` (código na BK §4)
- [ ] `aderencia_a_recomendacao`: passa a usar `Interesse.rank_snapshot` e `era_principal`. Pergunta que ela responde: "quando o aluno salva um curso, ele costuma salvar o 1º lugar?"
- [ ] `cobertura_de_areas`: `Count("pesos_alternativa")` → `Count("pesos__alternativa")`
- [ ] Acrescente `tentativas_via_link(inicio)`: quantas tentativas do período vieram por link de questionário (código na BK §5). Mostre no painel como "respostas vindas do link da escola"
- [ ] Corrija `painel/tests/test_metricas.py::test_demanda_por_area_le_o_jsonfield`: ele monta `{"eletrica": 0.6, "ti": 0.2}`, um formato que o motor **nunca** gravou. Troque por `{"top_areas": [{"area": "eletrica", "area_name": "Elétrica", "contribuicao": 3.0, "percentual": 75.0}]}`

## 8️⃣ PR-5 — pronto quando

- [ ] `python manage.py test painel -v 2` inteiro verde
- [ ] "Demanda por área" mostra nomes de área de verdade (Elétrica, TI…), não `top_areas`
- [ ] Aderência mostra a porcentagem de interesses que eram o 1º lugar
- [ ] Nenhuma falha nova na suíte

---

## 9️⃣ Armadilhas

> [!warning] Gráfico vazio sem erro nenhum
> Se as tabelas por período saírem vazias com dado no banco, o culpado quase sempre é o MySQL **sem as tabelas de fuso**. Rode o teste da pessoa A: `python manage.py test core`.

> [!warning] `@staff_member_required` manda para o login do `/admin`
> Quem não é *staff* cai na tela de login do `/admin`, não na `/entrar/` do projeto. É o comportamento certo (o painel é ferramenta de administração), mas avise quem for testar para não achar que errou a URL.

> [!note] Quem precisa ver um caso individual usa o `/admin`
> Não é limitação, é desenho: o `/admin` já controla quem é *staff*. Construir no painel um segundo caminho para dado individual seria duplicar isso com metade dos controles. É um bom parágrafo para a monografia.
