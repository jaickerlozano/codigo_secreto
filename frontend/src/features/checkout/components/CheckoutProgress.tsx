import { Check } from 'lucide-react'

import { useReducedMotion } from '@/hooks/useReducedMotion'

import type { CheckoutStep } from '../types'

interface CheckoutProgressProps {
  currentStep: CheckoutStep
  totalSteps?: number
}

const STEP_LABELS = ['Datos', 'Envío', 'Pago', 'Confirmar'] as const

export function CheckoutProgress({
  currentStep,
  totalSteps = 4,
}: CheckoutProgressProps) {
  const labels = STEP_LABELS.slice(0, totalSteps)
  const prefersReduced = useReducedMotion()

  return (
    <nav aria-label="Progreso del checkout" className="mb-10 px-2">
      <ol className="relative flex items-start justify-between md:items-center">
        {/* Connecting line background */}
        <li
          className="absolute top-4 left-0 right-0 hidden h-px bg-muted md:block"
          aria-hidden="true"
        />
        {/* Active connecting line */}
        <li
          className={`absolute top-4 left-0 hidden h-px bg-neon-magenta md:block ${prefersReduced ? '' : 'transition-all duration-500'}`}
          style={{ width: `${((currentStep - 1) / (totalSteps - 1)) * 100}%` }}
          aria-hidden="true"
        />

        {labels.map((label, index) => {
          const stepNumber = (index + 1) as CheckoutStep
          const isCompleted = stepNumber < currentStep
          const isCurrent = stepNumber === currentStep

          return (
            <li
              key={label}
              className="relative z-10 flex flex-1 flex-col items-center gap-2"
            >
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold ${
                  prefersReduced ? '' : 'transition-all'
                } ${
                  isCompleted || isCurrent
                    ? 'text-white'
                    : 'bg-secondary text-muted-foreground'
                } ${isCurrent ? 'ring-4 ring-neon-magenta/20' : ''}`}
                style={
                  isCompleted || isCurrent
                    ? { background: 'var(--gradient-brand)' }
                    : undefined
                }
                aria-current={isCurrent ? 'step' : undefined}
              >
                {isCompleted ? (
                  <Check size={14} aria-hidden="true" />
                ) : (
                  stepNumber
                )}
              </div>
              <span
                className={`text-center text-[9px] font-bold uppercase tracking-wide ${
                  isCurrent
                    ? 'text-foreground'
                    : isCompleted
                      ? 'text-neon-magenta'
                      : 'text-muted-foreground'
                }`}
              >
                {label}
              </span>
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
