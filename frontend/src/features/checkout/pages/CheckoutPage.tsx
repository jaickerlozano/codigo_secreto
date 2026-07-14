import { useEffect } from 'react'
import { useNavigate } from 'react-router'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { SEO } from '@/components/SEO'
import { useCart } from '@/features/cart'
import { useCreateOrder } from '@/features/orders/hooks/useCreateOrder'
import { addGuestOrder } from '@/features/orders/lib/guestOrders'

import { useInitiatePayment } from '../hooks/useInitiatePayment'
import { CheckoutProgress } from '../components/CheckoutProgress'
import { OrderSummary } from '../components/OrderSummary'
import { StepAddress } from '../components/steps/StepAddress'
import { StepContact } from '../components/steps/StepContact'
import { StepPayment } from '../components/steps/StepPayment'
import { StepReview } from '../components/steps/StepReview'
import { StepShipping } from '../components/steps/StepShipping'
import { useCheckout } from '../hooks/useCheckout'

const ORDER_STORAGE_KEY = 'cs-last-order'

export function CheckoutPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { items, clearCart, subtotal, shippingCost, total, mode, isLoading } = useCart()
  const createOrder = useCreateOrder()
  const initiatePayment = useInitiatePayment()
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

  useEffect(() => {
    if (!isLoading && items.length === 0) {
      navigate('/', { replace: true })
    }
  }, [items.length, isLoading, navigate])

  if (items.length === 0) {
    return null
  }

  const handleConfirm = () => {
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
      }),
    }

    createOrder.mutate(payload, {
      onSuccess: (order) => {
        sessionStorage.setItem(ORDER_STORAGE_KEY, order.order_number)

        if (mode === 'guest') {
          addGuestOrder(order.order_number)
        }

        initiatePayment.mutate(
          { order_id: order.id },
          {
            onSuccess: () => {
              if (mode === 'authenticated') {
                queryClient.invalidateQueries({ queryKey: ['cart'] })
              } else {
                clearCart()
              }

              navigate('/confirmation', { replace: true })
            },
            onError: (error) => {
              toast.error(error.message)
            },
          },
        )
      },
      onError: (error) => {
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
                  <StepContact
                    defaultValues={data.contact}
                    onSubmit={(contact) => {
                      setContact(contact)
                      nextStep()
                    }}
                  />
                )}
                {currentStep === 2 && (
                  <StepAddress
                    defaultValues={data.address}
                    onSubmit={(address) => {
                      setAddress(address)
                      nextStep()
                    }}
                    onBack={prevStep}
                  />
                )}
                {currentStep === 3 && (
                  <StepShipping
                    defaultValues={data.shipping}
                    onSubmit={(shipping) => {
                      setShipping(shipping)
                      nextStep()
                    }}
                    onBack={prevStep}
                  />
                )}
                {currentStep === 4 && (
                  <StepPayment
                    defaultValues={data.payment}
                    onSubmit={(payment) => {
                      setPayment(payment)
                      nextStep()
                    }}
                    onBack={prevStep}
                  />
                )}
                {currentStep === 5 && (
                  <StepReview
                    data={data}
                    subtotal={subtotal}
                    shippingCost={shippingCost}
                    total={total}
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

            <OrderSummary />
          </div>
        </div>
      </main>
    </>
  )
}
