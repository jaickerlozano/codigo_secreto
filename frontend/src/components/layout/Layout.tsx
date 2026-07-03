import { Outlet } from 'react-router'

import { AgeGate } from './AgeGate'
import { Footer } from './Footer'
import { Header } from './Header'
import { WhatsAppFAB } from './WhatsAppFAB'

interface LayoutProps {
  cartCount?: number
  wishlistCount?: number
}

const CATEGORIES = ['Vibradores', 'Para Parejas', 'Bienestar', 'Masajeadores', 'Kits', 'Lencería']

export function Layout({ cartCount = 0, wishlistCount = 0 }: LayoutProps) {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <AgeGate />

      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[9999] focus:px-4 focus:py-2.5 focus:text-primary-foreground focus:rounded-xl focus:font-bold focus:text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        style={{ background: 'var(--gradient-brand)' }}
      >
        Saltar al contenido
      </a>

      <Header
        cartCount={cartCount}
        wishlistCount={wishlistCount}
        categories={CATEGORIES}
      />

      <main id="main-content" className="flex-1">
        <Outlet />
      </main>

      <Footer />
      <WhatsAppFAB />
    </div>
  )
}
