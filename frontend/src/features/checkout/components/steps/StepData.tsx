import { useState } from 'react'

import type { AddressData, ContactData } from '../../types'

import { StepAddress } from './StepAddress'
import { StepContact } from './StepContact'

interface StepDataProps {
  defaultValues: {
    contact: ContactData
    address: AddressData
  }
  onSubmit: (data: { contact: ContactData; address: AddressData }) => void
}

// Data step of the four-step checkout: reuses the existing contact and
// address forms in sequence and submits them together.
export function StepData({ defaultValues, onSubmit }: StepDataProps) {
  const [stage, setStage] = useState<'contact' | 'address'>('contact')
  const [contact, setContact] = useState<ContactData>(defaultValues.contact)

  if (stage === 'contact') {
    return (
      <StepContact
        defaultValues={contact}
        onSubmit={(nextContact) => {
          setContact(nextContact)
          setStage('address')
        }}
      />
    )
  }

  return (
    <StepAddress
      defaultValues={defaultValues.address}
      onSubmit={(address) => onSubmit({ contact, address })}
      onBack={() => setStage('contact')}
    />
  )
}
