import { Outlet } from 'react-router'

import { CartDrawer } from '@/features/cart'
import { useCategories } from '@/features/catalog'

import { AgeGate } from './AgeGate'
import { Footer } from './Footer'
import { Header } from './Header'
import { WhatsAppFAB } from './WhatsAppFAB'

interface LayoutProps {
  wishlistCount?: number
}

export function Layout({ wishlistCount = 0 }: LayoutProps) {
  const { data: categories } = useCategories()

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <AgeGate />

      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:bg-neon-magenta-500 focus:text-white focus:px-4 focus:py-2 focus:rounded"
      >
        Saltar al contenido
      </a>

      <Header
        wishlistCount={wishlistCount}
        categories={categories ?? []}
      />

      <CartDrawer />

      <main id="main-content" className="flex-1">
        <Outlet />
      </main>

      <Footer />
      <WhatsAppFAB />
    </div>
  )
}
