import { useEffect } from 'react'
import { useNavigate } from 'react-router'

import { useCartStore } from '@/features/cart'

import { CheckoutProgress } from '../components/CheckoutProgress'
import { OrderSummary } from '../components/OrderSummary'
import { StepAddress } from '../components/steps/StepAddress'
import { StepContact } from '../components/steps/StepContact'
import { StepPayment } from '../components/steps/StepPayment'
import { StepReview } from '../components/steps/StepReview'
import { StepShipping } from '../components/steps/StepShipping'
import { SHIPPING_OPTIONS } from '../data'
import { useCheckout } from '../hooks/useCheckout'

const ORDER_STORAGE_KEY = 'cs-last-order'

export function CheckoutPage() {
  const navigate = useNavigate()
  const { items, clearCart, getSubtotal } = useCartStore()
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
    if (items.length === 0) {
      navigate('/', { replace: true })
    }
  }, [items.length, navigate])

  if (items.length === 0) {
    return null
  }

  const subtotal = getSubtotal()
  const shippingCost =
    SHIPPING_OPTIONS.find((s) => s.id === data.shipping.carrier)?.price ?? 0
  const total = subtotal + shippingCost

  const handleConfirm = () => {
    const orderNumber = `CS-${Math.floor(100000 + Math.random() * 900000)}`
    sessionStorage.setItem(ORDER_STORAGE_KEY, orderNumber)
    clearCart()
    navigate('/confirmation', { replace: true })
  }

  return (
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
                />
              )}
            </div>
          </div>

          <OrderSummary shippingCost={shippingCost} />
        </div>
      </div>
    </main>
  )
}
