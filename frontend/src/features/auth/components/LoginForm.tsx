import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { useNavigate, useSearchParams } from 'react-router'

import { loginSchema, type LoginSchema } from '../schemas/login.schema'
import { useAuth } from '../context/AuthContext'

export function LoginForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginSchema>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  })

  const { login, isLoggingIn, loginError } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const onSubmit = async (data: LoginSchema) => {
    try {
      await login(data)
      const next = searchParams.get('next') ?? '/'
      navigate(next, { replace: true })
    } catch {
      // El error queda expuesto en loginError; no navegamos.
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
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
          autoComplete="current-password"
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

      {loginError && (
        <div className="rounded-lg border border-error-500 bg-error-500/10 px-4 py-3" role="alert">
          <p className="text-sm text-error-500">{loginError.message}</p>
        </div>
      )}

      <button
        type="submit"
        disabled={isLoggingIn}
        className="w-full rounded-lg bg-neon-magenta-500 px-4 py-2.5 font-semibold text-base-900 shadow-glow-magenta transition hover:bg-neon-magenta-400 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isLoggingIn ? 'Ingresando...' : 'Iniciar sesión'}
      </button>
    </form>
  )
}
