const DEFAULT_ICON = '✦'
const DEFAULT_GRADIENT = 'from-violet-950 via-purple-900 to-violet-800'

const CATEGORY_STYLES: Record<string, { icon: string; gradient: string }> = {
  Vibradores: {
    icon: '✦',
    gradient: 'from-violet-950 via-purple-900 to-violet-800',
  },
  Anillos: {
    icon: '◯',
    gradient: 'from-fuchsia-950 via-pink-900 to-fuchsia-800',
  },
  Masturbadores: {
    icon: '◈',
    gradient: 'from-cyan-950 via-teal-900 to-cyan-800',
  },
  Anal: {
    icon: '⬡',
    gradient: 'from-indigo-950 via-violet-900 to-indigo-800',
  },
  Juegos: {
    icon: '❋',
    gradient: 'from-lime-950 via-emerald-900 to-lime-800',
  },
  Bondage: {
    icon: '⬤',
    gradient: 'from-rose-950 via-pink-900 to-rose-800',
  },
  Lubricantes: {
    icon: '◇',
    gradient: 'from-amber-950 via-yellow-900 to-amber-800',
  },
  'Aceites y Feromonas': {
    icon: '♦',
    gradient: 'from-emerald-950 via-green-900 to-emerald-800',
  },
}

export function getCategoryStyle(name: string) {
  return CATEGORY_STYLES[name] ?? { icon: DEFAULT_ICON, gradient: DEFAULT_GRADIENT }
}
