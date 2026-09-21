import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { ButtonPrimary, ButtonGhost } from '../../components/ui/Button'
import { useSessao } from '../../lib/sessao'

export function Welcome() {
  const navegar = useNavigate()
  const { logado, definirNome } = useSessao()
  const [nome, setNome] = useState('')

  const comecar = () => {
    definirNome(nome.trim())
    navegar('/quiz')
  }

  return (
    <main className="flex-1 max-w-[800px] w-full mx-auto p-5 sm:p-8 flex flex-col">
      {}
    </main>
  )
}