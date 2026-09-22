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
python manage.py migrate
python manage.py seed_areas && python manage.py seed_cursos && python manage.py seed_questoes
python manage.py runserver      # http://localhost:8000
```

As credenciais do banco ficam em `core/settings.py`; veja `docs/specs/passo-a-passo-bk-01-bk-08.md` (BK-08) para movê-las para variáveis de ambiente.

### Rotas principais

| Rota | O que é |
| --- | --- |
| `/` | início do quiz |
| `/questionario/<token>/` | acesso ao questionário por link |
| `/resultado/<id>/` | resultado com os cursos recomendados |
| `/quiz/dashboard/` | dashboard e geração de link |
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
