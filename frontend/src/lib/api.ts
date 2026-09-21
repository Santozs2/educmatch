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
    credentials: 'include',
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