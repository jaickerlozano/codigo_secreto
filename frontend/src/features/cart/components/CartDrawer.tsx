import { AnimatePresence, motion } from 'motion/react'
import { Lock, Minus, Package, Plus, ShoppingCart, X } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router'

import { useReducedMotion } from '@/hooks/useReducedMotion'
import { formatCLP } from '@/lib/format'

import { useCart, useCartStore } from '..'

const FOCUSABLE_SELECTORS = [
  'button:not([disabled])',
  'a[href]',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(', ')

export function CartDrawer() {
  const { isOpen, closeCart } = useCartStore()
  const navigate = useNavigate()

  const {
    mode,
    items: cartItems,
    isLoading,
    error,
    retry,
    updateQuantity,
    removeItem,
    subtotal,
    shippingCost,
    total,
    totalItems,
    freeShippingProgress,
    freeShippingThreshold,
    quoteIsError,
    quoteError,
    retryQuote,
  } = useCart()

  const progress = freeShippingProgress ?? 0
  const quotePlaceholder = quoteIsError ? 'No disponible' : 'Cotizando…'
  const prefersReduced = useReducedMotion()
  const panelRef = useRef<HTMLDivElement>(null)
  const previouslyFocusedRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (isOpen) {
      previouslyFocusedRef.current = document.activeElement as HTMLElement
      const firstFocusable = panelRef.current?.querySelector(
        FOCUSABLE_SELECTORS,
      ) as HTMLElement | null
      firstFocusable?.focus()
    } else if (previouslyFocusedRef.current) {
      previouslyFocusedRef.current.focus()
    }
  }, [isOpen])

  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab' || !panelRef.current) return

      const focusable = Array.from(
        panelRef.current.querySelectorAll(FOCUSABLE_SELECTORS),
      ) as HTMLElement[]
      if (focusable.length === 0) return

      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      const active = document.activeElement

      if (e.shiftKey && active === first) {
        e.preventDefault()
        last.focus()
      } else if (!e.shiftKey && active === last) {
        e.preventDefault()
        first.focus()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen])

  return (
    <AnimatePresence>
      {isOpen && (
        <div
          className="fixed inset-0 z-[200] flex justify-end"
          role="dialog"
          aria-modal="true"
          aria-label="Carrito de compras"
        >
          <motion.div
            initial={prefersReduced ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={prefersReduced ? { duration: 0 } : undefined}
            className="absolute inset-0 z-[1] bg-black/80 backdrop-blur-sm"
            onClick={closeCart}
            aria-hidden="true"
          />
          <motion.div
            ref={panelRef}
            initial={prefersReduced ? false : { x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={
              prefersReduced
                ? { duration: 0 }
                : { type: 'spring', damping: 28, stiffness: 280 }
            }
            onClick={(e) => e.stopPropagation()}
            className="relative z-[2] flex h-full w-full max-w-[400px] flex-col border-l border-white/[0.06] bg-card"
            aria-label="Carrito de compras"
          >
            <div className="flex items-center justify-between border-b border-white/[0.06] px-6 py-5">
              <h2 className="flex items-center gap-2.5 text-[15px] font-extrabold uppercase tracking-wide text-foreground">
                <ShoppingCart
                  size={17}
                  className="text-neon-magenta"
                  aria-hidden="true"
                />
                Tu Carrito
                {totalItems > 0 && (
                  <span className="rounded-full bg-neon-magenta px-2 py-0.5 text-[10px] font-bold text-background">
                    {totalItems}
                  </span>
                )}
              </h2>
              <button
                type="button"
                onClick={closeCart}
                className="rounded-lg p-2 text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                aria-label="Cerrar"
              >
                <X size={17} />
              </button>
            </div>

            <div
              className="flex-1 space-y-4 overflow-y-auto px-6 py-4"
              style={{ scrollbarWidth: 'none' }}
            >
              {mode === 'authenticated' && isLoading ? (
                <p role="status" className="py-20 text-center text-base text-muted-foreground">Loading cart…</p>
              ) : mode === 'authenticated' && error ? (
                <div role="alert" className="my-16 rounded-xl bg-destructive/10 p-4 text-center">
                  <p className="mb-3 text-base text-destructive">{error.message}</p>
                  <button type="button" onClick={() => void retry()} className="min-h-12 rounded text-sm font-bold text-neon-magenta underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Retry cart</button>
                </div>
              ) : cartItems.length === 0 ? (
                <div className="py-20 text-center">
                  <ShoppingCart
                    size={36}
                    className="mx-auto mb-4 text-muted"
                    aria-hidden="true"
                  />
                  <p className="mb-4 text-sm text-muted-foreground">
                    Tu carrito está vacío
                  </p>
                  <button
                    type="button"
                    onClick={closeCart}
                    className="rounded text-sm text-neon-magenta hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    Explorar productos
                  </button>
                </div>
              ) : (
                cartItems.map((item) => (
                  <div
                    key={item.product.id}
                    className="flex gap-3.5 border-b border-white/[0.05] pb-4 last:border-0"
                  >
                    <div
                      className={`flex h-16 w-16 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${item.product.gradient}`}
                      aria-hidden="true"
                    >
                      <span className="text-xl opacity-25">
                        {item.product.icon}
                      </span>
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="mb-0.5 truncate text-[13px] font-semibold text-foreground">
                        {item.product.name}
                      </p>
                      <p className="mb-2 truncate text-[11px] text-muted-foreground">
                        {item.product.shortDesc ?? item.product.description}
                      </p>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() =>
                              updateQuantity(
                                item.product.id,
                                item.quantity - 1,
                              )
                            }
                            className="flex h-12 w-12 items-center justify-center rounded-lg bg-secondary text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                            aria-label={`Reducir ${item.product.name}`}
                          >
                            <Minus size={11} />
                          </button>
                          <span
                            className="w-5 text-center text-sm font-bold text-foreground"
                            aria-live="polite"
                          >
                            {item.quantity}
                          </span>
                          <button
                            type="button"
                            onClick={() =>
                              updateQuantity(
                                item.product.id,
                                item.quantity + 1,
                              )
                            }
                            className="flex h-12 w-12 items-center justify-center rounded-lg bg-secondary text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                            aria-label={`Aumentar ${item.product.name}`}
                          >
                            <Plus size={11} />
                          </button>
                        </div>
                        <span className="text-[13px] font-bold text-foreground">
                          {item.subtotal === undefined ? quotePlaceholder : formatCLP(item.subtotal)}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeItem(item.product.id)}
                        className="mt-1.5 rounded text-[11px] text-muted-foreground transition-colors hover:text-neon-magenta focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        aria-label={`Quitar ${item.product.name}`}
                      >
                        Quitar
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>

            {cartItems.length > 0 && (
              <div className="border-t border-white/[0.06] px-6 py-5">
                {quoteIsError && <div role="alert" className="mb-4 rounded-xl bg-destructive/10 p-3"><p className="mb-2 text-[11px] text-destructive">{quoteError?.message ?? 'No pudimos calcular el total. Inténtalo de nuevo.'}</p><button type="button" onClick={retryQuote} className="rounded text-[11px] font-bold text-neon-magenta underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Reintentar cotización</button></div>}
                {freeShippingThreshold > 0 && subtotal! < freeShippingThreshold && (
                  <div className="mb-4 rounded-xl bg-secondary p-3">
                    <p className="text-[11px] text-muted-foreground">
                      <span className="font-bold text-neon-lime">
                        Alcanza el mínimo para obtener envío gratis
                      </span>
                    </p>
                    <motion.div className="mt-2 h-1 overflow-hidden rounded-full bg-muted">
                      <motion.div
                        className="h-full rounded-full bg-neon-lime"
                        initial={prefersReduced ? false : { width: 0 }}
                        animate={{ width: `${progress}%` }}
                        transition={prefersReduced ? { duration: 0 } : { duration: 0.5 }}
                        role="progressbar"
                        aria-valuenow={subtotal!}
                        aria-valuemin={0}
                        aria-valuemax={freeShippingThreshold}
                        aria-label="Progreso envío gratis"
                      />
                    </motion.div>
                  </div>
                )}

                {freeShippingThreshold > 0 && subtotal! >= freeShippingThreshold && (
                  <div className="mb-4 flex items-center gap-2 rounded-xl bg-neon-lime/10 p-3 text-neon-lime">
                    <span className="text-[11px] font-bold">
                      ¡Envío gratis! Has alcanzado el mínimo de compra.
                    </span>
                  </div>
                )}

                <div className="mb-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Subtotal</span>
                    <span className="text-foreground">
                      {subtotal === null ? quotePlaceholder : formatCLP(subtotal)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">
                      Envío estimado
                    </span>
                    <span
                      className={
                        shippingCost === 0
                          ? 'font-semibold text-neon-lime'
                          : 'text-foreground'
                      }
                    >
                      {shippingCost === null ? 'Selecciona una comuna' : shippingCost === 0 ? 'Gratis' : formatCLP(shippingCost)}
                    </span>
                  </div>
                  <div className="flex justify-between border-t border-white/[0.06] pt-2.5 text-[15px] font-extrabold">
                    <span className="text-foreground">Total</span>
                    <span className="text-foreground">{total === null ? quotePlaceholder : formatCLP(total)}</span>
                  </div>
                </div>

                <div className="mb-4 flex items-center justify-center gap-5">
                  <span className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                    <Lock
                      size={9}
                      className="text-neon-lime"
                      aria-hidden="true"
                    />{' '}
                    Pago seguro
                  </span>
                  <span className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                    <Package
                      size={9}
                      className="text-neon-lime"
                      aria-hidden="true"
                    />{' '}
                    Envío discreto
                  </span>
                </div>

                <button
                  type="button"
                  onClick={() => {
                    closeCart()
                    navigate('/checkout')
                  }}
                  className="mb-2 flex w-full items-center justify-center gap-2 rounded-xl py-4 text-sm font-bold uppercase tracking-wide text-white transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card"
                  style={{
                    background: 'var(--gradient-brand)',
                    boxShadow: 'var(--shadow-glow-brand)',
                  }}
                >
                  <Lock size={14} aria-hidden="true" /> Continuar al pago
                </button>
                <button
                  type="button"
                  onClick={() => {
                    // Do not restore focus to the drawer's opener: focus is
                    // handed to the catalog main heading by CategoryPage
                    // after navigation to /category/todos.
                    previouslyFocusedRef.current = null
                    closeCart()
                    navigate('/category/todos')
                  }}
                  className="w-full rounded-xl py-2.5 text-sm text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  Seguir comprando
                </button>
              </div>
            )}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
