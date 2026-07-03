import { motion } from 'motion/react'
import { ArrowRight, Clock, Lock, Package, Zap } from 'lucide-react'

import { LogoBadge } from '@/components/brand/CSLogo'

export function HeroSection() {
  return (
    <section
      className="relative flex items-center overflow-hidden"
      style={{ minHeight: '82vh' }}
      aria-label="Inicio"
    >
      <div
        className="pointer-events-none absolute inset-0"
        aria-hidden="true"
      >
        <div
          className="absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage: 'var(--circuit-overlay)',
            backgroundSize: '60px 60px',
          }}
        />
        <div className="absolute top-1/4 left-1/4 h-[500px] w-[500px] rounded-full bg-neon-magenta/10 blur-[160px]" />
        <div className="absolute bottom-1/3 right-1/4 h-96 w-96 rounded-full bg-neon-violet/10 blur-[130px]" />
        <div className="absolute top-1/2 right-1/3 h-64 w-64 rounded-full bg-neon-cyan/8 blur-[100px]" />
      </div>

      <div className="relative z-10 mx-auto grid w-full max-w-6xl items-center gap-12 px-6 py-20 lg:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
        >
          <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-neon-magenta/25 bg-neon-magenta/8 px-4 py-2">
            <Lock
              size={11}
              className="text-neon-magenta"
              aria-hidden="true"
            />
            <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-neon-magenta">
              Envío Discreto · Pago Seguro · 100% Privado
            </span>
          </div>

          <h1 className="mb-5 text-5xl font-extrabold uppercase leading-[1.05] text-foreground sm:text-6xl">
            Bienestar
            <br />
            <span className="bg-gradient-to-r from-neon-magenta via-[#ec4899] to-neon-violet bg-clip-text text-transparent">
              íntimo,
            </span>
            <br />
            entrega discreta.
          </h1>

          <p className="mb-3 text-[17px] font-medium text-muted-foreground">
            Envío mismo día en Santiago · 100% discreto
          </p>
          <p className="mb-9 max-w-lg text-[14px] leading-relaxed text-muted-foreground">
            Selección premium de productos de bienestar íntimo. Compra
            segura, embalaje sin marcas, entrega en tu puerta.
          </p>

          <div className="flex flex-col gap-4 sm:flex-row">
            <a
              href="#catalogo"
              className="inline-flex items-center justify-center gap-2 rounded-xl px-8 py-4 text-[13px] font-bold uppercase tracking-wide text-white transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              style={{
                background: 'var(--gradient-brand)',
                boxShadow: 'var(--shadow-glow-brand)',
              }}
            >
              Ver catálogo{' '}
              <ArrowRight size={15} aria-hidden="true" />
            </a>
            <button
              type="button"
              className="rounded-xl border border-neon-cyan/40 bg-transparent px-8 py-4 text-[13px] font-bold uppercase tracking-wide text-neon-cyan transition-all hover:border-neon-cyan/70 hover:bg-neon-cyan/8 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan"
            >
              Hablar con un asesor
            </button>
          </div>

          <div
            className="mt-9 flex flex-wrap gap-5"
            role="list"
            aria-label="Garantías"
          >
            {[
              { icon: Package, label: 'Empaque 100% discreto' },
              { icon: Lock, label: 'Pago seguro con Webpay' },
              { icon: Zap, label: 'Entrega mismo día' },
              { icon: Clock, label: 'Atención personalizada' },
            ].map(({ icon: Icon, label }) => (
              <div
                key={label}
                className="flex items-center gap-2"
                role="listitem"
              >
                <Icon
                  size={13}
                  className="text-neon-lime"
                  aria-hidden="true"
                />
                <span className="text-[12px] text-muted-foreground">
                  {label}
                </span>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.7, ease: [0.4, 0, 0.2, 1] }}
          className="hidden items-center justify-center lg:flex"
        >
          <div className="relative">
            <div
              className="absolute inset-0 scale-150 rounded-full opacity-20 blur-3xl"
              style={{ background: 'var(--gradient-brand)' }}
              aria-hidden="true"
            />
            <LogoBadge size={300} />
            <motion.div
              animate={{ rotate: 360 }}
              transition={{
                duration: 20,
                repeat: Infinity,
                ease: 'linear',
              }}
              className="absolute inset-[-20px] rounded-full border-2 border-neon-magenta/15"
              aria-hidden="true"
            />
          </div>
        </motion.div>
      </div>

      <div
        className="absolute bottom-8 left-1/2 flex -translate-x-1/2 flex-col items-center gap-1 opacity-30"
        aria-hidden="true"
      >
        <div className="h-8 w-px bg-gradient-to-b from-neon-magenta to-transparent" />
      </div>
    </section>
  )
}
