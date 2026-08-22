import { useMutation, useQueryClient } from '@tanstack/react-query'
import { AlertCircle, CheckCircle2, Loader2, Lock, MessageCircle, ShieldAlert, WifiOff } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router'

import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { formatCLP } from '@/lib/format'
import { useOrder } from '@/features/orders/hooks/useOrder'
import { approvePayment, clampPollIntervalSeconds, initiatePayment, isSpecialDeliveryAgreementError } from '../api/payments.api'
import { PAYMENT_OPTIONS } from '../data'

export function PendingPaymentPage() {
  const { orderNumber = '' } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()
  const stateTransactionId = typeof location.state === 'object' && location.state !== null && 'transactionId' in location.state && typeof location.state.transactionId === 'number' ? location.state.transactionId : null
  const [transactionId, setTransactionId] = useState<number | null>(stateTransactionId)
  const { data: order, isLoading, isError, error, refetch } = useOrder(orderNumber || undefined)
  const initiate = useMutation({ mutationFn: initiatePayment })
  const approve = useMutation({ mutationFn: approvePayment })
  const isDev = import.meta.env.MODE !== 'production'
  const [online, setOnline] = useState(() => navigator.onLine)
  const [wasBlocked, setWasBlocked] = useState(false)

  const agreement = isSpecialDeliveryAgreementError(initiate.error) ? initiate.error : null
  const gateBlocked = order?.delivery_gate_status === 'blocked'
  const gateReady = order?.delivery_gate_status === 'ready'
  const failure = agreement ? approve.error : (initiate.error ?? approve.error)

  useEffect(() => {
    const handleOnline = () => setOnline(true)
    const handleOffline = () => setOnline(false)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  useEffect(() => {
    if (gateBlocked) setWasBlocked(true)
  }, [gateBlocked])

  // Bounded polling of the delivery gate while a special-delivery agreement is
  // pending: polls at the backend-provided interval (clamped), and stops as
  // soon as the agreement resolves, the gate opens, or the page unmounts.
  useEffect(() => {
    if (!agreement || !gateBlocked || order?.status !== 'PENDING') return
    const seconds = clampPollIntervalSeconds(agreement.pollAfterSeconds)
    const id = window.setInterval(() => {
      void refetch()
    }, seconds * 1000)
    return () => window.clearInterval(id)
  }, [agreement, gateBlocked, order?.status, refetch])

  useEffect(() => {
    if (order && order.status !== 'PENDING') navigate(`/confirmation/${orderNumber}`, { replace: true })
  }, [navigate, order, orderNumber])

  if (isLoading) return <main id="main-content" className="flex min-h-screen items-center justify-center px-4 py-16"><LoadingSpinner /></main>

  if (isError || !order) return (
    <main id="main-content" className="flex min-h-screen flex-col items-center justify-center gap-4 px-4 text-center" role="alert">
      <h1 className="text-xl font-semibold text-error-500">No pudimos cargar el estado del pago</h1>
      <p className="text-base-200">{error?.message ?? 'Pedido no encontrado.'}</p>
      <button type="button" onClick={() => void refetch()} className="min-h-12 rounded-lg bg-neon-cyan-500 px-6 py-3 font-semibold text-base-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Reintentar</button>
      <Link to="/" className="min-h-12 rounded-lg border border-white/10 px-6 py-3 text-sm font-bold uppercase tracking-wide text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Volver al inicio</Link>
    </main>
  )

  const methodName = order.payment_method ? PAYMENT_OPTIONS.find((p) => p.id === order.payment_method)?.name ?? '—' : '—'
  const primaryClass = 'mb-5 flex min-h-12 w-full items-center justify-center gap-2 rounded-xl py-3.5 text-sm font-bold uppercase tracking-wide text-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-40'
  const pollSeconds = agreement ? clampPollIntervalSeconds(agreement.pollAfterSeconds) : null

  return (
    <main id="main-content" className="flex min-h-screen items-center justify-center px-4 py-16">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full border border-neon-cyan/25 bg-neon-cyan/10"><CheckCircle2 size={26} className="text-neon-cyan" aria-hidden="true" /></div>
          <h1 className="mb-2 text-2xl font-extrabold uppercase tracking-wide text-foreground">Pago pendiente</h1>
          <p className="text-sm leading-relaxed text-muted-foreground">Tu pedido está guardado y espera el pago. No se creará ningún duplicado al reintentar.</p>
        </div>
        <div className="mb-5 space-y-3 rounded-2xl border border-white/[0.06] bg-card p-5">
          <div className="flex items-center justify-between text-sm"><span className="text-muted-foreground">Número de pedido</span><span className="font-mono font-bold text-foreground">{order.order_number}</span></div>
          <div className="flex items-center justify-between text-sm"><span className="text-muted-foreground">Total</span><span className="font-bold text-foreground">{formatCLP(order.total)}</span></div>
          <div className="flex items-center justify-between text-sm"><span className="text-muted-foreground">Método</span><span className="font-semibold text-foreground">{methodName}</span></div>
        </div>

        <div className="mb-5 flex items-start gap-3 rounded-2xl border border-neon-cyan/20 bg-neon-cyan/10 p-4"><CheckCircle2 size={14} className="mt-0.5 shrink-0 text-neon-cyan" aria-hidden="true" /><p className="text-xs leading-relaxed text-neon-cyan">Pago <strong>simulado</strong> — disponible solo en desarrollo para validar la compra.</p></div>

        {!online && <div className="mb-5 flex items-start gap-3 rounded-2xl border border-white/10 bg-secondary p-4" role="status"><WifiOff size={14} className="mt-0.5 shrink-0 text-muted-foreground" aria-hidden="true" /><p className="text-xs text-muted-foreground">Sin conexión a internet. Revisa tu conexión y vuelve a intentarlo.</p></div>}

        {gateBlocked && agreement && (
          <div className="mb-5 space-y-3 rounded-2xl border border-neon-magenta/20 bg-neon-magenta/10 p-4" role="status">
            <div className="flex items-start gap-3">
              <MessageCircle size={14} className="mt-0.5 shrink-0 text-neon-magenta" aria-hidden="true" />
              <div className="space-y-2">
                <p className="text-xs leading-relaxed text-foreground">{agreement.message}</p>
                <a href={agreement.whatsappUrl} target="_blank" rel="noopener noreferrer" className="inline-flex min-h-12 items-center gap-2 rounded-lg bg-neon-magenta px-4 py-2.5 text-sm font-bold text-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Coordinar por WhatsApp</a>
                <button type="button" onClick={() => void refetch()} className="ml-2 inline-flex min-h-12 items-center rounded-lg border border-neon-magenta/40 px-4 py-2.5 text-sm font-semibold text-neon-magenta focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Revisar acuerdo</button>
              </div>
            </div>
            {pollSeconds !== null && <p className="pl-7 text-[11px] text-muted-foreground">Revisaremos el estado automáticamente cada {pollSeconds} segundos.</p>}
          </div>
        )}

        {gateBlocked && !agreement && (
          <div className="mb-5 flex items-start gap-3 rounded-2xl border border-neon-magenta/20 bg-neon-magenta/10 p-4" role="status">
            <MessageCircle size={14} className="mt-0.5 shrink-0 text-neon-magenta" aria-hidden="true" />
            <p className="text-xs leading-relaxed text-foreground">Este pedido requiere coordinar la entrega especial antes del pago. Intenta continuar para ver las instrucciones.</p>
          </div>
        )}

        {gateReady && wasBlocked && <div className="mb-5 flex items-start gap-3 rounded-2xl border border-neon-lime/25 bg-neon-lime/10 p-4" role="status"><CheckCircle2 size={14} className="mt-0.5 shrink-0 text-neon-lime" aria-hidden="true" /><p className="text-xs leading-relaxed text-foreground">Acuerdo registrado. Ya puedes continuar con el pago.</p></div>}

        {(!gateBlocked || !agreement) && isDev && (transactionId === null ? (
          <button type="button" style={{ background: 'var(--gradient-brand)' }} disabled={!online || initiate.isPending} onClick={() => initiate.mutate({ order_id: order.id }, { onSuccess: (result) => setTransactionId(result.transaction_id), onError: () => void refetch() })} className={primaryClass}>
            {initiate.isPending && <Loader2 size={15} aria-hidden="true" className="animate-spin" />} Continuar pago
          </button>
        ) : (
          <button type="button" style={{ background: 'var(--gradient-brand)' }} disabled={!online || approve.isPending} onClick={() => approve.mutate(transactionId, { onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['order', orderNumber] }), onError: () => void refetch() })} className={primaryClass}>
            {approve.isPending ? <Loader2 size={15} aria-hidden="true" className="animate-spin" /> : <Lock size={15} aria-hidden="true" />} Aprobar pago (simulado)
          </button>
        ))}
        {!isDev && !gateBlocked && <div className="mb-5 flex items-start gap-3 rounded-2xl bg-secondary p-4" role="status"><ShieldAlert size={14} className="mt-0.5 shrink-0 text-muted-foreground" aria-hidden="true" /><p className="text-xs text-muted-foreground">La aprobación simulada no está disponible en este entorno.</p></div>}
        {failure && <p className="mb-5 flex items-center gap-1.5 text-xs text-destructive" role="alert"><AlertCircle size={11} aria-hidden="true" /> {failure.message}</p>}
        <Link to="/" className="block w-full rounded-xl border border-white/10 py-3.5 text-center text-sm font-bold uppercase tracking-wide text-muted-foreground transition-all hover:border-white/20 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Volver al inicio</Link>
      </div>
    </main>
  )
}
