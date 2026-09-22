import { useNavigate } from 'react-router-dom'
import { ArrowRight, BookOpen, List, Trash2 } from 'lucide-react'
import { Carregando, EstadoErro } from '../../components/Estado'
import { useToast } from '../../components/Toast'
import { horas } from '../../lib/formatters'
import { useInteresses, useRemoverInteresse } from '../../lib/queries'
import { CascaConta } from './CascaConta'

export function ListaInteresse() {
  const navegar = useNavigate()
  const lista = useInteresses()
  const remover = useRemoverInteresse()
  const mostrarToast = useToast()

  const conteudo = () => {
    if (lista.isPending) return <Carregando />
    if (lista.isError) return <EstadoErro titulo="Não deu para abrir sua lista" mensagem={lista.error.message} onTentar={() => lista.refetch()} />
    if (lista.data.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-16 h-16 rounded-full bg-ink-100 flex items-center justify-center mb-4">
            <List size={28} className="text-ink-400" />
          </div>
          <p className="text-ink-600 font-semibold text-lg mb-1">Sua lista está vazia</p>
          <p className="text-ink-400 text-sm">Explore os cursos e manifeste interesse para adicioná-los aqui.</p>
        </div>
      )
    }
    return (
      <ul className="flex flex-col gap-4">
        {lista.data.map(({ id, curso }) => (
          <li key={id} className="bg-white rounded-[12px] border border-line-200 p-4 sm:p-5 flex flex-col gap-4 hover:border-red-200 hover:shadow-md transition-all duration-200">
            <div className="flex flex-col sm:flex-row sm:items-start gap-4">
              <div className="flex-1 min-w-0">
                <h2 className="font-bold text-ink-900 text-lg leading-tight">{curso.nome_curso}</h2>
                <p className="text-ink-600 text-sm mt-1 line-clamp-2">{curso.descricao}</p>
                <div className="flex flex-wrap gap-2 mt-3">
                  <span className="bg-red-100 text-red-900 px-2 py-1 rounded text-xs font-bold uppercase tracking-wide">{curso.area_principal.nome}</span>
                  <span className="bg-white border border-line-200 text-ink-600 px-2 py-1 rounded text-xs font-bold uppercase tracking-wide flex items-center gap-1">
                    <BookOpen size={11} /> {horas(curso.duracao)}
                  </span>
                </div>
              </div>
              <button
                onClick={() => remover.mutate(id, { onSuccess: () => mostrarToast('Curso removido da lista') })}
                className="min-w-[48px] min-h-[48px] flex items-center justify-center text-ink-300 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors active:scale-95 self-start shrink-0"
                aria-label={`Remover ${curso.nome_curso} da lista`}
              >
                <Trash2 size={20} />
              </button>
            </div>
            <div className="border-t border-line-200 pt-3">
              <button onClick={() => navegar(`/curso/${curso.id}`)} className="flex items-center gap-2 text-red-600 font-semibold text-sm hover:text-red-800 hover:underline transition-colors min-h-[44px]">
                <ArrowRight size={16} /> Ver detalhes do curso
              </button>
            </div>
          </li>
        ))}
      </ul>
    )
  }

  return (
    <CascaConta titulo="Minha lista de interesse" subtitulo="Os cursos que você quer conhecer melhor.">
      {remover.isError && <p role="alert" className="mb-4 text-sm font-semibold text-red-700">{remover.error.message} O item voltou para a lista.</p>}
      {conteudo()}
    </CascaConta>
  )
}