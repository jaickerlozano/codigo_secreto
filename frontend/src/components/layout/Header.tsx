import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { Heart, LogOut, Menu, Search, ShoppingCart, User, X } from 'lucide-react'
import { Link, useNavigate } from 'react-router'

import { CSLogo } from '@/components/brand/CSLogo'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuth } from '@/features/auth/context/AuthContext'
import type { Category } from '@/features/catalog/types'
import { useCart, useCartStore } from '@/features/cart'

const FOCUSABLE_SELECTORS = [
  'button:not([disabled])',
  'a[href]',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(', ')

interface HeaderProps {
  wishlistCount?: number
  categories?: Category[]
}

export function Header({
  wishlistCount = 0,
  categories = [],
}: HeaderProps) {
  const [menuOpen, setMenuOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('') // 💡 NUEVO ESTADO
  const navigate = useNavigate()
  const { isAuthenticated, user, logout } = useAuth()
  const { totalItems: cartCount } = useCart()
  const toggleCart = useCartStore((state) => state.toggleCart)
  const menuRef = useRef<HTMLDivElement>(null)
  const menuButtonRef = useRef<HTMLButtonElement>(null)

  const handleLogout = async () => {
    try {
      await logout()
    } catch {
      // Logout may fail due to network/CORS, but we still navigate
    } finally {
      navigate('/')
    }
  }

  useEffect(() => {
    if (menuOpen) {
      const firstFocusable = menuRef.current?.querySelector(
        FOCUSABLE_SELECTORS,
      ) as HTMLElement | null
      firstFocusable?.focus()
    } else {
      menuButtonRef.current?.focus()
    }
  }, [menuOpen])

  useEffect(() => {
    if (!menuOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab' || !menuRef.current) return

      const focusable = Array.from(
        menuRef.current.querySelectorAll(FOCUSABLE_SELECTORS),
      ) as HTMLElement[]
      if (focusable.length === 0) return

      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      const active = document.activeElement

      if (e.shiftKey && active === first) {
        e.preventDefault()
        last.focus()
      } else if (!e.shiftKey && active === last) {
        e.preventDefault()
        first.focus()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [menuOpen])

  const handleHome = () => {
    navigate('/')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // 💡 NUEVA FUNCIÓN MANEJADORA
  const handleSearchSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (searchTerm.trim()) {
      // Redirige al catálogo general inyectando la palabra en la URL
      navigate(`/category/todos?search=${encodeURIComponent(searchTerm.trim())}`)
    }
  }
  return (
    <header
      className="sticky top-0 z-50 bg-background/96 backdrop-blur-md border-b border-border"
      role="banner"
    >
      <div className="max-w-7xl mx-auto px-4 h-[64px] grid grid-cols-[auto_1fr_auto] items-center gap-4">
        <CSLogo onClick={handleHome} />

        <form 
          onSubmit={handleSearchSubmit} 
          className="hidden sm:block max-w-xl w-full mx-auto"
        >
          <div className="relative">
            <Search
              size={15}
              className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground"
              aria-hidden="true"
            />
            <input
              type="search"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)} // Vinculamos el texto
              placeholder="¿Qué estás buscando?"
              className="w-full bg-popover border border-border rounded-xl pl-10 pr-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-neon-magenta-500 focus:ring-1 focus:ring-neon-magenta-500/40 transition-all"
              aria-label="Buscar productos"
            />
          </div>
        </form>

        <div className="flex items-center gap-0.5">
          <button
            type="button"
            className="sm:hidden p-2.5 text-muted-foreground hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-lg"
            aria-label="Buscar"
          >
            <Search size={19} />
          </button>
          {isAuthenticated ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  type="button"
                  className="hidden md:flex p-2.5 text-muted-foreground hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-lg"
                  aria-label="Mi cuenta"
                >
                  <User size={19} />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel className="font-normal">
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium text-foreground">
                      {user?.first_name || user?.email}
                    </p>
                    <p className="text-xs text-muted-foreground">{user?.email}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout}>
                  <LogOut className="mr-2 size-4" />
                  Cerrar sesión
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Link
              to="/login"
              className="hidden md:flex p-2.5 text-muted-foreground hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-lg"
              aria-label="Iniciar sesión"
            >
              <User size={19} />
            </Link>
          )}
          <button
            type="button"
            className="hidden md:flex relative p-2.5 text-muted-foreground hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-lg"
            aria-label={`Favoritos — ${wishlistCount}`}
          >
            <Heart size={19} />
            {wishlistCount > 0 && (
              <span
                className="absolute -top-0.5 -right-0.5 w-[17px] h-[17px] bg-neon-magenta-500 text-foreground text-[9px] font-bold rounded-full flex items-center justify-center"
                aria-hidden="true"
              >
                {wishlistCount > 9 ? '9+' : wishlistCount}
              </span>
            )}
          </button>
          <button
            type="button"
            onClick={toggleCart}
            className="relative p-2.5 text-muted-foreground hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-lg"
            aria-label={`Carrito — ${cartCount} ${cartCount === 1 ? 'producto' : 'productos'}`}
          >
            <ShoppingCart size={19} />
            <AnimatePresence>
              {cartCount > 0 && (
                <motion.span
                  key="cart-badge"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  exit={{ scale: 0 }}
                  className="absolute -top-0.5 -right-0.5 w-[17px] h-[17px] bg-neon-magenta-500 text-foreground text-[9px] font-bold rounded-full flex items-center justify-center"
                  aria-hidden="true"
                >
                  {cartCount > 9 ? '9+' : cartCount}
                </motion.span>
              )}
            </AnimatePresence>
          </button>
          <button
            ref={menuButtonRef}
            type="button"
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden p-2.5 text-muted-foreground hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-lg"
            aria-label={menuOpen ? 'Cerrar menú' : 'Abrir menú'}
            aria-expanded={menuOpen}
            aria-controls="mobile-menu"
          >
            {menuOpen ? <X size={19} /> : <Menu size={19} />}
          </button>
        </div>
      </div>

      {/* Category strip */}
      <div className="hidden md:block border-t border-border">
        <div className="max-w-7xl mx-auto px-4">
          <div
            className="flex items-center gap-6 h-10 overflow-x-auto scrollbar-hide"
            style={{ scrollbarWidth: 'none' }}
          >
            {categories.map((category) => (
              <Link
                key={category.id}
                to={`/category/${category.id}`}
                className="text-[12px] font-medium text-muted-foreground hover:text-foreground whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded px-1"
              >
                {category.name}
              </Link>
            ))}
            <button
              type="button"
              className="text-[12px] font-medium text-muted-foreground hover:text-foreground whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded px-1 ml-auto"
            >
              Contacto
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            ref={menuRef}
            id="mobile-menu"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18 }}
            className="md:hidden overflow-hidden border-t border-border bg-background"
          >
            <div className="max-w-7xl mx-auto px-4 py-3">
              <form 
                onSubmit={(e) => {
                  handleSearchSubmit(e);
                  setMenuOpen(false); // Cierra automáticamente el menú lateral en celulares tras buscar
                }} 
                className="relative mb-3"
              >
                <Search
                  size={14}
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground"
                  aria-hidden="true"
                />
                <input
                  type="search"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)} // Vinculamos el mismo estado global de búsqueda
                  placeholder="¿Qué estás buscando?"
                  className="w-full bg-popover border border-border rounded-xl pl-10 pr-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-neon-magenta-500 focus:ring-1 focus:ring-neon-magenta-500/40"
                  aria-label="Buscar"
                />
              </form>
              <nav className="flex flex-col" aria-label="Menú móvil">
                {categories.map((category) => (
                  <Link
                    key={category.id}
                    to={`/category/${category.id}`}
                    onClick={() => setMenuOpen(false)}
                    className="text-sm text-muted-foreground hover:text-foreground py-2.5 text-left border-b border-border last:border-0 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded"
                  >
                    {category.name}
                  </Link>
                ))}
                <button
                  type="button"
                  onClick={() => setMenuOpen(false)}
                  className="text-sm text-muted-foreground hover:text-foreground py-2.5 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded mt-1"
                >
                  Contacto
                </button>
                <div className="border-t border-border mt-2 pt-2">
                  {isAuthenticated ? (
                    <>
                      <p className="px-2 py-1.5 text-sm font-medium text-foreground">
                        {user?.first_name || user?.email}
                      </p>
                      <button
                        type="button"
                        onClick={() => {
                          setMenuOpen(false)
                          handleLogout()
                        }}
                        className="w-full text-sm text-muted-foreground hover:text-foreground py-2.5 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded"
                      >
                        Cerrar sesión
                      </button>
                    </>
                  ) : (
                    <Link
                      to="/login"
                      onClick={() => setMenuOpen(false)}
                      className="block text-sm text-muted-foreground hover:text-foreground py-2.5 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded"
                    >
                      Iniciar sesión
                    </Link>
                  )}
                </div>
              </nav>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}
