import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './api'
import type { Curso, EnvioQuiz, Questao, Tentativa } from './tipos'

export const chaves = {
  questoes: ['quiz', 'questoes'] as const,
  tentativa: (id: number) => ['quiz', 'tentativa', id] as const,
  curso: (id: number) => ['catalogo', 'curso', id] as const,
}

export function idDaUrl(valor: string | null | undefined): number | null {
  const numero = Number(valor)
  return Number.isInteger(numero) && numero > 0 ? numero : null
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
    queryFn: () => api<Tentativa>(`/quiz/tentativas/${id}/`),
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
      api<Tentativa>('/quiz/tentativas/', { method: 'POST', body: JSON.stringify(corpo) }),
    onSuccess: (tentativa) => {
      cliente.setQueryData(chaves.tentativa(tentativa.tentativa_id), tentativa)
    },
  })
}