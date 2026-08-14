import { useState } from 'react'

import type {
  AddressData,
  CheckoutData,
  CheckoutStep,
  ContactData,
  PaymentData,
  ShippingData,
} from '../types'

const INITIAL_DATA: CheckoutData = {
  contact: {
    name: '',
    email: '',
    phone: '',
    isGuest: true,
  },
  address: {
    regionId: 0,
    regionName: '',
    comunaId: 0,
    comunaName: '',
    address: '',
    apartment: '',
    postalCode: '',
    notes: '',
  },
  shipping: {},
  payment: {
    method: 'webpay',
  },
  termsAccepted: false,
}

interface UseCheckoutReturn {
  currentStep: CheckoutStep
  data: CheckoutData
  setContact: (contact: ContactData) => void
  setAddress: (address: AddressData) => void
  setShipping: (shipping: ShippingData) => void
  setPayment: (payment: PaymentData) => void
  setTermsAccepted: (accepted: boolean) => void
  nextStep: () => void
  prevStep: () => void
  goToStep: (step: CheckoutStep) => void
}

export function useCheckout(): UseCheckoutReturn {
  const [currentStep, setCurrentStep] = useState<CheckoutStep>(1)
  const [data, setData] = useState<CheckoutData>(INITIAL_DATA)

  const updateField = <K extends keyof CheckoutData>(
    field: K,
    value: CheckoutData[K],
  ) => {
    setData((prev) => ({ ...prev, [field]: value }))
  }

  const nextStep = () => {
    setCurrentStep((prev) => (prev < 4 ? ((prev + 1) as CheckoutStep) : prev))
  }

  const prevStep = () => {
    setCurrentStep((prev) => (prev > 1 ? ((prev - 1) as CheckoutStep) : prev))
  }

  const goToStep = (step: CheckoutStep) => {
    if (step >= 1 && step <= 4) {
      setCurrentStep(step)
    }
  }

  return {
    currentStep,
    data,
    setContact: (contact) => updateField('contact', contact),
    setAddress: (address) => updateField('address', address),
    setShipping: (shipping) => updateField('shipping', shipping),
    setPayment: (payment) => updateField('payment', payment),
    setTermsAccepted: (accepted) => updateField('termsAccepted', accepted),
    nextStep,
    prevStep,
    goToStep,
  }
}
