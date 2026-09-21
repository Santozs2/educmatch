import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ButtonPrimary } from '../../components/ui/Button'
import { useQuestoes } from '../../lib/queries'
import { iniciarRascunho, lerRascunho } from './rascunho'

export function Welcome() {
  const navegar = useNavigate()
  const [nome, setNome] = useState('')
  const { data: questoes } = useQuestoes()
  const total = questoes?.length

  const comecar = () => {
    iniciarRascunho(nome.trim(), lerRascunho().link)
    navegar('/quiz')
  }

  return (
    <main className="flex-1 max-w-[1440px] w-full mx-auto p-5 sm:p-8 md:p-12 flex flex-col items-center justify-center">
      <div className="max-w-[600px] w-full bg-white rounded-[12px] p-6 sm:p-10 shadow-[0_8px_24px_rgba(16,24,40,0.08)]">
        <h1 className="text-3xl sm:text-4xl font-bold text-red-900 mb-4 leading-tight">
          Descubra o curso certo para o seu perfil
        </h1>
        <p className="text-ink-600 text-[17px] mb-8">
          Responda a {total ?? 'algumas'} perguntas simples sobre o seu jeito de trabalhar e descubra as áreas que mais combinam com você.
        </p>

        <div className="flex flex-wrap gap-3 mb-8">
          <span className="bg-ink-900 text-white px-4 py-1.5 rounded-full text-sm font-semibold flex items-center gap-1 shadow-sm">
            Leva 2 minutos
          </span>
          <span className="bg-white border border-line-200 text-ink-900 px-4 py-1.5 rounded-full text-sm font-semibold flex items-center gap-1 shadow-sm">
            Sem cadastro
          </span>
          {total !== undefined && (
            <span className="bg-white border border-line-200 text-ink-900 px-4 py-1.5 rounded-full text-sm font-semibold flex items-center gap-1 shadow-sm">
              {total} perguntas
            </span>
          )}
        </div>

        <form onSubmit={(evento) => { evento.preventDefault(); comecar() }}>
          <div className="mb-8">
            <label htmlFor="nome" className="block font-semibold text-ink-900 mb-2">Seu nome (opcional)</label>
            <input
              id="nome"
              type="text"
              autoComplete="given-name"
              maxLength={100}
              value={nome}
              onChange={(evento) => setNome(evento.target.value)}
              className="w-full border-2 border-line-200 rounded-[8px] p-3 min-h-[48px] text-[17px] text-ink-900 focus:border-red-600 focus:ring-0 outline-none"
            />
          </div>
          <ButtonPrimary type="submit">Começar</ButtonPrimary>
        </form>

        <p className="text-center text-ink-600 text-sm mt-4">Nenhum dado seu é compartilhado.</p>
      </div>
    </main>
  )
}