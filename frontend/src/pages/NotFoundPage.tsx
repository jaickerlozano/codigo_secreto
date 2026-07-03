import { motion } from 'motion/react'
import { Link } from 'react-router'
import { Home, Search } from 'lucide-react'

export function NotFoundPage() {
  return (
    <main
      id="main-content"
      className="flex min-h-[80vh] flex-col items-center justify-center px-4 py-20 text-center"
    >
      <div className="pointer-events-none absolute inset-0" aria-hidden="true">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-neon-magenta-500/8 rounded-full blur-[180px]" />
        <div className="absolute bottom-1/4 right-1/4 w-72 h-72 bg-neon-violet-500/8 rounded-full blur-[120px]" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
        className="relative z-10 w-full max-w-md"
      >
        <h1
          className="mb-2 text-[120px] font-black leading-none tracking-tighter text-transparent sm:text-[160px]"
          style={{
            background: 'var(--gradient-brand)',
            WebkitBackgroundClip: 'text',
            backgroundClip: 'text',
            textShadow: 'var(--shadow-glow-brand-sm)',
          }}
          aria-label="Error 404"
        >
          404
        </h1>

        <p className="mb-3 text-2xl font-extrabold uppercase tracking-wide text-foreground">
          Página no encontrada
        </p>

        <p className="mx-auto mb-10 max-w-xs text-sm leading-relaxed text-muted-foreground">
          Esta página se perdió en el placer... pero no te vayas con las manos
          vacías. Tenemos mucho por explorar.
        </p>

        <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
          <Link
            to="/"
            className="inline-flex items-center justify-center gap-2 rounded-xl px-8 py-4 text-sm font-bold uppercase tracking-wide text-background transition-all hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            style={{
              background: 'var(--gradient-brand)',
              boxShadow: 'var(--shadow-glow-brand)',
            }}
          >
            <Home size={16} aria-hidden="true" />
            Volver al inicio
          </Link>

          <Link
            to="/category/todos"
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-neon-magenta/40 bg-transparent px-8 py-4 text-sm font-bold uppercase tracking-wide text-neon-magenta transition-all hover:border-neon-magenta hover:bg-neon-magenta/8 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Search size={16} aria-hidden="true" />
            Explorar productos
          </Link>
        </div>
      </motion.div>
    </main>
  )
}
