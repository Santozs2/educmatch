import React from 'react'
import ReactDOM from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'

import { ToastProvider } from './components/Toast'
import { router } from './routes'
import { queryClient } from './lib/query'
import { SessaoProvider } from './lib/sessao'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <SessaoProvider>
        <ToastProvider>
          <RouterProvider router={router} />
        </ToastProvider>
      </SessaoProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)