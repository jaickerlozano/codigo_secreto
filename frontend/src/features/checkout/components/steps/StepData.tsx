import { useState } from 'react'

import type { UserMe } from '@/features/auth/types'

import type { AddressData, ContactData } from '../../types'
import { hasValidChileanMobilePhone } from '../../schemas/checkout.schema'

import { StepAddress } from './StepAddress'
import { StepContact } from './StepContact'
import { StepProfilePhone } from './StepProfilePhone'

interface StepDataProps {
  defaultValues: {
    contact: ContactData
    address: AddressData
  }
  authenticatedUser?: UserMe | null
  onCompleteProfilePhone?: (phone: string) => Promise<UserMe>
  onSubmit: (data: { contact: ContactData; address: AddressData }) => void
}

// Data step of the four-step checkout: reuses the existing contact and
// address forms in sequence and submits them together.
function profileContact(user: UserMe): ContactData {
  return {
    name: `${user.first_name} ${user.last_name}`.trim(),
    email: user.email,
    phone: user.phone ?? '',
    isGuest: false,
  }
}

export function StepData({ defaultValues, authenticatedUser = null, onCompleteProfilePhone, onSubmit }: StepDataProps) {
  const [stage, setStage] = useState<'contact' | 'profile-phone' | 'address'>(() => {
    if (!authenticatedUser) return 'contact'
    return hasValidChileanMobilePhone(authenticatedUser.phone) ? 'address' : 'profile-phone'
  })
  const [contact, setContact] = useState<ContactData>(defaultValues.contact)

  if (stage === 'profile-phone' && authenticatedUser && onCompleteProfilePhone) {
    return <StepProfilePhone onSubmit={async (phone) => {
      const updatedUser = await onCompleteProfilePhone(phone)
      setContact(profileContact(updatedUser))
      setStage('address')
    }} />
  }

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
      onSubmit={(address) => onSubmit({ contact: authenticatedUser ? profileContact(authenticatedUser) : contact, address })}
      onBack={() => setStage('contact')}
      showBack={!authenticatedUser}
    />
  )
}
