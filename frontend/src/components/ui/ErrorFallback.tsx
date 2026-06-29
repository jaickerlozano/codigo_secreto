import type { FallbackProps } from 'react-error-boundary'

export function ErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
  return (
    <div role="alert" className="rounded-xl border border-error-500 bg-base-800 p-6 text-center">
      <h2 className="mb-2 text-lg font-semibold text-error-500">Ha ocurrido un error</h2>
      <p className="mb-4 text-base-300">{error instanceof Error ? error.message : 'Error desconocido'}</p>
      <button
        type="button"
        onClick={resetErrorBoundary}
        className="rounded-md bg-neon-cyan-500 px-4 py-2 font-medium text-base-900 transition hover:bg-neon-cyan-400"
      >
        Reintentar
      </button>
    </div>
  )
}
