---
title: "Spec — Pessoa D · Telas do aluno (templates, CSS, JS e acessibilidade)"
aliases: ["Spec pessoa D", "Spec telas do aluno", "PR-0 limpeza", "PR-7 telas", "PR-8 acessibilidade"]
tags: [tcc, front, django, templates, css, javascript, acessibilidade, spec]
status: proposto
projeto: TCC
criado: 2026-09-22
---

> [!info] Visão geral: [[Projetos/EducMatch(Secretária)/tarefas-backend-por-pessoa|👥 Tarefas por pessoa]] · Front atual: [[Projetos/EducMatch(Secretária)/front-templates-django|🎨 Templates do Django]] · Colegas: [[Projetos/EducMatch(Secretária)/spec-pessoa-a-infra|🧱 A]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-b-dados-motor|🧮 B]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-c-painel|📊 C]]

# 🎨 Spec — Pessoa D · Telas do aluno

> [!abstract] Sua missão em uma frase
> Fazer o caminho do aluno (**entrar no quiz → responder → ver o resultado → conhecer o curso → salvar na lista**) funcionar inteiro, com a identidade visual do guia de estilo, **acessível por teclado** e **funcionando mesmo sem JavaScript**.

> [!important] Por que HTML, CSS e JS puro (decisão de 2026-09-22)
> O front React foi abandonado. As telas são templates do Django com CSS e JS puro. Isso tem três ganhos que valem um parágrafo na monografia:
> 1. **Todo o grupo consegue mexer no front**, não só uma pessoa;
> 2. **Um processo, um endereço**: sem API, sem CORS, sem CSRF entre origens, sem segundo servidor;
> 3. **Aprimoramento progressivo**: o quiz é um formulário HTML que funciona **sem JavaScript**; o `quiz.js` só o transforma num passo a passo, uma pergunta por vez. Se o JS falhar na apresentação, o quiz continua respondível.

| PR | Branch | Quando | O que entrega |
|---|---|---|---|
| **PR-0** | `chore/remove-react-e-api` | **Hoje**, antes de todos | Remoção do React e da API REST (já feita no seu clone, falta o commit) |
| **PR-7** | `feat/telas-aluno` | Rodadas 1 e 2 | Detalhe do curso, resultado, perfil sem números inventados, histórico |
| **PR-8** | `feat/telas-acessibilidade` | Rodadas 3 e 4 | Guia de estilo aplicado, acessibilidade, link de questionário, testes de rota |

---

## 1️⃣ O que é seu (e o que não é)

| ✅ Você pode mexer | ❌ Não mexa |
|---|---|
| `templates/` (menos `quiz/dashboard.html`) e `accounts/templates/` | `painel/` e `templates/quiz/dashboard.html` → **C** |
| `static/css/style.css` e `static/js/quiz.js` | `static/css/painel.css` → **C** |
| `quiz/web_views.py`, **menos** `areas_da_recomendacao` até o PR-2 entrar | `models.py`, migrações e `quiz/engine.py` → **B** |
| `accounts/views.py`, **menos** `_salvar_interesse_pendente` e `salvar_interesse` até o PR-2 entrar | `core/settings.py` → **A** |
| `accounts/urls.py`, `quiz/web_urls.py` (menos as linhas do dashboard), `catalogo/views.py` e `catalogo/urls.py` | |
| `accounts/tests/test_c5_rotas.py`, `accounts/tests/test_c6_claim.py` e `quiz/tests/test_rotas_web.py` | |

> [!warning] Dois pedidos que chegam no seu primeiro dia
> - **Da pessoa C:** criar `{% block estilos %}{% endblock %}` dentro do `<head>` do `base.html`, para o painel carregar o CSS dele sem mexer no seu `style.css`. Depois, trocar no menu o link "Dashboard" para `{% if user.is_staff %}` e `{% url 'painel-dashboard' %}`.
> - **Da pessoa B:** não mexer nas funções `areas_da_recomendacao`, `_salvar_interesse_pendente` e `salvar_interesse` até o PR-2 dela entrar.

---

## 2️⃣ PR-0 — fechar a remoção do React e da API (hoje)

No seu clone (`Documents/educmatch/educmatch`) já estão feitas, sem commit: a pasta `frontend/` apagada e a API REST removida (`quiz/urls.py`, `quiz/serializers.py`, `quiz/tests/test_api.py`, as views da API em `quiz/views.py`, o dashboard movido para `quiz/web_urls.py` na mesma URL, e o teste novo `quiz/tests/test_rotas_web.py`).

> [!danger] Não commite as suas mudanças locais junto
> O `settings.py` tem `'USER': 'tecmysql'`, que é configuração **da sua máquina**; o `quiz/models.py` tem só uma limpeza de comentário. E o `style.css`/`quiz.js` são trabalho em andamento do PR-7. Nada disso entra no PR-0.

```bash
cd Documents/educmatch/educmatch
git switch -c chore/remove-react-e-api
git add frontend backend/core/urls.py backend/quiz/views.py backend/quiz/web_urls.py \
        backend/quiz/urls.py backend/quiz/serializers.py backend/quiz/tests/test_api.py \
        backend/quiz/tests/test_rotas_web.py
git status --short        # só isso em verde; settings.py, models.py, style.css e quiz.js continuam em vermelho
```

- [ ] No `README.md`: tirar a seção "Frontend" (pnpm, Vite, React), a pasta `frontend/` da árvore e o React/Vite/Tailwind de "Tecnologias". Um servidor só: `http://localhost:8000`
- [ ] No `.gitignore` da raiz: pode tirar as linhas só do front (`node_modules/`, `.pnpm/`, `.vite/`, `*.tsbuildinfo`). **Não** tire o `.env`
- [ ] Nas notas do vault `spec-front-react-vite`, `plano-execucao-front-react` e `passo-a-passo-fe-*`: um aviso no topo, `> [!warning] Abandonado em 2026-09-22: o front voltou a ser templates do Django. Mantido como histórico.`

```bash
git add README.md .gitignore
git commit -m "chore: remove o front React e a API REST sem consumidor"
git push -u origin chore/remove-react-e-api
```

Peça revisão, mescle e avise: "PR-0 entrou: `git pull`. O front agora é só o Django, em `localhost:8000`".

---

## 3️⃣ Antes do PR-7

```bash
git switch main
git pull
git switch -c feat/telas-aluno
git stash list             # se você guardou o style.css/quiz.js em stash, traga de volta: git stash pop
python manage.py test 2>&1 | tail -5     # a linha de base
```

**Referências visuais:** `Desktop/guia-de-estilo-educmatch.pdf` (cores, tipografia, componentes) e `Desktop/wireframes-educmatch.pdf` (o desenho de cada tela). Todas as cores e tamanhos vão em variáveis no `:root` do `style.css`, com nome, para ninguém repetir `#1a73e8` em 30 lugares.

---

## 4️⃣ PR-7 — as telas do aluno

### Passo 1 · o aviso de baixa confiança que nunca aparecia

Em `templates/quiz/resultado.html`, a linha 12 testa `tentativa.confidence_level`, mas o campo se chama **`confidence_band`**. O aviso "sua afinidade ficou baixa" **nunca** aparece por causa disso.

- [ ] Trocar para `{% if tentativa.confidence_band == "baixa" %}`
- [ ] Escrever um teste (em `quiz/tests/test_resultado.py`) que força uma tentativa com `confidence_band="baixa"` e afirma que o aviso aparece na página. É o seu "teste que falharia antes"

### Passo 2 · a página de detalhe do curso (hoje ela existe, mas ninguém chega nela)

`templates/quiz/curso_detalhe.html` existe, mas **não tem view nem rota**. E o template usa campos que não existem (`curso.nome` e `curso.main_area`).

- [ ] View `curso_detalhe(request, pk)` em `catalogo/views.py`: `get_object_or_404(Curso, pk=pk, is_active=True)` com `select_related("area_principal")`
- [ ] Rota `path("cursos/<int:pk>/", curso_detalhe, name="curso-detalhe")` num `catalogo/urls.py` novo, incluído em `core/urls.py`
- [ ] No template: `curso.nome_curso` e `curso.area_principal.nome`
- [ ] No resultado, o nome de cada curso vira link para o detalhe, e o detalhe tem "Voltar para o meu resultado" (passe o id da tentativa por `?tentativa=<id>`)
- [ ] O botão "Salvar na minha lista" também no detalhe, usando o mesmo formulário do resultado

### Passo 3 · o perfil, sem números inventados

`aluno_perfil` (em `accounts/views.py`) manda para o template `aulas_concluidas`, `horas_estudadas`, `exercicios_feitos` e `sequencia_dias`, **todos fixos em 0**. O sistema não mede nada disso. Na banca, número inventado na tela é pergunta difícil.

- [ ] Tirar `estatisticas` e `progresso` da view
- [ ] Mostrar só o que o sistema sabe de verdade: **quantos testes a pessoa fez** e **quantos cursos estão na lista**
- [ ] Cada item do histórico no perfil vira link para `/resultado/<id>/`
- [ ] Apagar `accounts/templates/accounts/perfil.html`, que está vazio e não é usado

### Passo 4 · "Meus testes" e "Minha lista"

- [ ] `accounts/templates/accounts/tentativas.html`: cada tentativa com data, 1º curso e afinidade, e o link para o resultado
- [ ] `accounts/templates/accounts/lista.html`: cada curso com link para o detalhe e o botão remover
- [ ] Estados vazios com uma ação: "Você ainda não fez o teste → Fazer o teste"

### Passo 5 · o CSS que você já começou

- [ ] Terminar o trabalho do `style.css` que está sem commit, com as variáveis do guia de estilo
- [ ] Os comentários que você tirou do `quiz.js` explicavam o *porquê* de trechos que não são óbvios (a pausa de 320 ms, o Enter que não envia pela metade). **Deixe esses de volta**: são eles que deixam outra pessoa do grupo mexer no arquivo sem quebrar

## 5️⃣ PR-7 — pronto quando

- [ ] Fazer o caminho inteiro sem digitar URL: início → quiz → resultado → detalhe → salvar → Minha lista → Meus testes → abrir o resultado de novo
- [ ] Um perfil "indeciso" (tudo na mesma coluna) mostra o aviso de baixa confiança
- [ ] Nenhum número na tela é fixo ou inventado
- [ ] `python manage.py test` sem falha nova, com o teste do passo 1

Commit sugerido: `feat(telas): detalhe do curso, perfil sem numeros inventados e aviso de confianca`.

---

## 6️⃣ PR-8 — acessibilidade, link de questionário e rotas

### Passo 1 · acessibilidade

- [ ] **Quiz inteiro só com teclado:** Tab chega em cada alternativa, as setas trocam de opção, Enter avança. Teste com o mouse longe
- [ ] **Foco visível:** `:focus-visible` com contorno forte em todo link, botão e alternativa. Nunca `outline: none` sem colocar outro no lugar
- [ ] **Alvos grandes:** botões e alternativas com pelo menos **48 px** de altura (o público responde pelo celular)
- [ ] **Cada pergunta continua sendo um `<fieldset>` com `<legend>`** (o `quiz.html` já faz isso: não perca ao redesenhar). É o que faz o leitor de tela ler a pergunta junto com as opções
- [ ] **Mensagens anunciadas:** o aviso "responda antes de avançar" e as mensagens do Django (`messages`) com `role="alert"` ou `aria-live="polite"`
- [ ] **A barra de progresso** com `role="progressbar"` e `aria-valuenow`, ou um texto "Pergunta 3 de 6"
- [ ] **Contraste:** texto com pelo menos 4,5:1 sobre o fundo (confira as cores do guia num verificador de contraste)
- [ ] **Sem JavaScript:** desligue o JS no navegador (DevTools → Configurações → Desativar JavaScript) e responda o quiz inteiro. Tem de funcionar

### Passo 2 · o link de questionário da escola

Hoje, token inexistente ou encerrado em `/questionario/<token>/` mostra o 404 padrão do Django.

- [ ] Uma página "Este link não existe ou foi encerrado", com o botão "Fazer o teste mesmo assim"
- [ ] Quando a pessoa entrou pelo link, uma faixa no quiz e no resultado: "Você está respondendo pelo link da escola"

### Passo 3 · os testes de rota (contratos C5 e C6)

- [ ] `accounts/tests/test_c6_claim.py` usa `reverse("criar-conta")`, mas a rota se chama `cadastro_usuario`. Corrija os nomes e crie os métodos auxiliares que faltam. Referência: [[Projetos/EducMatch(Secretária)/passo-a-passo-tst-01-tst-05|🧪 TST]] §3 e §4
- [ ] `accounts/tests/test_c5_rotas.py`: todas as páginas do aluno exigem login quando devem, e ninguém abre resultado de outra pessoa (**404**, nunca 403)

## 7️⃣ PR-8 — pronto quando

- [ ] Quiz inteiro respondido só com teclado e, separadamente, com o JavaScript desligado
- [ ] Token inválido mostra a página própria, não o 404 do Django
- [ ] `test_c5_rotas` e `test_c6_claim` verdes
- [ ] Um colega do grupo faz o caminho inteiro no celular dele, sem ajuda

Commit sugerido: `feat(telas): acessibilidade, link de questionario e testes de rota`.

---

## 8️⃣ Você também é a pessoa que conhece o front

Nas rodadas, você é quem mais sabe de HTML e CSS. Reserve tempo para:

- [ ] Revisar o template do painel da pessoa C (acessibilidade das tabelas, o `—` com explicação)
- [ ] Fazer o primeiro PR de cada colega junto, pelo Live Share, **com o colega como anfitrião** (a branch é dele)

---

## 9️⃣ Armadilhas

> [!danger] Não troque formulário por `fetch`
> A tentação, vindo do React, é mandar as respostas por JavaScript. Não faça: é isso que mantém o quiz funcionando sem JS, e cada `fetch` reabre o problema de CSRF que o projeto acabou de eliminar. JavaScript aqui só **melhora** um HTML que já funciona.

> [!warning] Arquivo estático não atualiza
> O navegador guarda o CSS e o JS em cache. Se a mudança não aparece, `Ctrl+F5`. Com `DEBUG=1`, o `runserver` serve a versão nova, mas o navegador pode não pedir.

> [!note] Cuidado com o `{% csrf_token %}`
> Todo `<form method="post">` precisa dele. Esquecer dá um 403 "CSRF verification failed" que parece bug do backend.
