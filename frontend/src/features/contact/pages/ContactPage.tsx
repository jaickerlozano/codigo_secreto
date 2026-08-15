import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { AlertCircle, CheckCircle2, Send } from 'lucide-react'
import type { ReactNode } from 'react'
import { useForm } from 'react-hook-form'

import { ContactSubmitError, sendContactMessage } from '../api/contact.api'
import { contactFormSchema, type ContactFormValues } from '../schemas/contact.schema'

const inputClass = (invalid: boolean) => `w-full rounded-xl border bg-secondary px-4 py-3 text-sm text-foreground placeholder-muted-foreground outline-none transition-all focus:ring-1 min-h-12 ${invalid ? 'border-destructive focus:border-destructive focus:ring-destructive/40' : 'border-base-600 focus:border-neon-magenta focus:ring-neon-magenta/40'}`

function Field({ id, label, error, children }: { id: string; label: string; error?: string; children: ReactNode }) {
  return (
    <div>
      <label htmlFor={id} className="mb-2 block text-sm font-semibold text-foreground">{label} <span className="text-neon-magenta" aria-label="requerido">*</span></label>
      {children}
      {error && <p id={`${id}-error`} role="alert" className="mt-2 flex items-center gap-1 text-xs text-destructive"><AlertCircle size={11} aria-hidden="true" /> {error}</p>}
    </div>
  )
}

export function ContactPage() {
  const { register, handleSubmit, reset, formState: { errors } } = useForm<ContactFormValues>({ resolver: zodResolver(contactFormSchema), defaultValues: { name: '', email: '', subject: '', body: '' } })
  const mutation = useMutation({ mutationFn: sendContactMessage })
  const serverFields = mutation.error instanceof ContactSubmitError ? mutation.error.fieldMessages : null
  const submit = (values: ContactFormValues) => { mutation.mutate(values) }
  const retrySubmit = () => { void handleSubmit(submit)() }
  const nameError = errors.name?.message ?? serverFields?.name
  const emailError = errors.email?.message ?? serverFields?.email
  const subjectError = errors.subject?.message ?? serverFields?.subject
  const bodyError = errors.body?.message ?? serverFields?.body

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <h1 className="mb-2 text-2xl font-extrabold uppercase tracking-wide text-foreground">Contacto</h1>
      <p className="mb-8 text-sm text-muted-foreground">Escríbenos y te responderemos a la brevedad. Tu mensaje es confidencial.</p>
      {mutation.isError && (
        <div role="alert" className="mb-5 flex items-start gap-2.5 rounded-xl border border-destructive/30 bg-destructive/10 p-3.5">
          <AlertCircle size={13} className="mt-0.5 shrink-0 text-destructive" aria-hidden="true" />
          <div className="text-xs text-destructive">
            <p>{mutation.error?.message}</p>
            {!serverFields && <button type="button" onClick={retrySubmit} className="mt-2 min-h-12 rounded-lg px-3 text-xs font-bold text-destructive underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Reintentar</button>}
          </div>
        </div>
      )}
      {mutation.isSuccess ? (
        <div role="status" className="rounded-2xl border border-neon-cyan/15 bg-neon-cyan/6 p-6 text-center">
          <CheckCircle2 size={32} className="mx-auto mb-3 text-neon-cyan" aria-hidden="true" />
          <h2 className="mb-1 text-lg font-bold text-foreground">¡Gracias! Tu mensaje fue recibido.</h2>
          <p className="mb-5 text-sm text-muted-foreground">Te responderemos a la brevedad (mensaje #{mutation.data.id}).</p>
          <button type="button" onClick={() => { mutation.reset(); reset() }} className="min-h-12 rounded-xl px-6 py-3 text-sm font-bold uppercase tracking-wide text-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" style={{ background: 'var(--gradient-brand)' }}>Enviar otro mensaje</button>
        </div>
      ) : (
        <form onSubmit={handleSubmit(submit)} noValidate className="space-y-4">
          <Field id="contact-name" label="Nombre" error={nameError}>
            <input id="contact-name" type="text" autoComplete="name" placeholder="Tu nombre" maxLength={120} className={inputClass(!!nameError)} aria-required="true" aria-invalid={!!nameError} {...register('name')} />
          </Field>
          <Field id="contact-email" label="Email" error={emailError}>
            <input id="contact-email" type="email" autoComplete="email" placeholder="tu@email.com" className={inputClass(!!emailError)} aria-required="true" aria-invalid={!!emailError} {...register('email')} />
          </Field>
          <Field id="contact-subject" label="Asunto" error={subjectError}>
            <input id="contact-subject" type="text" placeholder="¿En qué podemos ayudarte?" maxLength={200} className={inputClass(!!subjectError)} aria-required="true" aria-invalid={!!subjectError} {...register('subject')} />
          </Field>
          <Field id="contact-body" label="Mensaje" error={bodyError}>
            <textarea id="contact-body" rows={5} placeholder="Cuéntanos en qué podemos ayudarte" className={inputClass(!!bodyError)} aria-required="true" aria-invalid={!!bodyError} {...register('body')} />
          </Field>
          <div className="flex gap-3 pt-4">
            <button type="submit" disabled={mutation.isPending} className="flex min-h-12 flex-1 items-center justify-center gap-2 rounded-xl text-sm font-bold uppercase tracking-wide text-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card disabled:opacity-60" style={{ background: 'var(--gradient-brand)' }}>
              {mutation.isPending ? 'Enviando…' : 'Enviar mensaje'} <Send size={15} aria-hidden="true" />
            </button>
          </div>
          {mutation.isPending && <p role="status" className="text-center text-xs text-muted-foreground">Enviando mensaje…</p>}
        </form>
      )}
    </div>
  )
}
