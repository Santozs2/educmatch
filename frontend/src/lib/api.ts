const BASE = '/api/v1'

export class ErroApi extends Error {
  constructor(
    public status: number,
    public corpo: unknown,
    mensagem: string,
  ) {
    super(mensagem)
    this.name = 'ErroApi'
  }
}

function lerCookie(nome: string): string {
  const achado = document.cookie.split('; ').find((linha) => linha.startsWith(`${nome}=`))
  return achado ? decodeURIComponent(achado.slice(nome.length + 1)) : ''
}

function mensagemDeErro(status: number, corpo: any): string {
  if (corpo?.detail) return corpo.detail
  if (status === 400 && corpo && typeof corpo === 'object') return 'Confira os campos destacados.'
  if (status === 401) return 'Você precisa entrar para continuar.'
  if (status === 403) return 'Você não tem permissão para isso.'
  if (status === 404) return 'Não encontramos o que você procura.'
  if (status >= 500) return 'O servidor falhou. Tente de novo em instantes.'
  return 'Não foi possível concluir a ação.'
}

export async function api<T>(caminho: string, init: RequestInit = {}): Promise<T> {
  const metodo = (init.method ?? 'GET').toUpperCase()
  const escreve = metodo !== 'GET' && metodo !== 'HEAD'

  const resposta = await fetch(`${BASE}${caminho}`, {
    ...init,
    method: metodo,
    credentials: 'include', // sem isto o cookie de sessão não viaja
    headers: {
      'Content-Type': 'application/json',
      ...(escreve ? { 'X-CSRFToken': lerCookie('csrftoken') } : {}),
      ...init.headers,
    },
  })

  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => null)
    throw new ErroApi(resposta.status, corpo, mensagemDeErro(resposta.status, corpo))
  }
  if (resposta.status === 204) return null as T
  return resposta.json() as Promise<T>
}

export const garantirCsrf = () => api<void>('/auth/csrf/')
export function errosDeCampo(erro: unknown): Record<string, string> {
  if (!(erro instanceof ErroApi) || erro.status !== 400) return {}
  if (!erro.corpo || typeof erro.corpo !== 'object') return {}
  const saida: Record<string, string> = {}
  for (const [campo, valor] of Object.entries(erro.corpo as Record<string, unknown>)) {
    if (campo === 'detail') continue
    saida[campo] = Array.isArray(valor) ? String(valor[0]) : String(valor)
  }
  return saida
}