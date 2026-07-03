import { SlidersHorizontal } from 'lucide-react'
import { motion } from 'motion/react'

import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'

import type { Category } from '../types'
import type { ProductFilters } from '../hooks/useProductFilters'

interface FilterSidebarProps
  extends Pick<
    ProductFilters,
    | 'selectedCategories'
    | 'toggleCategory'
    | 'experience'
    | 'toggleExperience'
    | 'experienceLevels'
    | 'priceRange'
    | 'setMinPrice'
    | 'setMaxPrice'
    | 'clearFilters'
  > {
  categories: Category[]
}

export function FilterSidebar({
  categories,
  selectedCategories,
  toggleCategory,
  experience,
  toggleExperience,
  experienceLevels,
  priceRange,
  setMinPrice,
  setMaxPrice,
  clearFilters,
}: FilterSidebarProps) {
  return (
    <motion.aside
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}
      className="hidden lg:block"
    >
      <div className="sticky top-24 space-y-6 rounded-2xl border border-border bg-card p-5">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wide text-foreground">
            Filtros
          </h2>
          <button
            type="button"
            onClick={clearFilters}
            className="rounded px-1 text-xs text-muted-foreground transition-colors hover:text-neon-magenta focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            Limpiar
          </button>
        </div>

        <FilterGroup
          title="Categorías"
          icon={<SlidersHorizontal size={14} />}
        >
          <div className="space-y-2.5">
            {categories.map((category) => (
              <div key={category.id} className="flex items-center gap-2.5">
                <Checkbox
                  id={`category-${category.id}`}
                  checked={selectedCategories.includes(category.name)}
                  onCheckedChange={() => toggleCategory(category.name)}
                  aria-label={category.name}
                />
                <Label
                  htmlFor={`category-${category.id}`}
                  className="cursor-pointer text-xs font-medium text-muted-foreground"
                >
                  {category.name}
                </Label>
              </div>
            ))}
          </div>
        </FilterGroup>

        <FilterGroup title="Nivel de experiencia">
          <div className="space-y-2.5">
            {experienceLevels.map((level) => (
              <div key={level} className="flex items-center gap-2.5">
                <Checkbox
                  id={`experience-${level}`}
                  checked={experience.includes(level)}
                  onCheckedChange={() => toggleExperience(level)}
                  aria-label={level}
                />
                <Label
                  htmlFor={`experience-${level}`}
                  className="cursor-pointer text-xs font-medium capitalize text-muted-foreground"
                >
                  {level}
                </Label>
              </div>
            ))}
          </div>
        </FilterGroup>

        <FilterGroup title="Rango de precio">
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label
                  htmlFor="price-min"
                  className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-muted-foreground"
                >
                  Mín
                </Label>
                <input
                  id="price-min"
                  type="number"
                  min={0}
                  value={priceRange.min}
                  onChange={(event) =>
                    setMinPrice(Number(event.target.value))
                  }
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:border-neon-magenta focus:outline-none focus:ring-1 focus:ring-neon-magenta/40"
                />
              </div>
              <div>
                <Label
                  htmlFor="price-max"
                  className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-muted-foreground"
                >
                  Máx
                </Label>
                <input
                  id="price-max"
                  type="number"
                  min={0}
                  value={priceRange.max}
                  onChange={(event) =>
                    setMaxPrice(Number(event.target.value))
                  }
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:border-neon-magenta focus:outline-none focus:ring-1 focus:ring-neon-magenta/40"
                />
              </div>
            </div>
          </div>
        </FilterGroup>
      </div>
    </motion.aside>
  )
}

function FilterGroup({
  title,
  icon,
  children,
}: {
  title: string
  icon?: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <div className="border-t border-border pt-5 first:border-t-0 first:pt-0">
      <h3 className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-foreground">
        {icon}
        {title}
      </h3>
      {children}
    </div>
  )
}
