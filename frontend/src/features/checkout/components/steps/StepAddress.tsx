import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowRight, MapPin } from 'lucide-react'
import { Controller, useForm } from 'react-hook-form'

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useComunas, useRegions } from '@/features/shipping'

import {
  addressSchema,
  type AddressSchema,
} from '../../schemas/checkout.schema'

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
    control,
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<AddressSchema>({
    resolver: zodResolver(addressSchema),
    defaultValues,
  })

  // Providers handles unexpected render errors; query loading and errors stay inline here.
  const {
    data: regions,
    isLoading: isLoadingRegions,
    error: regionsError,
    refetch: refetchRegions,
  } = useRegions()

  const rawRegionId = watch('regionId')
  const regionId = Number.isNaN(rawRegionId) ? 0 : rawRegionId || 0

  const {
    data: comunas,
    isLoading: isLoadingComunas,
    error: comunasError,
    refetch: refetchComunas,
  } = useComunas(regionId > 0 ? regionId : undefined, { enabled: regionId > 0 })

  const inputClass = (hasError?: boolean) =>
    `w-full rounded-xl border px-4 py-3 text-sm text-foreground outline-none transition-all focus:ring-1 ${
      hasError
        ? 'border-destructive focus:border-destructive focus:ring-destructive/40'
        : 'border-base-600 bg-secondary focus:border-neon-magenta focus:ring-neon-magenta/40'
    }`

  // min-h-12 keeps the 48px touch target mandated for checkout controls; the
  // Radix Select wrapper already renders the chevron, listbox, keyboard and
  // type-ahead behavior and bounds the owned scrollable content.
  const selectClass = (hasError?: boolean) =>
    `min-h-12 w-full rounded-xl border px-4 py-3 text-sm text-foreground outline-none transition-all focus:ring-1 disabled:cursor-not-allowed disabled:opacity-50 ${
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
            <Controller
              control={control}
              name="regionId"
              render={({ field }) => (
                <Select
                  required
                  disabled={
                    isLoadingRegions ||
                    (regions !== undefined && regions.length === 0)
                  }
                  value={field.value > 0 ? String(field.value) : ''}
                  onValueChange={(value) => {
                    const id = Number(value)
                    field.onChange(id)
                    const region = regions?.find((r) => r.id === id)
                    setValue('regionName', region?.name ?? '')
                    // Clear the comuna before the new cascade loads so a
                    // stale selection can never be submitted.
                    setValue('comunaId', 0)
                    setValue('comunaName', '')
                  }}
                >
                  <SelectTrigger
                    id="address-region"
                    className={selectClass(!!errors.regionId)}
                    aria-invalid={!!errors.regionId}
                  >
                    <SelectValue
                      placeholder={
                        isLoadingRegions
                          ? 'Cargando regiones...'
                          : 'Seleccionar...'
                      }
                    />
                  </SelectTrigger>
                  <SelectContent className="border-border bg-card">
                    {regions?.map((r) => (
                      <SelectItem
                        key={r.id}
                        value={String(r.id)}
                        className="min-h-12"
                      >
                        {r.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {regions && regions.length === 0 && (
              <p className="mt-2 text-xs text-muted-foreground" role="status">
                No hay regiones disponibles.
              </p>
            )}
            {regionsError && (
              <div className="mt-2 flex items-center gap-2">
                <p className="text-xs text-destructive" role="alert">
                  No se pudieron cargar las regiones.
                </p>
                <button
                  type="button"
                  onClick={() => refetchRegions()}
                  className="inline-flex min-h-12 min-w-12 items-center justify-center text-xs font-semibold text-neon-magenta underline underline-offset-2"
                >
                  Reintentar
                </button>
              </div>
            )}
            {errors.regionId && (
              <p className="mt-2 text-xs text-destructive" role="alert">
                {errors.regionId.message}
              </p>
            )}
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
            <Controller
              control={control}
              name="comunaId"
              render={({ field }) => (
                <Select
                  required
                  disabled={
                    regionId <= 0 ||
                    isLoadingComunas ||
                    (comunas !== undefined && comunas.length === 0)
                  }
                  value={field.value > 0 ? String(field.value) : ''}
                  onValueChange={(value) => {
                    const id = Number(value)
                    field.onChange(id)
                    const comuna = comunas?.find((c) => c.id === id)
                    setValue('comunaName', comuna?.name ?? '')
                  }}
                >
                  <SelectTrigger
                    id="address-comuna"
                    className={selectClass(!!errors.comunaId)}
                    aria-invalid={!!errors.comunaId}
                  >
                    <SelectValue
                      placeholder={
                        regionId <= 0
                          ? 'Selecciona una región primero'
                          : isLoadingComunas
                            ? 'Cargando comunas...'
                            : 'Seleccionar...'
                      }
                    />
                  </SelectTrigger>
                  <SelectContent className="border-border bg-card">
                    {comunas?.map((c) => (
                      <SelectItem
                        key={c.id}
                        value={String(c.id)}
                        className="min-h-12"
                      >
                        {c.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {comunas && comunas.length === 0 && regionId > 0 && (
              <p className="mt-2 text-xs text-muted-foreground" role="status">
                No hay comunas disponibles para esta región.
              </p>
            )}
            {comunasError && (
              <div className="mt-2 flex items-center gap-2">
                <p className="text-xs text-destructive" role="alert">
                  No se pudieron cargar las comunas.
                </p>
                <button
                  type="button"
                  onClick={() => refetchComunas()}
                  className="inline-flex min-h-12 min-w-12 items-center justify-center text-xs font-semibold text-neon-magenta underline underline-offset-2"
                >
                  Reintentar
                </button>
              </div>
            )}
            {errors.comunaId && (
              <p className="mt-2 text-xs text-destructive" role="alert">
                {errors.comunaId.message}
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
            className="min-h-12 rounded-xl border border-white/10 px-6 py-3 text-sm font-bold uppercase tracking-wide text-muted-foreground transition-all hover:border-white/20 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
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
