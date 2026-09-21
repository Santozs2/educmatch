# EducMatch

Plataforma de matching educacional — conecta estudantes a cursos técnicos com base no perfil respondido num quiz.

## Estrutura

```
educmatch/
├─ backend/          Django + DRF: API v1, engine de recomendação, admin
│  ├─ core/          settings e rotas do projeto
│  ├─ quiz/          questões, tentativas, engine (cosseno)
│  ├─ catalogo/      áreas e cursos
│  ├─ accounts/      usuário, login, lista de interesse
│  ├─ painel/        métricas agregadas com supressão k-anônima
│  ├─ templates/     front antigo em templates (sai na FE-24)
│  └─ requirements.txt
├─ frontend/         React 19 + Vite + TypeScript + Tailwind 4
│  └─ src/
│     ├─ lib/        cliente HTTP, tipos, queries, sessão
│     ├─ components/ compartilhados (Header, Modal, Toast…)
│     └─ features/   uma pasta por fluxo: quiz, conta, painel, pesquisa
└─ docs/specs/       planos e passo a passo de cada fase
```

## Como rodar

São dois servidores em desenvolvimento. Abra sempre o front em `http://localhost:5173`: o Vite repassa `/api` para o Django.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_areas && python manage.py seed_cursos && python manage.py seed_questoes
python manage.py runserver      # http://localhost:8000
```

O banco é MySQL (`educmatch`). As credenciais vêm de variáveis de ambiente; veja `docs/specs/passo-a-passo-bk-01-bk-08.md` (BK-08).

### Frontend

```bash
cd frontend
pnpm install
pnpm dev          # http://localhost:5173
pnpm typecheck
pnpm build        # gera frontend/dist/
```

## Tecnologias

- **Backend:** Python, Django 5.2 LTS, Django REST Framework, MySQL
- **Frontend:** React 19, Vite, TypeScript, Tailwind CSS 4, React Router, TanStack Query, Recharts
- **Gerenciadores:** pip e pnpm (use só o pnpm no front: o lockfile é `pnpm-lock.yaml`)

## Contribuindo

1. Crie uma branch a partir de `main` (uma fase do plano = um PR)
2. Antes do PR: `pnpm typecheck && pnpm build` em `frontend/` e `python manage.py test` em `backend/`
3. Commit com mensagem clara (Conventional Commits)
4. Abra PR para `main`
