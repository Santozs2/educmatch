import { Link } from 'react-router-dom'

export function NaoEncontrado() {
  return (
    <main className="flex-1 max-w-[800px] w-full mx-auto p-5 sm:p-8 flex flex-col items-center justify-center text-center">
      <h1 className="text-3xl font-bold text-red-900 mb-3">Página não encontrada</h1>
      <p className="text-ink-600 text-[17px] mb-8">
        O endereço que você abriu não existe ou saiu do ar.
      </p>
      <Link to="/" className="font-bold text-red-600 hover:text-red-700 underline min-h-[48px] flex items-center">
        Voltar para o início
      </Link>
    </main>
  )
}