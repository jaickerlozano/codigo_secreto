import { Minus, Plus } from 'lucide-react'
import { motion } from 'motion/react'

interface QuantitySelectorProps {
  value: number
  onChange: (value: number) => void
  min?: number
  max?: number
}

export function QuantitySelector({
  value,
  onChange,
  min = 1,
  max = 10,
}: QuantitySelectorProps) {
  const canDecrease = value > min
  const canIncrease = value < max

  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        onClick={() => canDecrease && onChange(value - 1)}
        disabled={!canDecrease}
        aria-label="Disminuir cantidad"
        className="flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-card text-foreground transition-all hover:border-neon-magenta hover:text-neon-magenta focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-40"
      >
        <Minus size={16} />
      </button>

      <div className="flex h-10 w-12 items-center justify-center overflow-hidden rounded-lg border border-border bg-card">
        <motion.span
          key={value}
          initial={{ y: -16, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 16, opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="text-sm font-semibold text-foreground"
          aria-live="polite"
        >
          {value}
        </motion.span>
      </div>

      <button
        type="button"
        onClick={() => canIncrease && onChange(value + 1)}
        disabled={!canIncrease}
        aria-label="Aumentar cantidad"
        className="flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-card text-foreground transition-all hover:border-neon-magenta hover:text-neon-magenta focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-40"
      >
        <Plus size={16} />
      </button>
    </div>
  )
}
