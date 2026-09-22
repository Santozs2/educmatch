import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './api'
import type { Curso, EnvioQuiz, Interesse, Questao, TentativaResumo } from './tipos'

export const chaves = {
  questoes: ['quiz', 'questoes'] as const,
  tentativa: (id: number) => ['quiz', 'tentativa', id] as const,
  curso: (id: number) => ['catalogo', 'curso', id] as const,
  eu: ['auth', 'eu'] as const,
  interesses: ['conta', 'interesses'] as const,
  tentativas: ['conta', 'tentativas'] as const,
}

export function idDaUrl(valor: string | null | undefined): number | null {
  const numero = Number(valor)
  return Number.isInteger(numero) && numero > 0 ? numero : null
}

export function useInteresses(ativo = true) {
  return useQuery({
    queryKey: chaves.interesses,
    queryFn: () => api<Interesse[]>('/interesses/'),
    enabled: ativo,
  })
}

export function useRemoverInteresse() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api<void>(`/interesses/${id}/`, { method: 'DELETE' }),
    onMutate: async (id) => {
      await cliente.cancelQueries({ queryKey: chaves.interesses })
      const antes = cliente.getQueryData<Interesse[]>(chaves.interesses)
      cliente.setQueryData<Interesse[]>(chaves.interesses, (lista) => lista?.filter((item) => item.id !== id))
      return { antes }
    },
    onError: (_erro, _id, contexto) => cliente.setQueryData(chaves.interesses, contexto?.antes),
    onSettled: () => cliente.invalidateQueries({ queryKey: chaves.interesses }),
  })
}

export function useMinhasTentativas() {
  return useQuery({
    queryKey: chaves.tentativas,
    queryFn: () => api<TentativaResumo[]>('/tentativas/'),
  })
}

export function useCriarInteresse() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (corpo: { curso: number; tentativa: number | null }) =>
      api<Interesse>('/interesses/', { method: 'POST', body: JSON.stringify(corpo) }),
    onSuccess: () => cliente.invalidateQueries({ queryKey: chaves.interesses }),
  })
}

export function useQuestoes() {
  return useQuery({
    queryKey: chaves.questoes,
    queryFn: () => api<Questao[]>('/quiz/questoes/'),
    staleTime: Infinity, 
  })
}

export function useTentativa(id: number | null) {
  return useQuery({
    queryKey: chaves.tentativa(id ?? 0),
    queryFn: () => api<TentativaResumo>(`/quiz/tentativas/${id}/`),
    enabled: id !== null,
    staleTime: Infinity,
  })
}

export function useCurso(id: number | null, inicial?: Curso) {
  return useQuery({
    queryKey: chaves.curso(id ?? 0),
    queryFn: () => api<Curso>(`/catalogo/cursos/${id}/`),
    enabled: id !== null,
    placeholderData: inicial,
  })
}

export function useEnviarQuiz() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (corpo: EnvioQuiz) =>
      api<TentativaResumo>('/quiz/tentativas/', { method: 'POST', body: JSON.stringify(corpo) }),
    onSuccess: (tentativa) => {
      cliente.setQueryData(chaves.tentativa(tentativa.tentativa_id), tentativa)
    },
  })
}