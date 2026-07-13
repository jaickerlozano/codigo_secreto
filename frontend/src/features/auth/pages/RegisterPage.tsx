import { Link } from 'react-router'

import { RegisterForm } from '../components/RegisterForm'

export function RegisterPage() {
  return (
    <section className="mx-auto max-w-md rounded-2xl border border-base-700 bg-base-800 p-8 shadow-glow-violet">
      <h1 className="mb-2 text-center text-2xl font-bold text-neon-magenta-500">
        Crear cuenta
      </h1>
      <p className="mb-6 text-center text-sm text-base-300">
        Únete a Código Secreto de forma segura y discreta.
      </p>
      <RegisterForm />
      <p className="mt-6 text-center text-sm text-base-300">
        ¿Ya tienes cuenta?{' '}
        <Link to="/login" className="text-neon-cyan-500 hover:underline">
          Inicia sesión
        </Link>
      </p>
    </section>
  )
}
