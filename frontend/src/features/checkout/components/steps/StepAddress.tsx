import { zodResolver } from '@hookform/resolvers/zod'
import { AlertCircle, ArrowRight, MapPin } from 'lucide-react'
import { useForm } from 'react-hook-form'

import { CHILEAN_REGIONS, COMUNAS_RM } from '@/lib/constants'

import { addressSchema, type AddressSchema } from '../../schemas/checkout.schema'

interface StepAddressProps {
  defaultValues: AddressSchema
  onSubmit: (data: AddressSchema) => void
  onBack: () => void
}

export function StepAddress({
  defaultValues,
  onSubmit,
  onBack,
}: StepAddressProps) {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<AddressSchema>({
    resolver: zodResolver(addressSchema),
    defaultValues,
  })

  const region = watch('region')
  const isRM = region === 'Región Metropolitana'

  const inputClass = (hasError?: boolean) =>
    `w-full rounded-xl border px-4 py-3 text-sm text-foreground outline-none transition-all focus:ring-1 ${
      hasError
        ? 'border-destructive focus:border-destructive focus:ring-destructive/40'
        : 'border-base-600 bg-secondary focus:border-neon-magenta focus:ring-neon-magenta/40'
    }`

  return (
    <fieldset>
      <legend className="mb-6 text-xl font-extrabold uppercase tracking-wide text-foreground">
        Dirección de envío
      </legend>

      <div className="mb-5 flex items-center gap-2.5 rounded-xl bg-secondary p-3.5">
        <MapPin
          size={13}
          className="shrink-0 text-neon-lime"
          aria-hidden="true"
        />
        <p className="text-xs text-muted-foreground">
          Esta dirección es confidencial y solo se usará para tu envío.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <div>
          <label
            htmlFor="address-street"
            className="mb-2 block text-sm font-semibold text-foreground"
          >
            Calle y número{' '}
            <span className="text-neon-magenta" aria-label="requerido">
              *
            </span>
          </label>
          <input
            id="address-street"
            type="text"
            autoComplete="street-address"
            placeholder="Av. Principal 1234"
            className={inputClass(!!errors.address)}
            aria-required="true"
            aria-invalid={!!errors.address}
            {...register('address')}
          />
          {errors.address && (
            <p className="mt-2 text-xs text-destructive" role="alert">
              {errors.address.message}
            </p>
          )}
        </div>

        <div>
          <label
            htmlFor="address-apartment"
            className="mb-2 block text-sm font-semibold text-foreground"
          >
            Depto / Oficina{' '}
            <span className="text-xs font-normal text-muted-foreground">
              (opcional)
            </span>
          </label>
          <input
            id="address-apartment"
            type="text"
            autoComplete="address-line2"
            placeholder="Depto 302"
            className={inputClass()}
            {...register('apartment')}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label
              htmlFor="address-region"
              className="mb-2 block text-sm font-semibold text-foreground"
            >
              Región{' '}
              <span className="text-neon-magenta" aria-label="requerido">
                *
              </span>
            </label>
            <select
              id="address-region"
              className="w-full appearance-none rounded-xl border border-base-600 bg-secondary px-4 py-3 text-sm text-foreground outline-none transition-all focus:border-neon-magenta focus:ring-1 focus:ring-neon-magenta/40"
              aria-required="true"
              {...register('region', {
                onChange: () => setValue('comuna', ''),
              })}
            >
              {CHILEAN_REGIONS.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor="address-comuna"
              className="mb-2 block text-sm font-semibold text-foreground"
            >
              Comuna{' '}
              <span className="text-neon-magenta" aria-label="requerido">
                *
              </span>
            </label>
            {isRM ? (
              <select
                id="address-comuna"
                className={`w-full appearance-none rounded-xl border px-4 py-3 text-sm text-foreground outline-none transition-all focus:ring-1 ${
                  errors.comuna
                    ? 'border-destructive focus:border-destructive focus:ring-destructive/40'
                    : 'border-base-600 bg-secondary focus:border-neon-magenta focus:ring-neon-magenta/40'
                }`}
                aria-required="true"
                aria-invalid={!!errors.comuna}
                {...register('comuna')}
              >
                <option value="">Seleccionar...</option>
                {COMUNAS_RM.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            ) : (
              <input
                id="address-comuna"
                type="text"
                placeholder="Tu comuna"
                className={inputClass(!!errors.comuna)}
                aria-required="true"
                aria-invalid={!!errors.comuna}
                {...register('comuna')}
              />
            )}
            {errors.comuna && (
              <p className="mt-2 text-xs text-destructive" role="alert">
                {errors.comuna.message}
              </p>
            )}
          </div>
        </div>

        <div>
          <label
            htmlFor="address-postal"
            className="mb-2 block text-sm font-semibold text-foreground"
          >
            Código postal{' '}
            <span className="text-xs font-normal text-muted-foreground">
              (opcional)
            </span>
          </label>
          <input
            id="address-postal"
            type="text"
            autoComplete="postal-code"
            placeholder="1234567"
            className={inputClass()}
            {...register('postalCode')}
          />
        </div>

        <div>
          <label
            htmlFor="address-notes"
            className="mb-2 block text-sm font-semibold text-foreground"
          >
            Notas de entrega{' '}
            <span className="text-xs font-normal text-muted-foreground">
              (opcional)
            </span>
          </label>
          <textarea
            id="address-notes"
            rows={3}
            placeholder="Instrucciones adicionales para el repartidor"
            className={`${inputClass()} resize-none`}
            {...register('notes')}
          />
        </div>

        <div className="flex gap-3 pt-4">
          <button
            type="button"
            onClick={onBack}
            className="rounded-xl border border-white/10 px-6 py-3 text-sm font-bold uppercase tracking-wide text-muted-foreground transition-all hover:border-white/20 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            Atrás
          </button>
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
