import { Check, Truck } from 'lucide-react'
import { motion } from 'motion/react'

export interface TimelineStep {
  id: string
  title: string
  description: string
  timestamp?: string
  completed: boolean
  current: boolean
}

interface OrderTimelineProps {
  steps: TimelineStep[]
}

export function OrderTimeline({ steps }: OrderTimelineProps) {
  return (
    <ol className="relative" aria-label="Estado del pedido">
      {steps.map((step, index) => {
        const isLast = index === steps.length - 1

        return (
          <li key={step.id} className="relative flex gap-4 pb-8 last:pb-0">
            {!isLast && (
              <div
                className={`absolute left-5 top-10 bottom-0 w-px ${
                  step.completed ? 'bg-neon-lime/50' : 'bg-border'
                }`}
                aria-hidden="true"
              />
            )}

            <div className="relative z-10">
              <motion.div
                initial={false}
                animate={
                  step.current
                    ? { scale: [1, 1.08, 1] }
                    : {}
                }
                transition={
                  step.current
                    ? {
                        duration: 2,
                        repeat: Infinity,
                        ease: 'easeInOut',
                      }
                    : undefined
                }
                className={`flex h-10 w-10 items-center justify-center rounded-full border-2 ${
                  step.completed
                    ? 'border-neon-lime bg-neon-lime'
                    : step.current
                      ? 'border-neon-magenta bg-neon-magenta/10'
                      : 'border-border bg-card'
                }`}
              >
                {step.completed ? (
                  <Check size={18} className="text-background" />
                ) : step.current ? (
                  <Truck size={18} className="text-neon-magenta" />
                ) : (
                  <span className="text-xs font-semibold text-muted-foreground">
                    {index + 1}
                  </span>
                )}
              </motion.div>

              {step.current && (
                <span
                  className="absolute inset-0 rounded-full bg-neon-magenta/20"
                  aria-hidden="true"
                >
                  <motion.span
                    className="absolute inset-0 rounded-full border border-neon-magenta"
                    animate={{ scale: [1, 1.6], opacity: [0.6, 0] }}
                    transition={{
                      duration: 1.8,
                      repeat: Infinity,
                      ease: 'easeOut',
                    }}
                  />
                </span>
              )}
            </div>

            <div className="pt-1.5">
              <p
                className={`text-sm font-semibold ${
                  step.current
                    ? 'text-neon-magenta'
                    : step.completed
                      ? 'text-foreground'
                      : 'text-muted-foreground'
                }`}
              >
                {step.title}
              </p>
              <p className="text-xs leading-relaxed text-muted-foreground">
                {step.description}
              </p>
              {step.timestamp && (
                <p className="mt-1 text-[10px] text-muted-foreground">
                  {step.timestamp}
                </p>
              )}
            </div>
          </li>
        )
      })}
    </ol>
  )
}
