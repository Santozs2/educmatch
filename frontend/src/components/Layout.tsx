import { Outlet } from 'react-router-dom'
import { Header } from './Header'

export function Layout({ semNav = false }: { semNav?: boolean }) {
  return (
    <div className="font-sans text-ink-900 selection:bg-red-100 selection:text-red-900 min-h-screen flex flex-col">
      <Header semNav={semNav} />
      <Outlet />
    </div>
  )
}