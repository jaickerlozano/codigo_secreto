import { cn } from '@/lib/utils'

interface StarRatingProps {
  rating: number
  maxStars?: number
  size?: number
  className?: string
}

export function StarRating({
  rating,
  maxStars = 5,
  size = 13,
  className,
}: StarRatingProps) {
  const rounded = Math.round(rating)

  return (
    <div
      className={cn('flex gap-0.5', className)}
      aria-label={`${rating} de ${maxStars} estrellas`}
      role="img"
    >
      {Array.from({ length: maxStars }, (_, index) => {
        const filled = index < rounded
        return (
          <svg
            key={index}
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill={filled ? 'var(--color-neon-magenta)' : 'none'}
            stroke="var(--color-neon-magenta)"
            strokeWidth="1.5"
            aria-hidden="true"
          >
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
          </svg>
        )
      })}
    </div>
  )
}
