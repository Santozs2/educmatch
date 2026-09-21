import { createBrowserRouter } from 'react-router-dom'
import { Layout } from './components/Layout'

import { Welcome } from './features/quiz/Welcome'
import { Wizard } from './features/quiz/Wizard'
import { Resultado } from './features/quiz/Resultado'
import { DetalheCurso } from './features/quiz/DetalheCurso'
import { Entrar } from './features/conta/Entrar'
import { Cadastro } from './features/conta/Cadastro'
import { ListaInteresse } from './features/conta/ListaInteresse'
import { Perfil } from './features/conta/Perfil'
import { Historico } from './features/conta/Historico'
import { Dashboard } from './features/painel/Dashboard'
import { Questionario } from './features/pesquisa/Questionario'
import { Obrigado } from './features/pesquisa/Obrigado'
import { NaoEncontrado } from './components/NaoEncontrado'

export const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: '/', element: <Welcome /> },
      { path: '/quiz', element: <Wizard /> },
      { path: '/resultado/:id', element: <Resultado /> },
      { path: '/curso/:id', element: <DetalheCurso /> },
      { path: '/entrar', element: <Entrar /> },
      { path: '/cadastro', element: <Cadastro /> },
      { path: '/meus-interesses', element: <ListaInteresse /> },
      { path: '/meu-perfil', element: <Perfil /> },
      { path: '/meus-testes', element: <Historico /> },
      { path: '/painel', element: <Dashboard /> },
      { path: '*', element: <NaoEncontrado /> },
    ],
  },
  {
    element: <Layout semNav />,
    children: [
      { path: '/questionario/obrigado', element: <Obrigado /> },
      { path: '/questionario/:token', element: <Questionario /> },
    ],
  },
])