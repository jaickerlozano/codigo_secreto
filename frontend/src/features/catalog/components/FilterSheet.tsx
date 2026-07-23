// src/features/catalog/components/FilterSheet.tsx
import { SlidersHorizontal } from 'lucide-react'
import { motion } from 'motion/react'

import { Button } from '@/components/ui/button'
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

// 💡 CORRECCIÓN DE TIPADO: Declaramos explícitamente las propiedades idénticas a la barra lateral
export interface FilterSheetProps {
  priceRange: { min: number; max: number }
  setMinPrice: (value: number) => void
  setMaxPrice: (value: number) => void
  clearFilters: () => void
  categories: Category[]
  selectedCategories: number[]
  toggleCategory: (id: number) => void
  experienceLevels: { value: number; label: string }[]
  experience: number[]
  toggleExperience: (level: number) => void
}

export function FilterSheet({
  priceRange,
  setMinPrice,
  setMaxPrice,
  clearFilters,
  categories,
  selectedCategories,
  toggleCategory,
  experienceLevels,
  experience,
  toggleExperience,
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
      <SheetContent side="left" className="w-[300px] border-border bg-card p-0 flex flex-col h-full">
        <SheetHeader className="p-5 pb-0">
          <SheetTitle className="text-sm font-bold uppercase tracking-wide text-foreground">
            Filtros Móviles
          </SheetTitle>
        </SheetHeader>

        {/* Usamos flex-1 y overflow-y-auto para que los filtros hagan scroll en celulares sin tapar los botones de abajo */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, delay: 0.1 }}
          className="flex-1 space-y-6 overflow-y-auto p-5 scrollbar-thin"
        >
          {/* 1. Rango de precio */}
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

          {/* 2. Categorías móviles */}
          {categories.length > 0 && (
            <FilterGroup title="Categorías">
              <div className="space-y-3 max-h-[160px] overflow-y-auto pr-1">
                {categories.map((cat) => {
                  const isChecked = selectedCategories.includes(cat.id)
                  return (
                    <label key={cat.id} className="flex items-center gap-3 text-xs text-muted-foreground hover:text-foreground cursor-pointer transition-colors py-0.5">
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => toggleCategory(cat.id)}
                        className="rounded border-border text-neon-magenta focus:ring-neon-magenta/40 size-4 bg-background"
                      />
                      <span className={isChecked ? "font-semibold text-foreground" : ""}>
                        {cat.name}
                      </span>
                    </label>
                  )
                })}
              </div>
            </FilterGroup>
          )}

          {/* 3. Nivel de Experiencia móvil */}
          <FilterGroup title="Nivel de Experiencia">
            <div className="space-y-3">
              {experienceLevels.map((lvl) => {
                const isChecked = experience.includes(lvl.value)
                return (
                  <label key={lvl.value} className="flex items-center gap-3 text-xs text-muted-foreground hover:text-foreground cursor-pointer transition-colors py-0.5">
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => toggleExperience(lvl.value)}
                      className="rounded border-border text-neon-magenta focus:ring-neon-magenta/40 size-4 bg-background"
                    />
                    <span className={isChecked ? "font-semibold text-foreground" : ""}>
                      {lvl.label}
                    </span>
                  </label>
                )
              })}
            </div>
          </FilterGroup>
        </motion.div>

        <SheetFooter className="grid grid-cols-2 gap-3 p-5 border-t border-border bg-background/50">
          <Button
            type="button"
            variant="outline"
            onClick={clearFilters}
            className="border-border text-foreground hover:bg-secondary text-xs font-bold uppercase tracking-wide"
          >
            Limpiar
          </Button>
          <SheetClose asChild>
            <Button
              type="button"
              className="text-background text-xs font-bold uppercase tracking-wide"
              style={{ background: 'var(--gradient-brand)' }}
            >
              Aplicar
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
      <h3 className="mb-3.5 text-[11px] font-bold uppercase tracking-wider text-foreground/80">
        {title}
      </h3>
      {children}
    </div>
  )
}
