// src/features/catalog/components/FilterSidebar.tsx
import { SlidersHorizontal, Tag, Zap } from 'lucide-react'
import { motion } from 'motion/react'
import { Slider } from '@/components/ui/slider'
import type { Category } from '../types'

export interface FilterSidebarProps {
  priceRange: { min: number; max: number }
  availableRange: { min: number; max: number }
  setMinPrice: (value: number) => void
  setMaxPrice: (value: number) => void
  clearFilters: () => void
  
  // 💡 NUEVAS PROPS: Declaradas correctamente para TypeScript
  categories: Category[]
  selectedCategories: number[]
  toggleCategory: (id: number) => void
  experienceLevels: { value: number; label: string }[]
  experience: number[]
  toggleExperience: (level: number) => void
}

export function FilterSidebar({
  priceRange,
  availableRange,
  setMinPrice,
  setMaxPrice,
  clearFilters,
  categories,
  selectedCategories,
  toggleCategory,
  experienceLevels,
  experience,
  toggleExperience,
}: FilterSidebarProps) {
  return (
    <motion.aside
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}
      className="hidden lg:block w-[260px] shrink-0"
    >
      <div className="sticky top-24 space-y-6 rounded-2xl border border-border bg-card p-5 shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold uppercase tracking-wider text-foreground">
            Filtros Avanzados
          </h2>
          <button
            type="button"
            onClick={clearFilters}
            className="rounded px-1.5 py-0.5 text-xs font-semibold text-muted-foreground transition-colors hover:text-neon-magenta hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            Limpiar Todo
          </button>
        </div>

        {/* 1. Rango de precio */}
        <FilterGroup title="Rango de precio" icon={<SlidersHorizontal size={13} />}>
          <div className="space-y-4 pt-1">
            <div className="flex items-center justify-between text-[11px] font-medium text-muted-foreground">
              <span>${priceRange.min.toLocaleString()}</span>
              <span>${priceRange.max.toLocaleString()}</span>
            </div>
            <Slider
              min={availableRange.min}
              max={availableRange.max}
              step={100}
              value={[priceRange.min, priceRange.max]}
              onValueChange={([min, max]) => {
                setMinPrice(min)
                setMaxPrice(max)
              }}
              className="w-full"
            />
          </div>
        </FilterGroup>

        {/* 2. Categorías */}
        {categories.length > 0 && (
          <FilterGroup title="Categorías" icon={<Tag size={13} />}>
            <div className="space-y-2 max-h-[180px] overflow-y-auto pr-1 scrollbar-thin">
              {categories.map((cat) => {
                const isChecked = selectedCategories.includes(cat.id)
                return (
                  <label key={cat.id} className="flex items-center gap-2.5 text-xs text-muted-foreground hover:text-foreground cursor-pointer transition-colors py-0.5">
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => toggleCategory(cat.id)}
                      className="rounded border-border text-neon-magenta focus:ring-neon-magenta/40 size-3.5 bg-popover"
                    />
                    <span className={isChecked ? "font-medium text-foreground" : ""}>
                      {cat.name}
                    </span>
                  </label>
                )
              })}
            </div>
          </FilterGroup>
        )}

        {/* 3. Nivel de Experiencia */}
        <FilterGroup title="Nivel de Experiencia" icon={<Zap size={13} />}>
          <div className="space-y-2">
            {experienceLevels.map((lvl) => {
              const isChecked = experience.includes(lvl.value)
              return (
                <label key={lvl.value} className="flex items-center gap-2.5 text-xs text-muted-foreground hover:text-foreground cursor-pointer transition-colors py-0.5">
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => toggleExperience(lvl.value)}
                    className="rounded border-border text-neon-magenta focus:ring-neon-magenta/40 size-3.5 bg-popover"
                  />
                  <span className={isChecked ? "font-medium text-foreground" : ""}>
                    {lvl.label}
                  </span>
                </label>
              )
            })}
          </div>
        </FilterGroup>
      </div>
    </motion.aside>
  )
}

function FilterGroup({ title, icon, children }: { title: string; icon?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="border-t border-border pt-5 first:border-t-0 first:pt-0">
      <h3 className="mb-3.5 flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-foreground/80">
        {icon}
        {title}
      </h3>
      {children}
    </div>
  )
}
