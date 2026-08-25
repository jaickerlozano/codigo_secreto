import { zodResolver } from '@hookform/resolvers/zod'
import { AlertCircle, ArrowRight } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { chileanMobilePhoneSchema } from '../../schemas/checkout.schema'

const profilePhoneSchema = z.object({ phone: chileanMobilePhoneSchema })
type ProfilePhoneSchema = z.infer<typeof profilePhoneSchema>

interface StepProfilePhoneProps {
  onSubmit: (phone: string) => Promise<void>
}

export function StepProfilePhone({ onSubmit }: StepProfilePhoneProps) {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<ProfilePhoneSchema>({
    resolver: zodResolver(profilePhoneSchema),
    defaultValues: { phone: '' },
  })

  return (
    <fieldset>
      <legend className="mb-3 text-xl font-extrabold uppercase tracking-wide text-foreground">Completa tu teléfono</legend>
      <p className="mb-6 text-sm text-muted-foreground">Necesitamos un teléfono móvil chileno para coordinar la entrega. Lo guardaremos en tu perfil.</p>
      <form onSubmit={handleSubmit(async ({ phone }) => onSubmit(phone))} className="space-y-4" noValidate>
        <div>
          <label htmlFor="profile-phone" className="mb-2 block text-sm font-semibold text-foreground">Teléfono <span className="text-neon-magenta" aria-label="requerido">*</span></label>
          <input id="profile-phone" type="tel" autoComplete="tel" placeholder="+56 9 XXXX XXXX" aria-required="true" aria-invalid={!!errors.phone} className={`w-full rounded-xl border bg-secondary px-4 py-3 text-sm text-foreground placeholder-muted-foreground outline-none transition-all focus:ring-1 ${errors.phone ? 'border-destructive focus:border-destructive focus:ring-destructive/40' : 'border-base-600 focus:border-neon-magenta focus:ring-neon-magenta/40'}`} {...register('phone')} />
          {errors.phone && <p className="mt-2 flex items-center gap-1 text-xs text-destructive" role="alert"><AlertCircle size={11} aria-hidden="true" /> {errors.phone.message}</p>}
        </div>
        <button type="submit" disabled={isSubmitting} className="flex min-h-12 w-full items-center justify-center gap-2 rounded-xl py-3.5 text-sm font-bold uppercase tracking-wide text-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-40" style={{ background: 'var(--gradient-brand)' }}>
          {isSubmitting ? 'Guardando...' : <>Siguiente <ArrowRight size={15} aria-hidden="true" /></>}
        </button>
      </form>
    </fieldset>
  )
}
