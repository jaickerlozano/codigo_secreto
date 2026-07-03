import { Mail, MapPin, MessageCircle, Phone } from 'lucide-react'

import { CSLogo } from '@/components/brand/CSLogo'

const SHOP_LINKS = ['Vibradores', 'Para Parejas', 'Bienestar', 'Masajeadores', 'Kits', 'Lencería']
const SUPPORT_LINKS = [
  'Preguntas frecuentes',
  'Envíos y plazos',
  'Devoluciones',
  'Garantías',
  'Política de privacidad',
  'Términos de uso',
]
const PAYMENT_METHODS = ['Webpay', 'Flow', 'MercadoPago', 'Transferencia']
const LEGAL_LINKS = ['Privacidad', 'Términos', 'Cookies']

export function Footer() {
  return (
    <footer
      className="bg-background border-t border-border pt-14 pb-8 px-4"
      role="contentinfo"
    >
      <div className="max-w-6xl mx-auto">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-10 mb-12">
          {/* Brand */}
          <div>
            <CSLogo />
            <p className="text-xs text-muted-foreground mt-5 leading-relaxed">
              Tienda de bienestar íntimo con envíos discretos en todo Chile. Privacidad y calidad
              garantizada.
            </p>
            <a
              href="https://www.instagram.com/codigosecreto.cl"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 mt-5 px-3 py-2 bg-card border border-border rounded-xl text-muted-foreground hover:text-foreground transition-colors text-[12px] font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-label="Instagram @codigosecreto.cl (nueva pestaña)"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="currentColor"
                aria-hidden="true"
              >
                <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" />
              </svg>
              @codigosecreto.cl
            </a>
          </div>

          {/* Shop */}
          <div>
            <h3 className="text-[10px] font-extrabold text-foreground uppercase tracking-[0.2em] mb-5">
              Categorías
            </h3>
            <ul className="space-y-2.5">
              {SHOP_LINKS.map((link) => (
                <li key={link}>
                  <button
                    type="button"
                    className="text-[13px] text-muted-foreground hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded"
                  >
                    {link}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Support */}
          <div>
            <h3 className="text-[10px] font-extrabold text-foreground uppercase tracking-[0.2em] mb-5">
              Ayuda
            </h3>
            <ul className="space-y-2.5">
              {SUPPORT_LINKS.map((link) => (
                <li key={link}>
                  <button
                    type="button"
                    className="text-[13px] text-muted-foreground hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded"
                  >
                    {link}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h3 className="text-[10px] font-extrabold text-foreground uppercase tracking-[0.2em] mb-5">
              Contacto
            </h3>
            <div className="space-y-3 mb-5">
              <button
                type="button"
                className="flex items-center gap-2.5 text-[13px] text-muted-foreground hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded"
              >
                <Mail size={13} aria-hidden="true" /> contacto@codigosecreto.cl
              </button>
              <div className="flex items-center gap-2.5 text-[13px] text-muted-foreground">
                <Phone size={13} aria-hidden="true" /> +56 9 XXXX XXXX
              </div>
              <div className="flex items-center gap-2.5 text-[13px] text-muted-foreground">
                <MapPin size={13} aria-hidden="true" /> Santiago, Chile
              </div>
            </div>
            <a
              href="https://wa.me/56912345678?text=Hola%2C%20quisiera%20consultar"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-5 py-3 bg-[#25D366] text-white text-[13px] font-bold rounded-xl uppercase tracking-wide hover:bg-[#1fba58] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#25D366] mb-5"
              aria-label="Contactar por WhatsApp (nueva pestaña)"
            >
              <MessageCircle size={15} aria-hidden="true" /> WhatsApp
            </a>
            <div>
              <p className="text-[9px] font-bold text-muted-foreground uppercase tracking-[0.2em] mb-2">
                Pagos seguros
              </p>
              <div className="flex flex-wrap gap-2">
                {PAYMENT_METHODS.map((method) => (
                  <span
                    key={method}
                    className="px-2 py-1 bg-card border border-border rounded text-[10px] font-bold text-muted-foreground"
                  >
                    {method}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-border pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-muted-foreground">
            © 2024 Código Secreto. Todos los derechos reservados. +18
          </p>
          <div className="flex items-center gap-5">
            {LEGAL_LINKS.map((link) => (
              <button
                key={link}
                type="button"
                className="text-xs text-muted-foreground hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded"
              >
                {link}
              </button>
            ))}
          </div>
        </div>
      </div>
    </footer>
  )
}
