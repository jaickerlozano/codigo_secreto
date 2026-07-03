import { Link } from 'react-router'
import { motion } from 'motion/react'

import { cn } from '@/lib/utils'

import type { Category } from '../types'

interface CategoryGridProps {
  categories: Category[]
  activeCategoryId?: string
  viewAllHref?: string
}

export function CategoryGrid({
  categories,
  activeCategoryId,
  viewAllHref,
}: CategoryGridProps) {
  return (
    <section className="py-16 px-4" aria-label="Categorías destacadas">
      <div className="mx-auto max-w-6xl">
        <div className="mb-10 flex items-end justify-between">
          <div className="text-center sm:text-left">
            <h2 className="mb-2 text-3xl font-extrabold uppercase tracking-wide text-foreground">
              Categorías destacadas
            </h2>
            <p className="text-sm text-muted-foreground">
              Encuentra exactamente lo que buscas
            </p>
          </div>
          {viewAllHref && (
            <Link
              to={viewAllHref}
              className="hidden text-xs font-semibold text-neon-magenta transition-colors hover:text-neon-magenta/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:inline"
            >
              Ver todos
            </Link>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-8">
          {categories.map((category) => {
            const isActive = activeCategoryId === category.id

            return (
              <Link
                key={category.id}
                to={`/category/${category.id}`}
                className="group/card block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-2xl"
              >
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.98 }}
                  className={cn(
                    'flex flex-col items-center gap-2.5 rounded-2xl border p-3 transition-all duration-200',
                    isActive
                      ? 'border-neon-magenta/60 bg-neon-magenta/8 shadow-[0_0_20px_rgba(255,43,214,0.2)]'
                      : 'border-border bg-card hover:border-white/15',
                  )}
                >
                  <div
                    className={`flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br ${category.gradient}`}
                    aria-hidden="true"
                  >
                    <span className="text-lg opacity-50">
                      {category.icon}
                    </span>
                  </div>
                  <div className="text-center">
                    <p className="text-[11px] font-bold text-foreground">
                      {category.name}
                    </p>
                    {category.count !== undefined && (
                      <p className="mt-0.5 text-[9px] text-muted-foreground">
                        {category.count}
                      </p>
                    )}
                  </div>
                </motion.div>
              </Link>
            )
          })}
        </div>
      </div>
    </section>
  )
}
