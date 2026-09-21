export const horas = (h: number) => `${h} ${h === 1 ? 'hora' : 'horas'}`

export const porcentagem = (score: number) => `${Math.round(score * 100)}%`

export const dataCurta = (iso: string) =>
  new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })