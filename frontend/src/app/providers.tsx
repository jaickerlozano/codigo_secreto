import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { ErrorBoundary } from 'react-error-boundary'
import { RouterProvider, type DataRouter } from 'react-router'

import { ErrorFallback } from '@/components/ui/ErrorFallback'
import { createAppRouter } from '@/app/router'
import { queryClient } from '@/lib/query-client'

const client = queryClient()

interface ProvidersProps {
  children?: ReactNode
  router?: DataRouter
}

export function Providers({ children, router }: ProvidersProps) {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <QueryClientProvider client={client}>
        {children}
        <RouterProvider router={router ?? createAppRouter()} />
      </QueryClientProvider>
    </ErrorBoundary>
  )
}
