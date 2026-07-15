import { motion } from 'motion/react'
import { MessageCircle } from 'lucide-react'

import { SUPPORT_PHONE } from '@/lib/config'

interface WhatsAppFABProps {
  phone?: string
  message?: string
}

export function WhatsAppFAB({
  phone = SUPPORT_PHONE,
  message = 'Hola, quisiera consultar',
}: WhatsAppFABProps) {
  const href = `https://wa.me/${phone}?text=${encodeURIComponent(message)}`

  return (
    <motion.a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="fixed bottom-6 right-6 z-[90] w-14 h-14 rounded-full flex items-center justify-center focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#25D366]/40"
      style={{ background: '#25D366', boxShadow: '0 4px 24px rgba(37,211,102,0.45)' }}
      aria-label="Contactar por WhatsApp (nueva pestaña)"
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.95 }}
      transition={{ duration: 0.2 }}
    >
      <MessageCircle size={26} className="text-white" aria-hidden="true" />
    </motion.a>
  )
}
