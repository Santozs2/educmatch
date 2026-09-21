const CHAVE = 'educmatch.quiz'

export interface Rascunho {
  nome: string
  passo: number
  respostas: Record<number, number> 
  link: string | null 
}

const VAZIO: Rascunho = { nome: '', passo: 0, respostas: {}, link: null }

export function lerRascunho(): Rascunho {
  try {
    const bruto = sessionStorage.getItem(CHAVE)
    return bruto ? { ...VAZIO, ...JSON.parse(bruto) } : VAZIO
  } catch {
    return VAZIO 
  }
}

export function salvarRascunho(rascunho: Rascunho) {
  try {
    sessionStorage.setItem(CHAVE, JSON.stringify(rascunho))
  } catch {
  }
}

export function iniciarRascunho(nome: string, link: string | null) {
  salvarRascunho({ ...VAZIO, nome, link })
}

export function limparRascunho() {
  try {
    sessionStorage.removeItem(CHAVE)
  } catch { 
  }
}