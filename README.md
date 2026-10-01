# EducMatch

Plataforma de matching educacional — conecta estudantes a cursos técnicos com base no perfil respondido num quiz.

Aplicação Django única, renderizada no servidor (templates + CSS/JS estáticos). Não há mais SPA separada: o front em React foi removido e as telas vivem em `backend/templates/`.

## Estrutura

```
educmatch/
├─ backend/
│  ├─ core/         settings e rotas do projeto
│  ├─ quiz/         questões, tentativas, engine de recomendação (cosseno)
│  ├─ catalogo/     áreas e cursos
│  ├─ accounts/     usuário, login/cadastro, lista de interesse
│  ├─ painel/       métricas agregadas com supressão k-anônima
│  ├─ templates/    telas do quiz (base.html, quiz/)
│  ├─ static/       css/style.css e js/quiz.js
│  └─ requirements.txt
└─ docs/specs/      planos e passo a passo de cada fase
```

## Como rodar

Pré-requisitos: Python 3.12+ e MySQL com o banco `educmatch` criado.

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # e ajuste DB_USER e DB_PASSWORD para o seu MySQL
python manage.py migrate
python manage.py createcachetable
python manage.py seed_areas && python manage.py seed_cursos && python manage.py seed_questoes
python manage.py runserver      # http://localhost:8000
```

Confira o catálogo pelo número: `12` áreas, `20` cursos, `73` pesos.

### Configuração (`backend/.env`)

Tudo que muda de uma máquina para outra (chave, `DEBUG`, hosts e banco) vem de variável de ambiente. O `core/settings.py` lê o arquivo `backend/.env` sozinho; os nomes estão em `backend/.env.example`. O `.env` **nunca** vai para o Git.

### Tabelas de fuso do MySQL (uma vez por máquina)

O projeto usa `TIME_ZONE = "America/Sao_Paulo"`, e o MySQL vem sem as tabelas de fuso: sem elas, todo filtro por data do painel volta vazio, sem erro. Baixe o pacote POSIX em https://dev.mysql.com/downloads/timezones.html e rode:

```bash
mysql -u root -p mysql < timezone_posix.sql
```

O teste `python manage.py test core` diz se deu certo.

### Rotas principais

| Rota | O que é |
| --- | --- |
| `/` | início do quiz |
| `/questionario/<token>/` | acesso ao questionário por link |
| `/resultado/<id>/` | resultado com os cursos recomendados |
| `/cursos/<id>/` | detalhe do curso |
| `/painel/` | painel da coordenação (staff), com k-anonimato e geração de link |
| `/quiz/dashboard/` | endereço antigo: redireciona para `/painel/` |
| `/entrar/`, `/cadastro_usuario/` | login e cadastro |
| `/meus-testes/`, `/meu-perfil/`, `/lista_interesse/` | área do aluno |
| `/admin/` | admin do Django |

## Testes

```bash
cd backend
python manage.py test
```

Os testes cobrem o engine de recomendação (`quiz/tests/`), as rotas web, a lista de interesse (`accounts/tests/`) e as métricas do painel (`painel/tests/`).

## Tecnologias

- Python, Django 5.2 LTS, MySQL (`mysqlclient`)
- Templates Django + CSS e JavaScript sem build step
- `djangorestframework` continua instalado, mas nenhuma rota de API está exposta hoje

## Contribuindo

1. Crie uma branch a partir de `main` (uma fase do plano = um PR)
2. Antes do PR: `python manage.py test` em `backend/`
3. Commit com mensagem clara (Conventional Commits)
4. Abra PR para `main`
