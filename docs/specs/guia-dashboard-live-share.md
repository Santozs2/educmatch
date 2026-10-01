---
title: "Guia do dashboard — como o grupo trabalha junto no Live Share"
aliases: ["Guia do dashboard", "Dashboard no Live Share", "Mapa do dashboard"]
tags: [tcc, painel, dashboard, avaliacao, live-share, guia, spec]
status: proposto
projeto: TCC
criado: 2026-10-01
---

> [!info] Specs: [[spec-dashboard-pessoa-a-dados|🧮 A · Dados e regras]] · [[spec-dashboard-pessoa-b-telas|🖼️ B · Telas]] · [[spec-dashboard-pessoa-c-estilo-e-testes|🎨 C · Estilo, comportamento e testes]] · Design aprovado: `educmatch_dashboard_responsivo (2).html`

# 🖥️ Guia do dashboard: como o grupo trabalha junto

> [!abstract] O que esta nota é
> O **mapa** do trabalho do dashboard para as **três pessoas do grupo**, trabalhando **ao mesmo tempo no Live Share**. Aqui estão: quem faz o quê, como não atrapalhar um ao outro, os nomes que todo mundo precisa combinar antes de começar, e os **5 pontos de encontro** em que o grupo para, testa junto e só então segue.
> O passo a passo de cada pessoa, arquivo por arquivo, está na spec dela (links acima).

> [!success] O código das specs já foi testado
> Tudo o que está nas três specs foi aplicado numa cópia do projeto, rodado no MySQL e aberto no navegador com dados falsos, em tela de computador (1440px) e de celular (375px). Os números de testes de cada etapa são os que vocês devem ver.

---

## 👥 Quem é quem

| Pessoa | Frente | É dona de | Em uma frase |
|---|---|---|---|
| 🧮 **A** | Dados e regras | Todo arquivo **`.py`** que não é teste: `metricas.py`, `views.py`, `urls.py`, `models.py`, `forms.py`, migrações, seed | Decide **o que** cada tela recebe, e garante que nenhum número identifique uma pessoa |
| 🖼️ **B** | Telas | Todo arquivo **`.html`**: `base_painel.html` e as telas do painel e do aluno | Decide **onde** cada coisa aparece na tela |
| 🎨 **C** | Estilo, comportamento e testes | Todo **`.css`**, todo **`.js`** e todos os **testes** | Decide **como** a tela se parece e se comporta, e **prova** que o que A e B fizeram funciona |

> [!tip] Por que C escreve os testes do código de A
> Teste escrito por quem não escreveu o código pega o que o autor não pensou. É o mesmo motivo de alguém revisar a redação do outro: a gente não enxerga o próprio erro.

---

## 🤝 As regras do Live Share

No Live Share, **uma pessoa hospeda** e as outras entram na sessão. Todo mundo edita os **arquivos da máquina de quem hospeda**, ao mesmo tempo, vendo o cursor uns dos outros.

1. **Quem hospeda é a máquina que tem o MySQL e o `.venv` funcionando.** Ela roda o servidor e os testes. Combinem antes de começar quem é.
2. **Dono por arquivo.** Cada pessoa só **edita** os arquivos da sua frente (tabela acima). Pode **abrir e ler** qualquer um. Precisa mudar o arquivo de outra pessoa? Peça no chat da sessão.
3. **Terminal compartilhado só de leitura.** Quem hospeda roda os comandos (`test`, `migrate`, `runserver`) e compartilha o terminal **em modo leitura**. Assim todo mundo vê o resultado, mas dois comandos nunca rodam ao mesmo tempo.
4. **Servidor compartilhado.** Quem hospeda compartilha a porta `8000` (em "Shared Servers"). Os outros abrem `http://localhost:8000` na própria máquina e veem o mesmo site.
5. **Só a pessoa A cria migração**, pelo terminal de quem hospeda. Duas migrações criadas ao mesmo tempo no mesmo app quebram o `migrate`.
6. **Salve sempre** (`Ctrl+S`). O Live Share só manda para quem hospeda o que foi salvo.
7. **Para explicar algo, use "Seguir" (Follow).** Quem explica abre o arquivo e os outros clicam no nome dela para acompanhar a tela.

> [!warning] Antes de começar cada sessão
> Quem hospeda roda `python manage.py test` **uma vez**. Se algo já estiver vermelho antes de vocês mexerem, resolvam isso primeiro. Senão ninguém sabe se o erro novo é de hoje ou de antes.

---

## 📜 O contrato: os nomes que as três pessoas combinam

Para trabalhar **ao mesmo tempo**, B precisa saber o nome das variáveis que A vai mandar para a tela, e C precisa saber as classes que B vai usar, **antes** de o código do outro existir. Este é o contrato. Se alguém precisar mudar um nome, avisa as outras duas.

### Rotas (A cria, B usa no `{% url %}`)

| Nome | Endereço | Tela |
|---|---|---|
| `painel-dashboard` | `/painel/` | Início |
| `painel-quiz` | `/painel/quiz/` | Quiz — visão geral |
| `painel-cursos` | `/painel/cursos/` | Cursos e Áreas |
| `painel-links` | `/painel/links/` | Links de acesso do quiz |
| `painel-interesse` | `/painel/interesse/` | Lista de interesse |
| `painel-avaliacoes` | `/painel/avaliacoes/` | Links das turmas para a avaliação |
| `painel-avaliacoes-resultados` | `/painel/avaliacoes/resultados/` | Resultados das avaliações |
| `painel-avaliacoes-csv` | `/painel/avaliacoes/resultados.csv` | Download do CSV |
| `painel-gerar-link`, `painel-fechar-link`, `painel-fechar-um-link`, `painel-avaliacoes-gerar`, `painel-avaliacoes-fechar` | (só POST) | Ações dos botões |
| `avaliacao-responder`, `avaliacao-obrigado` | `/avaliacao/<token>/` | Telas do aluno |

### Variáveis que toda tela do painel recebe (A manda, B usa)

| Variável | O que é |
|---|---|
| `secao` | Qual item do menu fica marcado: `inicio`, `quiz`, `cursos`, `links`, `interesse`, `avaliacoes` |
| `periodo`, `periodo_label`, `periodo_qs`, `periodos`, `mes` | O filtro de período e o pedaço de endereço que os links do menu carregam |
| `total_de_tentativas`, `tem_massa`, `k_minimo` | Total de testes, se ele passa de 5 e o próprio 5 |

As variáveis de **cada tela** estão na spec de A, no começo de cada etapa, e repetidas na spec de B.

### Classes e ganchos (B escreve no HTML, C dá estilo e comportamento)

| Grupo | Nomes |
|---|---|
| Botões (nunca fantasma) | `botao`, `botao--secundario`, `botao--suave`, `botao--neutro`, `botao--perigo`, `botao--icone`, `botao--bloco` |
| Estrutura | `painel-app`, `painel-menu`, `painel-barra`, `painel-conteudo`, `painel-cabecalho`, `painel-kpis`, `painel-grade` (`--2`, `--3`, `--2-1`), `painel-card` |
| Pedaços | `painel-kpi`, `painel-ranking`, `painel-lista`, `painel-tabela`, `painel-selo`, `painel-suprimido`, `painel-aviso`, `painel-progresso`, `painel-funil`, `painel-qr`, `painel-distribuicao`, `painel-comentarios` |
| Ganchos de JS (`data-*`) | `data-abrir-menu`, `data-fechar-menu`, `data-confirmar`, `data-perigo`, `data-copiar`, `data-qr`, `data-alternar` |
| `id` que o JS procura | `painel-menu`, `painel-confirmar`, `periodo`, `mes`, `grafico-serie`, `grafico-areas`, `dados-serie`, `dados-areas` |

---

## 🗺️ As 5 etapas

Cada etapa tem trabalho para as três pessoas **ao mesmo tempo**, e termina num **ponto de encontro**: o grupo para, quem hospeda roda os testes, todo mundo olha a tela junto, e **só então** começa a próxima.

| Etapa | O que entrega | 🧮 A | 🖼️ B | 🎨 C | Testes ao final |
|---|---|---|---|---|---|
| **1** | A casca nova do painel e as telas **Início** e **Quiz** | 3 métricas novas, views e rotas | `base_painel.html` e as duas telas | Botões sólidos, `painel.css`, `painel.js`, gráficos e 10 testes | **96** |
| **2** | Telas **Cursos e Áreas**, **Links** e **Lista de interesse** | Supressão de várias colunas, 4 consultas, 3 views | 3 telas e o menu | Funil, QR code e 7 testes | **103** |
| **3** | **% concluídos** e **tempo típico** do quiz | Model `InicioDeQuiz`, migração e o registro do início | 4 KPIs na tela Quiz | 11 testes | **114** |
| **4** | **Avaliação de fim de curso**: a página do aluno | App `avaliacao` inteiro: models, seed, form e views | 3 telas do aluno | `avaliacao.css` e 11 testes | **125** |
| **5** | **Avaliações no painel**: links das turmas, resultados e CSV | Métricas da avaliação e 5 views | 2 telas, menu e mensagens | Estilos dos resultados e 12 testes | **137** |

> [!note] Os números de testes
> Contam a partir de **86**, que é o total com a PRE-03 já aplicada no código. Se a PRE-03 ainda não estiver aplicada, tirem 2 de cada número (84, 94, 101…).

> [!important] Por que nesta ordem
> - A **1** cria a casca, o CSS e o JS que todas as outras usam.
> - A **3** é a primeira com **migração**. Ela fica sozinha numa etapa para que, se algo der errado, o grupo saiba exatamente onde.
> - A **4** e a **5** são a avaliação. A 4 funciona sozinha (o link pode ser criado pelo admin); a 5 leva tudo para o painel.

### Dentro de cada etapa: quem espera quem

O contrato deixa os três começarem juntos, mas há uma ordem natural no fim:

```
A: métricas → views → avisa "views prontas" ──┐
B: telas (usando os nomes do contrato) ───────┼──► C: roda os testes ──► 🤝 ponto de encontro
C: CSS e JS → escreve os testes ──────────────┘
```

C escreve os testes enquanto A e B trabalham, mas só **roda** quando A avisa que as views estão prontas.

---

## 🔒 As regras do produto (valem para todas as etapas)

> [!danger] Regra 1: o painel fala de cursos, nunca de pessoas
> **k-anonimato com K = 5.** Toda contagem menor que 5 aparece como **"< 5" com um cadeado**. Toda **taxa** calculada sobre uma contagem escondida também some, porque taxa × total devolveria o número. Período com menos de 5 testes mostra só o total.

> [!danger] Regra 2: nenhum botão fantasma
> Botão fantasma é o de fundo transparente ou branco só com borda. No painel, todo botão tem **fundo sólido**. Há um teste que reprova o painel se aparecer `botao--contorno` ou `botao--texto`.

> [!danger] Regra 3: a avaliação de fim de curso é anônima por construção
> Os models da avaliação **não têm onde** guardar usuário, nome, e-mail, IP ou horário (só o dia). Não é uma promessa: é impossível pelo desenho.

### O que foi decidido em 2026-10-01

| Pergunta | Decisão |
|---|---|
| Implementar o design inteiro de uma vez? | **Não.** Primeiro o que já tem dado no banco (etapas 1 a 3), depois a avaliação (4 e 5) |
| Tentativas do quiz aparecem uma a uma para a coordenação? | Só **anônimas**, e numa fase futura |
| % concluídos e tempo médio não existem no banco | **Criar o registro de início** do quiz (etapa 3) |
| O "formulário" do design aparece no fim do quiz? | **Não.** É uma **avaliação aplicada no fim do curso técnico** |
| Como o aluno responde? | Por um **link da turma**, sem login |
| A avaliação tem construtor de perguntas? | **Não.** É **fixa**, com perguntas num seed (proposta a revisar pela coordenação) |

---

## 🎓 Conceitos que aparecem nas specs

Leiam juntos antes da etapa 1. Cada spec explica cada um no lugar onde ele aparece; aqui é só o resumo.

| Conceito | Em uma frase | Onde aparece |
|---|---|---|
| **Herança de template** | Uma tela "estende" outra e só preenche os `{% block %}` que mudam | `base_painel.html` (etapa 1) |
| **Contexto** | O dicionário que a view manda para o template; cada chave vira uma variável no HTML | Todas as views |
| **k-anonimato** | Esconder toda contagem pequena o bastante para apontar uma pessoa | `privacidade.py` |
| **Vazamento por diferença** | Descobrir um número escondido subtraindo dois números visíveis | Etapa 5 |
| **`json_script`** | Jeito seguro de passar dados do Python para o JavaScript | Gráficos (etapa 1) |
| **`<dialog>`** | Janela de confirmação nativa do navegador, já acessível | Modal (etapa 1) |
| **Migração** | O "roteiro" que o Django gera para mudar as tabelas do banco | Etapas 3 e 4 |
| **Seed** | Comando que coloca no banco os dados iniciais (como as perguntas) | Etapa 4 |
| **Mediana** | O valor do meio: não muda quando aparece um valor absurdo | Tempo típico (etapa 3) |
| **NPS** | % de notas 9 e 10 menos % de notas 0 a 6; vai de -100 a 100 | Etapa 5 |

---

## 🐞 Achado registrado (fora destas etapas)

| Achado | Onde | O que fazer depois |
|---|---|---|
| O filtro **"Mês" não tem data de fim**: escolher março mostra tudo de março **até hoje** | `painel/metricas.py`, função `inicio_do_periodo` e `_no_periodo` | Uma tarefa pequena separada: passar um `fim` para `_no_periodo` e um teste com uma tentativa de abril que não pode entrar em março |

## ❓ Pendente com a coordenação

- [ ] Revisar as **7 perguntas** da avaliação no `seed_avaliacao.py` (etapa 4) **antes da primeira turma real**. Elas foram propostas para esta spec, e não vieram da escola.

---

## ✅ Quando o dashboard está pronto

- [ ] As 5 etapas feitas, nesta ordem, com o ponto de encontro de cada uma conferido
- [ ] `python manage.py test` com **137 testes** (135 sem a PRE-03)
- [ ] `python manage.py makemigrations --check --dry-run` responde `No changes detected`
- [ ] As telas conferidas no navegador em tela de computador e de celular (DevTools, 375px)
- [ ] Na máquina de quem hospeda: `python manage.py migrate` e `python manage.py seed_avaliacao` rodados
