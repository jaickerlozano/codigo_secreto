import { Check, ChevronDown, ShoppingBag } from 'lucide-react'
import { useState } from 'react'

import { formatCLP } from '@/lib/format'

import type { UseCartResult } from '@/features/cart/hooks/useCart'

type OrderSummaryCart = Pick<UseCartResult, 'items' | 'mode' | 'subtotal' | 'shippingCost' | 'total' | 'quoteIsLoading' | 'quoteIsError' | 'quoteError' | 'retryQuote'>

interface OrderSummaryProps { cart: OrderSummaryCart }

function quoteAmount(value: number | null, empty = 'Cotizando…') { return value === null ? empty : formatCLP(value) }

export function OrderSummary({ cart }: OrderSummaryProps) {
  const { items, mode, subtotal, shippingCost, total, quoteIsLoading, quoteIsError, quoteError, retryQuote } = cart
  const [isOpen, setIsOpen] = useState(false)

  return (
    <aside aria-label="Resumen del pedido">
      {/* Mobile toggle */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="mb-4 flex w-full items-center justify-between rounded-2xl border border-white/[0.06] bg-card p-4 lg:hidden"
        aria-expanded={isOpen}
        aria-controls="order-summary-panel"
      >
        <span className="flex items-center gap-2 text-[13px] font-extrabold uppercase tracking-wide text-foreground">
          <ShoppingBag size={16} className="text-neon-magenta" aria-hidden="true" />
          Resumen del pedido
        </span>
        <span className="flex items-center gap-2">
          <span className="text-sm font-bold text-foreground">
            {quoteAmount(total)}
          </span>
          <ChevronDown
            size={16}
            className={`text-muted-foreground transition-transform ${isOpen ? 'rotate-180' : ''}`}
            aria-hidden="true"
          />
        </span>
      </button>

      <div
        id="order-summary-panel"
        className={`rounded-2xl border border-white/[0.06] bg-card p-5 lg:sticky lg:top-24 ${isOpen ? 'block' : 'hidden lg:block'}`}
      >
        <h3 className="mb-4 text-[13px] font-extrabold uppercase tracking-wide text-foreground">
          Resumen del pedido
        </h3>

        <div className="mb-4 space-y-3">
          {items.length === 0 ? (
            <p className="text-sm text-muted-foreground">Tu carrito está vacío.</p>
          ) : (
            items.map((item) => (
              <div key={item.product.id} className="flex items-center gap-3">
                <div
                  className={`relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${item.product.gradient}`}
                  aria-hidden="true"
                >
                  <span className="text-lg opacity-20">{item.product.icon}</span>
                  <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full border border-white/10 bg-[#1e1e1e] text-[9px] font-bold text-neon-magenta">
                    {item.quantity}
                  </span>
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs font-semibold text-foreground">
                    {item.product.name}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="border-t border-white/[0.06] pt-4 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Subtotal</span>
            <span className="text-foreground">{quoteAmount(subtotal)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Envío</span>
            <span
              className={
                shippingCost === 0 ? 'text-neon-lime' : 'text-foreground'
              }
            >
              {shippingCost === 0 ? 'Gratis' : quoteAmount(shippingCost, 'Selecciona una comuna')}
            </span>
          </div>
          <div className="flex justify-between border-t border-white/[0.06] pt-2.5 text-[15px] font-extrabold">
            <span className="text-foreground">Total</span>
            <span className="text-foreground">{quoteAmount(total)}</span>
          </div>
        </div>

        {mode === 'guest' && quoteIsLoading && <p className="mt-4 text-center text-xs text-muted-foreground" role="status">Calculando el total seguro…</p>}
        {mode === 'guest' && quoteIsError && <div className="mt-4 space-y-2" role="alert"><p className="text-xs text-destructive">{quoteError?.message ?? 'No se pudo calcular el total.'}</p><button type="button" onClick={retryQuote} className="min-h-12 w-full rounded-xl border border-neon-cyan/60 px-4 text-xs font-bold uppercase text-neon-cyan focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Reintentar cálculo</button></div>}

        <div className="mt-4 space-y-2">
          {[
            'Empaque 100% discreto',
            'Pago 100% seguro (SSL)',
            'Garantía 6 meses',
          ].map((benefit) => (
            <div key={benefit} className="flex items-center gap-2">
              <Check
                size={10}
                className="shrink-0 text-neon-lime"
                aria-hidden="true"
              />
              <span className="text-[10px] text-muted-foreground">
                {benefit}
              </span>
            </div>
          ))}
        </div>
      </div>
    </aside>
  )
}
