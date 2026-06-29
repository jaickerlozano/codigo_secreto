export function LoadingSpinner() {
  return (
    <div className="flex min-h-[200px] items-center justify-center" role="status" aria-live="polite">
      <div className="h-10 w-10 animate-spin rounded-full border-4 border-base-600 border-t-neon-cyan-500" />
      <span className="sr-only">Cargando...</span>
    </div>
  )
}
