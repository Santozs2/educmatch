import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  BarChart3, ChevronDown, Contrast, History, List, LogOut, Settings, User, ZoomIn,
} from 'lucide-react'
import { useSessao } from '../lib/sessao'

export function Header({ semNav = false }: { semNav?: boolean }) {
  const [menuAberto, setMenuAberto] = useState(false)
  const navegar = useNavigate()
  const { logado, admin, sair } = useSessao()

  const ir = (rota: string) => {
    setMenuAberto(false)
    navegar(rota)
  }

  return (
    <header className="bg-ink-900 text-white p-4">
      <div className="max-w-[1440px] mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Link to="/" className="font-bold text-xl hover:text-red-100 transition-colors">
            QuizPessoal
          </Link>
          <span className="bg-white/20 text-white text-xs px-2 py-1 rounded-full hidden sm:inline-block">
            Orientação profissional
          </span>
        </div>

        {!semNav && (
          <div className="flex items-center gap-2 sm:gap-4">
            {logado ? (
              <div className="relative">
                <button
                  onClick={() => setMenuAberto((aberto) => !aberto)}
                  aria-expanded={menuAberto}
                  aria-haspopup="menu"
                  className="flex items-center gap-2 rounded-lg border border-white/25 bg-white/10 px-3 py-2 text-sm font-bold text-white transition-colors hover:bg-white/20"
                >
                  <span className="grid h-7 w-7 place-items-center rounded-full bg-red-600 text-xs">
                    {admin ? 'A' : 'M'}
                  </span>
                  <span className="hidden sm:inline">{admin ? 'Administração' : 'Minha conta'}</span>
                  <ChevronDown size={16} className={menuAberto ? 'rotate-180 transition-transform' : 'transition-transform'} />
                </button>

                {menuAberto && (
                  <div role="menu" className="absolute right-0 top-[calc(100%+10px)] z-40 w-60 overflow-hidden rounded-xl border border-line-200 bg-white py-2 text-ink-900 shadow-xl">
                    <button role="menuitem" onClick={() => ir('/meus-interesses')} className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm font-semibold hover:bg-red-50">
                      <List size={17} className="text-red-600" /> Minha lista
                    </button>
                    <button role="menuitem" onClick={() => ir('/meus-testes')} className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm font-semibold hover:bg-red-50">
                      <History size={17} className="text-red-600" /> Meus testes
                    </button>
                    <button role="menuitem" onClick={() => ir('/meu-perfil')} className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm font-semibold hover:bg-red-50">
                      <Settings size={17} className="text-red-600" /> Meu perfil
                    </button>
                    {admin && (
                      <button role="menuitem" onClick={() => ir('/painel')} className="flex w-full items-center gap-3 border-t border-line-200 px-4 py-3 text-left text-sm font-bold hover:bg-red-50">
                        <BarChart3 size={17} className="text-red-600" /> Dashboard
                      </button>
                    )}
                    <button
                      role="menuitem"
                      onClick={() => { setMenuAberto(false); sair(); navegar('/') }}
                      className="flex w-full items-center gap-3 border-t border-line-200 px-4 py-3 text-left text-sm font-semibold text-ink-600 hover:bg-red-50 hover:text-red-700"
                    >
                      <LogOut size={17} /> Sair
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={() => navegar('/entrar')}
                className="flex items-center gap-2 border-2 border-white/30 hover:bg-white/10 text-white px-4 py-2 rounded-lg font-bold transition-all duration-200 text-sm active:scale-95"
              >
                <User size={16} /> <span className="hidden sm:inline">Entrar</span>
              </button>
            )}
          </div>
        )}
      </div>
    </header>
  )
}