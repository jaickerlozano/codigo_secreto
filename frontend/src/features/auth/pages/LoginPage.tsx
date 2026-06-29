import { LoginForm } from '../components/LoginForm'

export function LoginPage() {
  return (
    <section className="mx-auto max-w-md rounded-2xl border border-base-700 bg-base-800 p-8 shadow-glow-violet">
      <h1 className="mb-6 text-center text-2xl font-bold text-neon-magenta-500">Iniciar sesión</h1>
      <LoginForm />
    </section>
  )
}
