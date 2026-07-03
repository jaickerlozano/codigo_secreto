import { SlidersHorizontal } from 'lucide-react'
import { motion } from 'motion/react'

import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetClose,
  SheetFooter,
} from '@/components/ui/sheet'

import type { Category } from '../types'
import type { ProductFilters } from '../hooks/useProductFilters'

interface FilterSheetProps
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

export function FilterSheet({
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
}: FilterSheetProps) {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="gap-2 border-border bg-card text-foreground hover:bg-card/80 hover:text-neon-magenta lg:hidden"
        >
          <SlidersHorizontal size={14} />
          Filtros
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-[300px] border-border bg-card p-0">
        <SheetHeader className="p-5 pb-0">
          <SheetTitle className="text-sm font-bold uppercase tracking-wide text-foreground">
            Filtros
          </SheetTitle>
        </SheetHeader>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, delay: 0.1 }}
          className="space-y-6 overflow-y-auto p-5"
        >
          <FilterGroup title="Categorías">
            <div className="space-y-2.5">
              {categories.map((category) => (
                <div key={category.id} className="flex items-center gap-2.5">
                  <Checkbox
                    id={`mobile-category-${category.id}`}
                    checked={selectedCategories.includes(category.name)}
                    onCheckedChange={() => toggleCategory(category.name)}
                    aria-label={category.name}
                  />
                  <Label
                    htmlFor={`mobile-category-${category.id}`}
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
                    id={`mobile-experience-${level}`}
                    checked={experience.includes(level)}
                    onCheckedChange={() => toggleExperience(level)}
                    aria-label={level}
                  />
                  <Label
                    htmlFor={`mobile-experience-${level}`}
                    className="cursor-pointer text-xs font-medium capitalize text-muted-foreground"
                  >
                    {level}
                  </Label>
                </div>
              ))}
            </div>
          </FilterGroup>

          <FilterGroup title="Rango de precio">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label
                  htmlFor="mobile-price-min"
                  className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-muted-foreground"
                >
                  Mín
                </Label>
                <input
                  id="mobile-price-min"
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
                  htmlFor="mobile-price-max"
                  className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-muted-foreground"
                >
                  Máx
                </Label>
                <input
                  id="mobile-price-max"
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
          </FilterGroup>
        </motion.div>

        <SheetFooter className="grid grid-cols-2 gap-3 p-5">
          <Button
            type="button"
            variant="outline"
            onClick={clearFilters}
            className="border-border text-foreground hover:bg-secondary"
          >
            Limpiar
          </Button>
          <SheetClose asChild>
            <Button
              type="button"
              className="text-background"
              style={{ background: 'var(--gradient-brand)' }}
            >
              Aplicar filtros
            </Button>
          </SheetClose>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}

function FilterGroup({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="border-t border-border pt-5 first:border-t-0 first:pt-0">
      <h3 className="mb-3 text-xs font-bold uppercase tracking-wide text-foreground">
        {title}
      </h3>
      {children}
    </div>
  )
}
