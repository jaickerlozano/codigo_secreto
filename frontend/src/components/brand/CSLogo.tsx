import logoImg from '@/assets/logo-codigo-secreto.webp'

interface LogoBadgeProps {
  size?: number
}

export function LogoBadge({ size = 44 }: LogoBadgeProps) {
  return (
    <img
      src={logoImg}
      alt="Código Secreto logo"
      width={size}
      height={size}
      className="rounded-full object-cover flex-shrink-0"
      style={{ boxShadow: 'var(--shadow-glow-brand)' }}
    />
  )
}

interface CSLogoProps {
  onClick?: () => void
}

export function CSLogo({ onClick }: CSLogoProps) {
  const inner = (
    <span className="flex items-center gap-2.5">
      <LogoBadge size={40} />
      <span className="hidden sm:flex flex-col">
        <span className="text-[14px] font-extrabold text-foreground leading-none tracking-wider uppercase">
          Código Secreto
        </span>
        <span className="text-[9px] font-bold tracking-[0.28em] leading-none mt-0.5 text-neon-magenta-500">
          xxx · tienda íntima
        </span>
      </span>
    </span>
  )

  return onClick ? (
    <button
      type="button"
      onClick={onClick}
      className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-xl"
      aria-label="Código Secreto — Inicio"
    >
      {inner}
    </button>
  ) : (
    <div>{inner}</div>
  )
}
