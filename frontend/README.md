# EducMatch — Frontend

React + Vite + TypeScript + Tailwind CSS v4.

## Scripts

- `npm run dev` — desenvolvimento
- `npm run typecheck` — verificação de tipos
- `npm run build` — build de produção (`tsc --noEmit && vite build`)
- `npm run preview` — preview do build

## Estrutura

- `src/components/` — componentes compartilhados (Header, Layout, Modal, Toast, UI)
- `src/features/` — módulos por área (quiz, conta, painel, pesquisa)
- `src/lib/` — utilidades, API, formatação, sessão
- `src/routes.tsx` — roteamento com React Router

## Configuração

- `vite.config.ts` — Vite + plugin React
- `tsconfig.json` — TypeScript (strict)
- `.gitignore` — `node_modules/`, `dist/`, `.vite/`, `.env`
