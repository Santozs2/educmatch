export interface Alternativa {
  id: number
  texto: string
  order: number
}

export interface Questao {
  id: number
  texto: string
  order: number
  alternativas: Alternativa[]
}

export interface Area {
  slug: string
  nome: string
}

export interface Curso {
  id: number
  nome_curso: string
  descricao: string
  duracao: number 
  area_principal: Area
}

export interface AreaExplicada {
  area: string
  area_name: string
  contribuicao: number
  percentual: number
}

export interface Recomendacao {
  rank: number
  score: number
  match: number 
  explicacao: { top_areas: AreaExplicada[] }
}

export interface Tentativa {
  tentativa_id: number
  confidence_band: 'alta' | 'media' | 'baixa'
  diferenca: number
  recomendacoes: Recomendacao[]
}

export interface Usuario {
  id: number
  email: string
  username: string
  is_superuser: boolean
}

export interface Interesse {
  id: number
  curso: Curso
  status: 'interessado' | 'contatado' | 'descartado'
  criado_em: string
}