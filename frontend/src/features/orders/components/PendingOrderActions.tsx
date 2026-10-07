import { useEffect, useId, useRef, useState } from 'react'
import { Link } from 'react-router'

import { useCartStore } from '@/features/cart/store/cartStore'
import { OrderCreationError, type Order } from '../api/orders.api'
import { useCancelOrder } from '../hooks/useCancelOrder'
import { formatPaymentDeadline, getPaymentHoldState, usePaymentHoldState } from '../lib/pending-order'

const control = 'inline-flex min-h-12 items-center justify-center rounded-lg border border-neon-cyan/50 px-4 py-3 text-base-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan disabled:cursor-not-allowed disabled:opacity-50'

export function PendingOrderActions({ order, showContinue = true, paymentBusy = false, onCancellationPending, onCancelled }: {
  order: Order
  showContinue?: boolean
  paymentBusy?: boolean
  onCancellationPending?: (pending: boolean) => void
  onCancelled?: (order: Order) => void
}) {
  const cancel = useCancelOrder()
  const hold = usePaymentHoldState(order)
  const [confirming, setConfirming] = useState(false)
  const trigger = useRef<HTMLButtonElement>(null)
  const confirmation = useRef<HTMLButtonElement>(null)
  const submitting = useRef(false)
  const panelId = useId()
  const openCart = useCartStore(state => state.openCart)
  const resultMessage = useRef<HTMLParagraphElement>(null)
  useEffect(() => { if (confirming) confirmation.current?.focus() }, [confirming])
  useEffect(() => { if (cancel.isSuccess) resultMessage.current?.focus() }, [cancel.isSuccess])
  const close = () => {
    if (submitting.current) return
    setConfirming(false)
    trigger.current?.focus()
  }
  const submit = async () => {
    if (submitting.current || paymentBusy || getPaymentHoldState(order) !== 'active') return
    submitting.current = true
    onCancellationPending?.(true)
    try {
      const cancelledOrder = await cancel.mutateAsync(order.order_number)
      onCancelled?.(cancelledOrder)
    }
    catch { /* The mutation's inline error remains visible, including stale 409s. */ }
    finally { submitting.current = false; onCancellationPending?.(false) }
  }
  const cancelled = order.status === 'CANCELLED' || cancel.data?.status === 'CANCELLED'
  const error = cancel.error instanceof OrderCreationError && cancel.error.status === 409
    ? 'El estado del pedido cambió. Consulta el estado actualizado antes de continuar.'
    : cancel.error?.message

  return (
    <section aria-label={`Acciones del pedido ${order.order_number}`} className="my-4 space-y-3 rounded-xl border border-neon-cyan/30 bg-base-900 p-4 text-base-100">
      {error && <p role="alert">{error}</p>}
      {cancelled ? <>
        <p ref={resultMessage} tabIndex={-1} role="status">{order.cancellation_reason === 'EXPIRED' ? 'Vencido — plazo de pago vencido' : 'Cancelado'}</p>
        <div className="flex flex-wrap gap-2"><Link to="/" className={control}>Volver al catálogo</Link><button type="button" className={control} onClick={openCart}>Ver carrito</button></div>
      </> : order.status === 'PENDING' ? <>
        {hold === 'active' && order.payment_expires_at && <p>Pago disponible hasta <time dateTime={order.payment_expires_at}>{formatPaymentDeadline(order.payment_expires_at)}</time></p>}
        {hold === 'expired' && <p role="status">Plazo de pago vencido</p>}
        {hold === 'unknown' && <p role="status">No hay un plazo de pago válido. Actualiza el estado del pedido antes de pagar.</p>}
        {hold === 'active' && <>
          <div className="flex flex-wrap gap-2">
            {showContinue && !confirming && !paymentBusy && <Link to={`/checkout/payment/${order.order_number}`} className={control}>Continuar pago</Link>}
            <button ref={trigger} type="button" className={control} disabled={cancel.isPending || paymentBusy} aria-expanded={confirming} aria-controls={panelId} onClick={() => {
              setConfirming(value => !value)
              cancel.reset()
            }}>Cancelar pedido</button>
          </div>
          {confirming && <div id={panelId} role="group" aria-label="Confirmar cancelación" onKeyDown={event => {
            if (event.key === 'Escape') { event.preventDefault(); close() }
          }} className="space-y-3 border-t border-white/20 pt-3">
            <p>¿Cancelar este pedido pendiente? Tendrás que confirmar otro pedido si decides comprar después.</p>
            <div className="flex flex-wrap gap-2">
              <button ref={confirmation} type="button" className={control} disabled={cancel.isPending || paymentBusy} onClick={() => void submit()}>Sí, cancelar pedido</button>
              <button type="button" className={control} disabled={cancel.isPending} onClick={close}>Conservar pedido</button>
            </div>
          </div>}
        </>}
      </> : <p role="status">Este pedido ya no está pendiente de pago.</p>}
      {cancel.isPending && <p role="status" aria-live="polite">Cancelando pedido…</p>}
    </section>
  )
}
