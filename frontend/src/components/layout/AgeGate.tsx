import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'motion/react'

import { LogoBadge } from '@/components/brand/CSLogo'

interface AgeGateProps {
  onAccept?: () => void
}

const STORAGE_KEY = 'cs-age-verified'

export function AgeGate({ onAccept }: AgeGateProps) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const verified = window.localStorage.getItem(STORAGE_KEY)
    if (verified !== 'true') {
      setVisible(true)
    }
  }, [])

  const handleAccept = () => {
    window.localStorage.setItem(STORAGE_KEY, 'true')
    setVisible(false)
    onAccept?.()
  }

  const handleExit = () => {
    window.location.href = 'https://www.google.com'
  }

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          key="age-gate"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.35 }}
          className="fixed inset-0 z-[9999] flex items-center justify-center bg-background px-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="age-gate-title"
        >
          <div className="pointer-events-none absolute inset-0" aria-hidden="true">
            <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-neon-magenta-500/8 rounded-full blur-[180px]" />
            <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-neon-violet-500/8 rounded-full blur-[100px]" />
            <div
              className="absolute inset-0"
              style={{ backgroundImage: 'var(--circuit-overlay)', opacity: 0.15 }}
            />
          </div>

          <div className="relative text-center max-w-[360px] w-full">
            <div className="flex justify-center mb-7">
              <div className="relative">
                <div
                  className="absolute inset-0 rounded-full blur-2xl scale-150 opacity-25"
                  style={{ background: 'var(--gradient-brand)' }}
                  aria-hidden="true"
                />
                <LogoBadge size={110} />
              </div>
            </div>

            <h1
              id="age-gate-title"
              aria-label="Bienvenido a Código Secreto"
              className="text-3xl font-extrabold text-foreground mb-2 uppercase tracking-wide"
            >
              Bienvenido a
              <br />
              <span className="text-neon-magenta-500">Código Secreto</span>
            </h1>
            <p className="text-sm text-muted-foreground leading-relaxed mb-8 max-w-xs mx-auto">
              Este sitio contiene productos para adultos. Al continuar confirmas que tienes 18 años
              o más.
            </p>

            <button
              type="button"
              onClick={handleAccept}
              className="w-full py-4 text-sm font-bold text-primary-foreground uppercase tracking-wide rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background transition-all"
              style={{ background: 'var(--gradient-brand)', boxShadow: 'var(--shadow-glow-brand)' }}
            >
              Soy mayor de 18 años — Entrar
            </button>

            <button
              type="button"
              onClick={handleExit}
              className="w-full mt-3 py-3 text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-xl"
            >
              No, salir
            </button>

            <p className="text-[11px] text-muted-foreground mt-5">
              Al entrar aceptas nuestra{' '}
              <button
                type="button"
                className="text-muted-foreground underline hover:text-neon-magenta-500 transition-colors"
              >
                Política de Privacidad
              </button>{' '}
              y{' '}
              <button
                type="button"
                className="text-muted-foreground underline hover:text-neon-magenta-500 transition-colors"
              >
                Términos de Uso
              </button>
              .
            </p>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
