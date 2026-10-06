import { useEffect, useRef, useState } from 'react'

import type { UserMe } from '@/features/auth/types'

import type { AddressData, ContactData } from '../../types'
import { hasValidChileanMobilePhone } from '../../schemas/checkout.schema'

import { StepAddress } from './StepAddress'
import { StepContact } from './StepContact'
import { StepProfilePhone } from './StepProfilePhone'

export type DataSection = 'contact' | 'address'

interface StepDataProps {
  defaultValues: {
    contact: ContactData
    address: AddressData
  }
  initialSection?: DataSection
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

export function StepData({ defaultValues, initialSection, authenticatedUser = null, onCompleteProfilePhone, onSubmit }: StepDataProps) {
  const [stage, setStage] = useState<DataSection | 'profile-phone'>(() => {
    // An edit must not bypass the existing required profile-phone completion.
    if (authenticatedUser && onCompleteProfilePhone && !hasValidChileanMobilePhone(authenticatedUser.phone)) return 'profile-phone'
    return initialSection ?? (authenticatedUser ? 'address' : 'contact')
  })
  const [contact, setContact] = useState<ContactData>(defaultValues.contact)
  const [hasVisitedAddress, setHasVisitedAddress] = useState(stage === 'address')
  const contentRef = useRef<HTMLDivElement>(null)

  const showAddress = () => {
    setHasVisitedAddress(true)
    setStage('address')
  }

  useEffect(() => {
    if (!initialSection) return
    // preventScroll leaves the page's step-change scroll restoration in charge.
    const target = contentRef.current?.querySelector<HTMLElement>(
      '[data-stage]:not([hidden]) input:not([disabled]):not([readonly]), [data-stage]:not([hidden]) fieldset[tabindex="-1"]'
    )
    target?.focus({ preventScroll: true })
  }, [initialSection, stage])

  return (
    <div ref={contentRef}>
      {stage === 'profile-phone' && authenticatedUser && onCompleteProfilePhone && (
        <div data-stage="profile-phone">
          <StepProfilePhone onSubmit={async (phone) => {
            const updatedUser = await onCompleteProfilePhone(phone)
            setContact(profileContact(updatedUser))
            showAddress()
          }} />
        </div>
      )}
      {stage === 'contact' && (
        <div data-stage="contact">
          {authenticatedUser ? (
            <fieldset tabIndex={-1} className="rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
              <legend className="mb-6 text-xl font-extrabold uppercase tracking-wide text-foreground">
                Datos de contacto
              </legend>
              <p className="mb-4 text-sm text-muted-foreground">Usamos los datos de tu cuenta para este pedido.</p>
              <dl className="mb-6 space-y-3 text-sm text-foreground">
                <div><dt className="font-semibold">Nombre completo</dt><dd>{profileContact(authenticatedUser).name}</dd></div>
                <div><dt className="font-semibold">Email</dt><dd>{authenticatedUser.email}</dd></div>
                <div><dt className="font-semibold">Teléfono</dt><dd>{authenticatedUser.phone}</dd></div>
              </dl>
              <button
                type="button"
                onClick={showAddress}
                className="min-h-12 w-full rounded-xl py-3.5 text-sm font-bold uppercase tracking-wide text-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                style={{ background: 'var(--gradient-brand)' }}
              >
                Siguiente
              </button>
            </fieldset>
          ) : (
            <StepContact
              defaultValues={contact}
              onSubmit={(nextContact) => {
                setContact(nextContact)
                showAddress()
              }}
            />
          )}
        </div>
      )}
      {hasVisitedAddress && (
        // Keep the form mounted across internal Back so address drafts survive.
        <div data-stage="address" hidden={stage !== 'address'}>
          <StepAddress
            defaultValues={defaultValues.address}
            onSubmit={(address) => onSubmit({ contact: authenticatedUser ? profileContact(authenticatedUser) : contact, address })}
            onBack={() => setStage('contact')}
            showBack={!authenticatedUser}
          />
        </div>
      )}
    </div>
  )
}
