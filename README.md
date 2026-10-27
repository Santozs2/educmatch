# EducMatch

Plataforma de orientação educacional: o aluno responde um quiz de perfil e recebe
uma recomendação de cursos técnicos, com uma explicação em linguagem natural.
Depois do curso, a escola coleta a avaliação da turma pelo mesmo sistema.

Projeto de TCC, em produção no SENAI São José do Rio Preto (CFP 8.01 Antonio Devisate).

Aplicação Django única, renderizada no servidor — templates mais CSS e JavaScript
estáticos, sem build step. Não existe SPA: o front em React foi removido e as telas
vivem em `backend/templates/` e nos `templates/` de cada app.

## Como funciona a recomendação

São duas camadas, e a segunda nunca é obrigatória:

1. **Engine (`quiz/engine.py`)** — determinística. As respostas viram um vetor de
   pesos por área, comparado por **similaridade de cosseno** com o vetor de cada
   curso. Saem os 5 cursos mais parecidos (`QUIZ_RECOMENDACAO_LIMIT`), cada um com
   `rank_engine` e as 3 áreas que mais pesaram na escolha, mais a diferença entre
   1º e 2º, uma banda de confiança e o `tie_set` (os cursos empatados dentro de
   `EMPATE = 0.02`).
2. **Entrega (`quiz/delivery.py`)** — opcional. Manda um payload **sem dados
   pessoais** para uma LLM, que escreve a explicação e pode reordenar a lista —
   mas só promove ao 1º lugar um curso que já esteja no `tie_set`. A resposta passa
   por validação de contrato (`quiz/serializers.py`); se falhar, estourar o timeout
   ou o provedor cair, o resultado da engine é entregue como está
   (`used_fallback=True`).

Cada tentativa guarda o que aconteceu — `llm_model`, `prompt_version`,
`latency_ms`, `tokens_in`/`tokens_out`, `used_fallback`, `diverged`, `cache_hit` —
para a análise do TCC. `LLM_ENABLED=0` desliga a camada de IA por completo.

Quando o provedor falha, uma pausa de `LLM_PAUSA` segundos é gravada no cache: os
próximos alunos vão direto para a engine em vez de esperar o timeout cada um.

## Estrutura

```
educmatch/
├─ backend/
│  ├─ core/        settings, rotas raiz e testes de infraestrutura
│  ├─ quiz/        questões, tentativas, engine de cosseno, camada de LLM (quiz/llm/)
│  ├─ catalogo/    áreas, cursos e os pesos que ligam um ao outro
│  ├─ accounts/    usuário customizado, login/cadastro, lista de interesse
│  ├─ avaliacao/   avaliação de fim de curso, respondida por link público
│  ├─ painel/      telas da coordenação: métricas, cursos, links, avaliações
│  ├─ templates/   base.html, componentes/ e telas do quiz
│  ├─ static/      css/ e js/ por tela
│  ├─ scripts/     carga_turma.py (teste de carga)
│  └─ startup.sh   inicialização no Azure
└─ docs/
   ├─ apresentacao/  material da banca (engine, ia, contratos, backend, frontend)
   │  └─ mvt.md      arquitetura MVT: o caminho de uma requisição pelas 3 camadas
   ├─ experimento/   CSVs do experimento engine x LLM
   ├─ specs/         plano e passo a passo de cada fase
   └─ DER.png        modelo de dados
```

## Como rodar

Pré-requisitos: Python 3.12+ e MySQL com o banco `educmatch` criado.

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # ajuste DB_USER e DB_PASSWORD para o seu MySQL
python manage.py migrate
python manage.py createcachetable
python manage.py seed            # áreas, cursos e questões de uma vez
python manage.py seed_avaliacao  # perguntas da avaliação de fim de curso
python manage.py runserver       # http://localhost:8000
```

Confira o catálogo pelo número: `12` áreas, `20` cursos, `73` pesos.

Para entrar no painel é preciso um usuário staff: `python manage.py createsuperuser`.

### Configuração (`backend/.env`)

Tudo que muda de uma máquina para outra vem de variável de ambiente. O
`core/settings.py` lê o `backend/.env` sozinho; os nomes estão em
`backend/.env.example`. O `.env` **nunca** vai para o Git.

| Grupo | Variáveis |
| --- | --- |
| Django | `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS` |
| Banco | `DB_ENGINE` (`mysql` padrão, ou `sqlite`), `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` |
| Escola | `ESCOLA_NOME`, `ESCOLA_ENDERECO`, `ESCOLA_TELEFONE` — aparecem nas telas |
| LLM | `LLM_ENABLED`, `LLM_PROVIDER` (`fake`, `gemini`, `openai_compat`), `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`, `LLM_TIMEOUT`, `LLM_PROMPT_VERSION`, `LLM_PAUSA` |

O provedor `fake` responde sem rede nenhuma: é o que os testes usam e serve para
desenvolver a tela de resultado sem gastar cota.

### Tabelas de fuso do MySQL (uma vez por máquina)

O projeto usa `TIME_ZONE = "America/Sao_Paulo"`, e o MySQL vem sem as tabelas de
fuso: sem elas, todo filtro por data do painel volta vazio, sem erro. Baixe o
pacote POSIX em https://dev.mysql.com/downloads/timezones.html e rode:

```bash
mysql -u root -p mysql < timezone_posix.sql
```

O teste `python manage.py test core` diz se deu certo.

## Rotas

### Aluno

| Rota | O que é |
| --- | --- |
| `/` | início do quiz |
| `/questionario/<token>/` | acesso ao questionário pelo link gerado no painel |
| `/resultado/<id>/` | resultado com os cursos recomendados |
| `/cursos/<id>/` | detalhe do curso |
| `/entrar/`, `/cadastro_usuario/`, `/logout/` | conta |
| `/meus-testes/`, `/meu-perfil/`, `/lista_interesse/` | área do aluno |
| `/avaliacao/<token>/` | avaliação de fim de curso (link público, sem login) |

### Coordenação (staff)

| Rota | O que é |
| --- | --- |
| `/painel/` | visão geral |
| `/painel/quiz/` | métricas do quiz |
| `/painel/cursos/` | catálogo: editar curso, criar área |
| `/painel/links/` | gerar e fechar links de questionário |
| `/painel/interesse/` | quem marcou interesse em quais cursos |
| `/painel/avaliacoes/` | links de avaliação por curso e turma |
| `/painel/avaliacoes/resultados/` | resultados, com exportação em `.csv` |
| `/quiz/dashboard/` | endereço antigo: redireciona para `/painel/` |
| `/admin/` | admin do Django |

## Privacidade

O payload que vai para a LLM não leva nome, e-mail nem id de usuário — só o vetor
de áreas e os cursos candidatos.

O painel tem supressão k-anônima implementada em `painel/privacidade.py`, que
esconde o número de qualquer célula com menos de `k` ocorrências (a linha
continua na tabela, para que a omissão não vaze o valor). Por decisão do grupo em
01/10/2026 ela está **desligada** — `K_MINIMO = 0`. Para religar, volte a
constante para `5`.

## Testes

```bash
cd backend
python manage.py test
```

A suíte cobre a engine de recomendação e a camada de LLM (`quiz/tests/`), as rotas
web e a lista de interesse (`accounts/tests/`), a avaliação de fim de curso
(`avaliacao/tests/`), as métricas e telas do painel (`painel/tests/`) e o fuso do
banco (`core/tests.py`).

Comandos de apoio:

```bash
python manage.py testar_llm        # checa o provedor configurado no .env
python manage.py medir_empate      # calibra o limiar de empate da engine
python manage.py experimento_ia    # roda N perfis na engine e na LLM e grava um CSV
python scripts/carga_turma.py      # uma turma inteira enviando o quiz ao mesmo tempo
```

O `experimento_ia` roda cada perfil numa transação desfeita: nada fica no banco.
Os CSVs já gerados estão em `docs/experimento/`.

## Deploy

App Service Linux no plano gratuito F1 (`rg-educmatch` / `educmatch-7249`),
em https://educmatch-7249.azurewebsites.net.

O deploy é automático: `.github/workflows/deploy.yml` publica a cada merge na
`main`, e só se os testes de `test.yml` passarem. O pacote leva o commit dentro,
em `backend/VERSAO`.

- O Oryx procura o `requirements.txt` na raiz; o da raiz só inclui o de `backend/`.
- O comando de inicialização é `bash backend/startup.sh`, que roda migrações,
  seeds e `collectstatic` a cada boot e sobe o gunicorn com worker `gthread`
  (2 workers x 8 threads: a chamada à LLM é espera de rede, e com threads um
  worker atende outros alunos enquanto espera).
- Em produção o banco é SQLite em `/home/data/educmatch.sqlite3`
  (`DB_ENGINE=sqlite`), já que o MySQL gerenciado não tem camada gratuita
  permanente.
- Rollback: Actions -> deploy -> Run workflow, informando a tag em `versao`.
- Publicar a `main` na mão:
  `az webapp deployment source sync -g rg-educmatch -n educmatch-7249`

## Tecnologias

- Python 3.12, Django 5.2 LTS
- MySQL em desenvolvimento (`mysqlclient`), SQLite em produção
- Templates Django, CSS e JavaScript sem build step
- gunicorn e whitenoise em produção
- `djangorestframework` continua instalado, mas nenhuma rota de API está exposta hoje

## Contribuindo

1. Crie uma branch a partir de `main` (uma fase do plano = um PR)
2. Antes do PR: `python manage.py test` em `backend/`
3. Commit com mensagem clara (Conventional Commits)
4. Abra PR para `main`
