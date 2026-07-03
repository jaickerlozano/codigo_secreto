import { Check } from 'lucide-react'

import type { Review } from '../../types'
import { StarRating } from '../StarRating'

interface ReviewsSectionProps {
  reviews: Review[]
}

export function ReviewsSection({ reviews }: ReviewsSectionProps) {
  return (
    <section className="py-20 px-4" aria-label="Reseñas">
      <div className="mx-auto max-w-4xl">
        <div className="mb-12 text-center">
          <h2 className="mb-3 text-3xl font-extrabold uppercase tracking-wide text-foreground">
            Lo que dicen nuestros clientes
          </h2>
          <div className="flex items-center justify-center gap-2.5">
            <StarRating rating={5} size={17} />
            <span className="text-sm text-muted-foreground">
              4.8 promedio · +500 reseñas verificadas
            </span>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          {reviews.map((review) => (
            <article
              key={review.id}
              className="rounded-2xl border border-border bg-card p-5 transition-colors hover:border-white/12"
            >
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className="flex h-9 w-9 items-center justify-center rounded-full"
                    style={{ background: 'var(--gradient-brand)' }}
                    aria-hidden="true"
                  >
                    <span className="text-[10px] font-bold text-white">
                      {review.name}
                    </span>
                  </div>
                  <div>
                    <p className="text-[12px] font-semibold text-foreground">
                      Cliente verificado
                    </p>
                    {review.date && (
                      <p className="text-[10px] text-muted-foreground">
                        {review.date}
                      </p>
                    )}
                  </div>
                </div>
                <StarRating rating={review.rating} size={10} />
              </div>

              <p className="text-sm leading-relaxed text-muted-foreground">
                &ldquo;{review.text}&rdquo;
              </p>

              <div className="mt-3 flex items-center gap-1.5">
                <Check
                  size={10}
                  className="text-neon-lime"
                  aria-hidden="true"
                />
                <span className="text-[10px] text-muted-foreground">
                  Compra verificada
                </span>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
