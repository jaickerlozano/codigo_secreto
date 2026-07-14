import { zodResolver } from '@hookform/resolvers/zod'
import { AlertCircle, ArrowRight, Shield } from 'lucide-react'
import { useForm } from 'react-hook-form'

import { contactSchema, type ContactSchema } from '../../schemas/checkout.schema'

interface StepContactProps {
  defaultValues: ContactSchema
  onSubmit: (data: ContactSchema) => void
}

export function StepContact({ defaultValues, onSubmit }: StepContactProps) {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<ContactSchema>({
    resolver: zodResolver(contactSchema),
    defaultValues,
  })

  const isGuest = watch('isGuest')

  return (
    <fieldset>
      <legend className="mb-6 text-xl font-extrabold uppercase tracking-wide text-foreground">
        Datos de contacto
      </legend>

      <div className="mb-6 grid grid-cols-2 gap-2 rounded-2xl bg-secondary p-1">
        {[
          { label: 'Continuar como invitado', value: true },
          { label: 'Iniciar sesión', value: false },
        ].map(({ label, value }) => (
          <button
            key={label}
            type="button"
            onClick={() => setValue('isGuest', value)}
            className={`rounded-xl py-3 text-[13px] font-bold uppercase tracking-wide transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
              isGuest === value
                ? 'text-background'
                : 'text-muted-foreground hover:text-foreground'
            }`}
            style={isGuest === value ? { background: 'var(--gradient-brand)' } : undefined}
            aria-pressed={isGuest === value}
          >
            {label}
          </button>
        ))}
      </div>

      {isGuest && (
        <div className="mb-5 flex items-start gap-2.5 rounded-xl border border-neon-cyan/15 bg-neon-cyan/6 p-3.5">
          <Shield
            size={13}
            className="mt-0.5 shrink-0 text-neon-cyan"
            aria-hidden="true"
          />
          <p className="text-xs text-neon-cyan">
            No es necesario crear una cuenta. Solo usamos tu email para
            confirmar el pedido.
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <div>
          <label
            htmlFor="contact-name"
            className="mb-2 block text-sm font-semibold text-foreground"
          >
            Nombre completo{' '}
            <span className="text-neon-magenta" aria-label="requerido">
              *
            </span>
          </label>
          <input
            id="contact-name"
            type="text"
            autoComplete="name"
            placeholder="Tu nombre"
            className={`w-full rounded-xl border bg-secondary px-4 py-3 text-sm text-foreground placeholder-muted-foreground outline-none transition-all focus:ring-1 ${
              errors.name
                ? 'border-destructive focus:border-destructive focus:ring-destructive/40'
                : 'border-base-600 focus:border-neon-magenta focus:ring-neon-magenta/40'
            }`}
            aria-required="true"
            aria-invalid={!!errors.name}
            {...register('name')}
          />
          {errors.name && (
            <p className="mt-2 flex items-center gap-1 text-xs text-destructive" role="alert">
              <AlertCircle size={11} aria-hidden="true" /> {errors.name.message}
            </p>
          )}
        </div>

        <div>
          <label
            htmlFor="contact-email"
            className="mb-2 block text-sm font-semibold text-foreground"
          >
            Email{' '}
            <span className="text-neon-magenta" aria-label="requerido">
              *
            </span>
          </label>
          <input
            id="contact-email"
            type="email"
            autoComplete="email"
            placeholder="tu@email.com"
            className={`w-full rounded-xl border bg-secondary px-4 py-3 text-sm text-foreground placeholder-muted-foreground outline-none transition-all focus:ring-1 ${
              errors.email
                ? 'border-destructive focus:border-destructive focus:ring-destructive/40'
                : 'border-base-600 focus:border-neon-magenta focus:ring-neon-magenta/40'
            }`}
            aria-required="true"
            aria-invalid={!!errors.email}
            {...register('email')}
          />
          {errors.email && (
            <p className="mt-2 flex items-center gap-1 text-xs text-destructive" role="alert">
              <AlertCircle size={11} aria-hidden="true" /> {errors.email.message}
            </p>
          )}
        </div>

        <div>
          <label
            htmlFor="contact-phone"
            className="mb-2 block text-sm font-semibold text-foreground"
          >
            Teléfono{' '}
            <span className="text-neon-magenta" aria-label="requerido">
              *
            </span>
          </label>
          <input
            id="contact-phone"
            type="tel"
            autoComplete="tel"
            placeholder="+56 9 XXXX XXXX"
            className={`w-full rounded-xl border bg-secondary px-4 py-3 text-sm text-foreground placeholder-muted-foreground outline-none transition-all focus:ring-1 ${
              errors.phone
                ? 'border-destructive focus:border-destructive focus:ring-destructive/40'
                : 'border-base-600 focus:border-neon-magenta focus:ring-neon-magenta/40'
            }`}
            aria-required="true"
            aria-invalid={!!errors.phone}
            {...register('phone')}
          />
          {errors.phone && (
            <p className="mt-2 flex items-center gap-1 text-xs text-destructive" role="alert">
              <AlertCircle size={11} aria-hidden="true" /> {errors.phone.message}
            </p>
          )}
        </div>

        <div className="flex gap-3 pt-4">
          <button
            type="submit"
            className="flex flex-1 items-center justify-center gap-2 rounded-xl py-3.5 text-sm font-bold uppercase tracking-wide text-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card"
            style={{ background: 'var(--gradient-brand)' }}
          >
            Siguiente <ArrowRight size={15} aria-hidden="true" />
          </button>
        </div>
      </form>
    </fieldset>
  )
}
