import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router'

import { createAppRouter } from '@/app/router.tsx'
import '@/styles/globals.css'
import { Providers } from '@/app/providers.tsx'

const router = createAppRouter()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Providers>
      <RouterProvider router={router} />
    </Providers>
  </StrictMode>,
)
