import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router'
import { toast } from 'sonner'

import { registerSchema, type RegisterSchema } from '../schemas/register.schema'
import { useRegister } from '../hooks/useRegister'

export function RegisterForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterSchema>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      first_name: '',
      last_name: '',
      email: '',
      password: '',
      password_confirm: '',
    },
  })

  const { mutate, isPending, error } = useRegister()
  const navigate = useNavigate()

  const onSubmit = (data: RegisterSchema) => {
    mutate(data, {
      onSuccess: () => {
        toast.success('Cuenta creada con éxito. Ahora inicia sesión.')
        navigate('/login', { replace: true })
      },
    })
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
      <div className="space-y-1">
        <label htmlFor="first_name" className="block text-sm font-medium text-base-200">
          Nombre
        </label>
        <input
          id="first_name"
          type="text"
          autoComplete="given-name"
          className="w-full rounded-lg border border-base-600 bg-base-900 px-4 py-2.5 text-base-100 outline-none transition focus:border-neon-cyan-500 focus:ring-1 focus:ring-neon-cyan-500"
          placeholder="María"
          {...register('first_name')}
        />
        {errors.first_name && (
          <p className="text-sm text-error-500" role="alert">
            {errors.first_name.message}
          </p>
        )}
      </div>

      <div className="space-y-1">
        <label htmlFor="last_name" className="block text-sm font-medium text-base-200">
          Apellido
        </label>
        <input
          id="last_name"
          type="text"
          autoComplete="family-name"
          className="w-full rounded-lg border border-base-600 bg-base-900 px-4 py-2.5 text-base-100 outline-none transition focus:border-neon-cyan-500 focus:ring-1 focus:ring-neon-cyan-500"
          placeholder="González"
          {...register('last_name')}
        />
        {errors.last_name && (
          <p className="text-sm text-error-500" role="alert">
            {errors.last_name.message}
          </p>
        )}
      </div>

      <div className="space-y-1">
        <label htmlFor="email" className="block text-sm font-medium text-base-200">
          Correo electrónico
        </label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          className="w-full rounded-lg border border-base-600 bg-base-900 px-4 py-2.5 text-base-100 outline-none transition focus:border-neon-cyan-500 focus:ring-1 focus:ring-neon-cyan-500"
          placeholder="tu@email.com"
          {...register('email')}
        />
        {errors.email && (
          <p className="text-sm text-error-500" role="alert">
            {errors.email.message}
          </p>
        )}
      </div>

      <div className="space-y-1">
        <label htmlFor="password" className="block text-sm font-medium text-base-200">
          Contraseña
        </label>
        <input
          id="password"
          type="password"
          autoComplete="new-password"
          className="w-full rounded-lg border border-base-600 bg-base-900 px-4 py-2.5 text-base-100 outline-none transition focus:border-neon-cyan-500 focus:ring-1 focus:ring-neon-cyan-500"
          placeholder="••••••••"
          {...register('password')}
        />
        {errors.password && (
          <p className="text-sm text-error-500" role="alert">
            {errors.password.message}
          </p>
        )}
      </div>

      <div className="space-y-1">
        <label htmlFor="password_confirm" className="block text-sm font-medium text-base-200">
          Confirmar contraseña
        </label>
        <input
          id="password_confirm"
          type="password"
          autoComplete="new-password"
          className="w-full rounded-lg border border-base-600 bg-base-900 px-4 py-2.5 text-base-100 outline-none transition focus:border-neon-cyan-500 focus:ring-1 focus:ring-neon-cyan-500"
          placeholder="••••••••"
          {...register('password_confirm')}
        />
        {errors.password_confirm && (
          <p className="text-sm text-error-500" role="alert">
            {errors.password_confirm.message}
          </p>
        )}
      </div>

      {error && (
        <div className="rounded-lg border border-error-500 bg-error-500/10 px-4 py-3" role="alert">
          <p className="text-sm text-error-500">{error.message}</p>
        </div>
      )}

      <button
        type="submit"
        disabled={isPending}
        className="w-full rounded-lg bg-neon-magenta-500 px-4 py-2.5 font-semibold text-base-900 shadow-glow-magenta transition hover:bg-neon-magenta-400 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isPending ? 'Creando cuenta...' : 'Crear cuenta'}
      </button>
    </form>
  )
}
