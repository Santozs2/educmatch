# EducMatch

Plataforma de matching educacional — conecta estudantes a cursos e conteúdos com base em perfil e interesses.

## Estrutura

- `EducMatch/` — Backend Django (API, autenticação, catálogo, quiz)
- `frontend/` — Frontend React + Vite + TypeScript + Tailwind
- `docs/` — Documentação do projeto

## Como rodar

### Backend
```bash
cd EducMatch
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requeriments.txt
python manage.py migrate
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev        # dev server
npm run typecheck  # TypeScript check
npm run build      # produção
npm run preview    # preview do build
```

## Tecnologias

- **Backend:** Python, Django, SQLite (dev), REST
- **Frontend:** React 19, Vite, TypeScript, Tailwind CSS v4, React Router
- **Devops:** Git, pnpm/npm

## Contribuindo

1. Crie uma branch
2. Rode `npm run typecheck` e `npm run build` no front
3. Commit com mensagem clara
4. Abra PR para `main`
