import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { SEO } from '@/components/SEO'
import { Skeleton } from '@/components/ui/skeleton'
import { useCart } from '@/features/cart'
import { exchangeOrderAccess, OrderCreationError, type CreateOrderInput } from '@/features/orders/api/orders.api'
import { useCreateOrder } from '@/features/orders/hooks/useCreateOrder'
import { guestQuoteQueryKey } from '@/features/cart/api/quote.api'

import { useInitiatePayment } from '../hooks/useInitiatePayment'
import { CheckoutProgress } from '../components/CheckoutProgress'
import { OrderSummary } from '../components/OrderSummary'
import { StepData } from '../components/steps/StepData'
import { StepPayment } from '../components/steps/StepPayment'
import { StepReview } from '../components/steps/StepReview'
import { StepShipping } from '../components/steps/StepShipping'
import { useCheckout } from '../hooks/useCheckout'

export function CheckoutPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const {
    currentStep,
    data,
    setContact,
    setAddress,
    setShipping,
    setPayment,
    setTermsAccepted,
    nextStep,
    prevStep,
    goToStep,
  } = useCheckout()
  const cart = useCart({ comunaId: data.address.comunaId || null })
  const { items, clearCart, subtotal, shippingCost, total, mode, isLoading, error: cartError, retry: retryCart, quote, quoteInput, quoteIsLoading, quoteIsError, quoteError, quoteIsStale, retryQuote } = cart
  const createOrder = useCreateOrder()
  const initiatePayment = useInitiatePayment()
  const [confirmedRevision, setConfirmedRevision] = useState<string | null>(null)
  const quoteIdentity = useMemo(() => JSON.stringify(quoteInput), [quoteInput])
  const quoteCurrent = quote?.total !== undefined && !quoteIsLoading && !quoteIsError && !quoteIsStale
  const quoteReady = mode === 'authenticated' || Boolean(quoteCurrent && (confirmedRevision === null || confirmedRevision === quote.revision))

  useEffect(() => { setConfirmedRevision(null) }, [quoteIdentity, quote?.revision])

  useEffect(() => {
    if (!isLoading && !cartError && items.length === 0) {
      navigate('/', { replace: true })
    }
  }, [cartError, items.length, isLoading, navigate])

  if (cartError) return <main id="main-content" className="flex min-h-screen flex-col items-center justify-center gap-4 px-4 text-center" role="alert"><h1 className="text-xl font-semibold text-error-500">No pudimos cargar tu carrito</h1><p className="text-base-200">{cartError.message}</p><button type="button" onClick={() => void retryCart()} className="min-h-12 rounded-lg bg-neon-cyan-500 px-6 py-3 font-semibold text-base-900">Reintentar carrito</button></main>

  if (items.length === 0) {
    if (isLoading) return <CheckoutLoadingState />
    return null
  }

  const handleConfirm = () => {
    if (mode === 'guest' && !quoteReady) return

    const payload = {
      phone: data.contact.phone,
      shipping_address: data.address.address,
      apartment_office: data.address.apartment ?? '',
      payment_method: data.payment.method,
      comuna: data.address.comunaId,
      comuna_name: data.address.comunaName,
      region_name: data.address.regionName,
      ...(mode === 'guest' && {
        guest_email: data.contact.email,
        guest_name: data.contact.name,
        guest_items: items.map((item) => ({
          product_id: item.product.id,
          quantity: item.quantity,
        })),
        confirmed_revision: quote?.revision ?? '',
      }),
    } satisfies CreateOrderInput

    if (mode === 'guest' && quote) {
      setConfirmedRevision(quote.revision)
    }

    createOrder.mutate(payload, {
      onSuccess: async (order) => {
        try {
          if (mode === 'guest' && order.guest_access) await exchangeOrderAccess(order.order_number, order.guest_access.token)
          initiatePayment.mutate(
          { order_id: order.id },
          {
            onSuccess: () => {
              if (mode === 'authenticated') {
                queryClient.invalidateQueries({ queryKey: ['cart'] })
              } else {
                clearCart()
              }

              navigate('/confirmation', { replace: true, state: { orderNumber: order.order_number } })
            },
            onError: (error) => {
              toast.error(error.message)
            },
          },
          )
        } catch (error) {
          toast.error(error instanceof Error ? error.message : 'No se pudo validar el acceso al pedido.')
        }
      },
      onError: (error) => {
        if (mode === 'guest' && error instanceof OrderCreationError && error.refreshedQuote) {
          const key = guestQuoteQueryKey(quoteInput)
          queryClient.setQueryData(key, error.refreshedQuote)
          setConfirmedRevision(null)
          void queryClient.invalidateQueries({ queryKey: key, exact: true })
          toast.error('El total cambió. Revisa y confirma nuevamente.')
          return
        }
        toast.error(error.message)
      },
    })
  }

  return (
    <>
      <SEO pageTitle="Checkout" />
      <main id="main-content" className="min-h-screen py-8 px-4">
        <div className="mx-auto max-w-5xl">
          <CheckoutProgress currentStep={currentStep} />

          <div className="grid gap-8 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <div className="rounded-2xl border border-white/[0.06] bg-card p-6">
                {currentStep === 1 && (
                  <StepData
                    defaultValues={{
                      contact: data.contact,
                      address: data.address,
                    }}
                    onSubmit={({ contact, address }) => {
                      setContact(contact)
                      setAddress(address)
                      nextStep()
                    }}
                  />
                )}
                {currentStep === 2 && (
                  <StepShipping
                    destinationName={data.address.comunaName ?? ''}
                    destinationRegion={data.address.regionName}
                    tariff={shippingCost}
                    isLoading={quoteIsLoading}
                    errorMessage={quoteIsError ? (quoteError?.message ?? 'No pudimos calcular el costo de envío.') : null}
                    onRetry={retryQuote}
                    onSubmit={() => {
                      setShipping({})
                      nextStep()
                    }}
                    onBack={prevStep}
                  />
                )}
                {currentStep === 3 && (
                  <StepPayment
                    defaultValues={data.payment}
                    onSubmit={(payment) => {
                      setPayment(payment)
                      nextStep()
                    }}
                    onBack={prevStep}
                  />
                )}
                {currentStep === 4 && (
                  <StepReview
                    data={data}
                    subtotal={subtotal}
                    shippingCost={shippingCost}
                    total={total}
                    quoteReady={quoteReady}
                    onEditStep={goToStep}
                    onTermsChange={setTermsAccepted}
                    onBack={prevStep}
                    onConfirm={handleConfirm}
                    isSubmitting={
                      createOrder.isPending || initiatePayment.isPending
                    }
                  />
                )}
              </div>
            </div>

            <OrderSummary cart={cart} />
          </div>
        </div>
      </main>
    </>
  )
}

export function CheckoutLoadingState() {
  return <main id="main-content" className="min-h-screen px-4 py-8" role="status" aria-label="Cargando checkout" aria-live="polite"><div aria-hidden="true"><Skeleton className="h-8 w-48" /><Skeleton className="h-64 w-full rounded-2xl" /></div><span className="sr-only">Cargando checkout...</span></main>
}
