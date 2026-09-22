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
  curso: Curso
  explicacao: { top_areas: AreaExplicada[] }
}

export interface TentativaResumo {
  tentativa_id: number
  criado_em: string
  respondido_por: string
  confidence_band: 'alta' | 'media' | 'baixa'
  principal: Recomendacao | null
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
  rank_snapshot: number | null
  era_principal: boolean
}

export interface RespostaEnviada {
  questao: number
  alternativa: number
}

export interface EnvioQuiz {
  respondido_por: string
  questionario_link: string | null
  respostas: RespostaEnviada[]
}

export interface DadosCadastro {
  nome: string
  email: string
  senha: string
}