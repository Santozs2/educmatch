import { QueryClient } from '@tanstack/react-query'
import { ErroApi } from './api'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      retry: (falhas, erro) => !(erro instanceof ErroApi && erro.status < 500) && falhas < 1,
    },
  },
})