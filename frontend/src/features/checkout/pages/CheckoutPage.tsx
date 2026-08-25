import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { SEO } from '@/components/SEO'
import { Skeleton } from '@/components/ui/skeleton'
import { useCart } from '@/features/cart'
import { useAuth } from '@/features/auth'
import { updateProfilePhone } from '@/features/auth/api/auth.api'
import {
  exchangeOrderAccess,
  OrderCreationError,
  type CreateOrderInput,
} from '@/features/orders/api/orders.api'
import { useCreateOrder } from '@/features/orders/hooks/useCreateOrder'
import { guestQuoteQueryKey } from '@/features/cart/api/quote.api'
import { useComunas, useRegions } from '@/features/shipping'

import { useInitiatePayment } from '../hooks/useInitiatePayment'
import { CheckoutProgress } from '../components/CheckoutProgress'
import { OrderSummary } from '../components/OrderSummary'
import { StepData } from '../components/steps/StepData'
import { StepPayment } from '../components/steps/StepPayment'
import { StepReview } from '../components/steps/StepReview'
import { StepShipping } from '../components/steps/StepShipping'
import { useCheckout } from '../hooks/useCheckout'
import { reconcileShippingDestination } from '../lib/shipping-destination'

export function CheckoutPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user, isLoading: isAuthLoading } = useAuth()
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
  const regionsQuery = useRegions()
  const selectedRegion = regionsQuery.data?.find(
    (region) => region.id === data.address.regionId
  )
  const comunasQuery = useComunas(selectedRegion?.id, {
    enabled: selectedRegion !== undefined,
  })
  const destinationResolution = reconcileShippingDestination(
    data.address,
    regionsQuery.data,
    comunasQuery.data
  )
  const destination =
    destinationResolution.status === 'valid'
      ? destinationResolution.destination
      : null
  const cart = useCart({ comunaId: destination?.comunaId ?? null })
  const {
    items,
    subtotal,
    shippingCost,
    total,
    mode,
    isLoading,
    error: cartError,
    retry: retryCart,
    quote,
    quoteInput,
    quoteIsLoading,
    quoteIsError,
    quoteError,
    quoteIsStale,
    retryQuote,
  } = cart
  const createOrder = useCreateOrder()
  const initiatePayment = useInitiatePayment()
  const [confirmedRevision, setConfirmedRevision] = useState<string | null>(
    null
  )
  const quoteIdentity = useMemo(() => JSON.stringify(quoteInput), [quoteInput])
  const quoteCurrent =
    quote?.total !== undefined &&
    !quoteIsLoading &&
    !quoteIsError &&
    !quoteIsStale
  const quoteReady =
    mode === 'authenticated' ||
    Boolean(
      quoteCurrent &&
      (confirmedRevision === null || confirmedRevision === quote.revision)
    )

  useEffect(() => {
    setConfirmedRevision(null)
  }, [quoteIdentity, quote?.revision])

  useEffect(() => {
    if (destinationResolution.status === 'valid') {
      const { comunaId, comunaName, regionName } =
        destinationResolution.destination
      if (
        data.address.comunaId !== comunaId ||
        data.address.comunaName !== comunaName ||
        data.address.regionName !== regionName
      ) {
        setAddress({
          ...data.address,
          comunaId,
          comunaName,
          regionName,
        })
      }
      return
    }

    if (
      destinationResolution.status !== 'invalid' ||
      (data.address.regionId <= 0 &&
        data.address.comunaId <= 0 &&
        !data.address.regionName &&
        !data.address.comunaName)
    ) {
      return
    }

    setAddress({
      ...data.address,
      regionId: 0,
      regionName: '',
      comunaId: 0,
      comunaName: '',
    })
    setShipping({})
    goToStep(1)
  }, [data.address, destinationResolution, goToStep, setAddress, setShipping])

  useEffect(() => {
    if (!isLoading && !cartError && items.length === 0) {
      navigate('/', { replace: true })
    }
  }, [cartError, items.length, isLoading, navigate])

  // Wait for /api/auth/me/ before selecting a checkout branch so an active
  // session never briefly renders guest-only controls.
  if (isAuthLoading) return <CheckoutLoadingState />

  if (cartError)
    return (
      <main
        id="main-content"
        className="flex min-h-screen flex-col items-center justify-center gap-4 px-4 text-center"
        role="alert"
      >
        <h1 className="text-xl font-semibold text-error-500">
          No pudimos cargar tu carrito
        </h1>
        <p className="text-base-200">{cartError.message}</p>
        <button
          type="button"
          onClick={() => void retryCart()}
          className="min-h-12 rounded-lg bg-neon-cyan-500 px-6 py-3 font-semibold text-base-900"
        >
          Reintentar carrito
        </button>
      </main>
    )

  if (items.length === 0) {
    if (isLoading) return <CheckoutLoadingState />
    return null
  }

  const handleConfirm = () => {
    if (mode === 'guest' && !quoteReady) return

    const payload = {
      shipping_address: data.address.address,
      apartment_office: data.address.apartment ?? '',
      payment_method: data.payment.method,
      comuna: data.address.comunaId,
      comuna_name: data.address.comunaName,
      region_name: data.address.regionName,
      delivery_kind: data.shipping.deliveryKind,
      requested_dispatch_date: data.shipping.requestedDispatchDate ?? null,
      shipping_option_id: data.shipping.shippingOptionId ?? null,
      ...(mode === 'guest' && {
        phone: data.contact.phone,
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
          if (mode === 'guest' && order.guest_access)
            await exchangeOrderAccess(
              order.order_number,
              order.guest_access.token
            )
          initiatePayment.mutate(
            { order_id: order.id },
            {
              onSuccess: (initiation) => {
                if (mode === 'authenticated') {
                  queryClient.invalidateQueries({ queryKey: ['cart'] })
                }

                navigate(`/checkout/payment/${order.order_number}`, {
                  replace: true,
                  state: { transactionId: initiation.transaction_id },
                })
              },
              onError: (error) => {
                toast.error(error.message)
                navigate(`/checkout/payment/${order.order_number}`, {
                  replace: true,
                })
              },
            }
          )
        } catch (error) {
          toast.error(
            error instanceof Error
              ? error.message
              : 'No se pudo validar el acceso al pedido.'
          )
        }
      },
      onError: (error) => {
        if (
          mode === 'guest' &&
          error instanceof OrderCreationError &&
          error.refreshedQuote
        ) {
          const key = guestQuoteQueryKey(quoteInput)
          queryClient.setQueryData(key, error.refreshedQuote)
          setConfirmedRevision(null)
          void queryClient.invalidateQueries({ queryKey: key, exact: true })
          toast.error('El total cambió. Revisa y confirma nuevamente.')
          return
        }
        if (
          error instanceof OrderCreationError &&
          (error.code === 'checkout_key_conflict' ||
            error.code === 'delivery_option_stale' ||
            error.code === 'delivery_schedule_ineligible')
        ) {
          setShipping({})
          goToStep(2)
          toast.error(
            'Tu selección de envío ya no está disponible. Selecciónala nuevamente.'
          )
          return
        }
        toast.error(error.message)
      },
    })
  }

  const accountContact = user
    ? `${`${user.first_name} ${user.last_name}`.trim()} · ${user.email}`
    : undefined

  const completeProfilePhone = async (phone: string) => {
    const updatedUser = await updateProfilePhone({ phone })
    queryClient.setQueryData(['me'], updatedUser)
    return updatedUser
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
                    authenticatedUser={user}
                    onCompleteProfilePhone={completeProfilePhone}
                    onSubmit={({ contact, address }) => {
                      setContact(contact)
                      if (data.address.comunaId !== address.comunaId) {
                        setShipping({})
                      }
                      setAddress(address)
                      nextStep()
                    }}
                  />
                )}
                {currentStep === 2 && (
                  <StepShipping
                    comunaId={destination?.comunaId ?? null}
                    destinationName={destination?.comunaName ?? ''}
                    destinationRegion={destination?.regionName}
                    shippingCost={shippingCost}
                    quoteIsLoading={quoteIsLoading}
                    quoteIsError={quoteIsError}
                    quoteError={quoteError}
                    onRetryQuote={retryQuote}
                    selection={data.shipping}
                    onSubmit={(shipping) => {
                      setShipping(shipping)
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
                    accountContact={
                      mode === 'authenticated' ? accountContact : undefined
                    }
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
  return (
    <main
      id="main-content"
      className="min-h-screen px-4 py-8"
      role="status"
      aria-label="Cargando checkout"
      aria-live="polite"
    >
      <div aria-hidden="true">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full rounded-2xl" />
      </div>
      <span className="sr-only">Cargando checkout...</span>
    </main>
  )
}
