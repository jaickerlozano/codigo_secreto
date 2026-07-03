# Discreet Shipping UI — Patterns & Copy Guidelines

## Core Principle

Shipping must feel **safe and private** without explicitly saying "we know this is sensitive." The language should normalize the purchase, not highlight the taboo.

## Shipping Method Selection UI

### Layout Pattern

```
┌─────────────────────────────────────────────┐
│  📦 Método de Envío                         │
│  ─────────────────────────────────────────  │
│                                             │
│  ○ ⚡ Chilexpress              $4.990       │
│    1-2 días hábiles                         │
│    ✓ Embalaje discreto                      │
│                                             │
│  ○ 🚚 Starken                   $3.490       │
│    2-4 días hábiles                         │
│    ✓ Embalaje discreto                      │
│                                             │
│  ○ 📮 Bluexpress                 $2.990       │
│    3-5 días hábiles                         │
│    ✓ Embalaje discreto                      │
│                                             │
│  ○ 🏪 Retiro en tienda           GRATIS      │
│    Disponible en 24 horas                   │
│    Santiago Centro                          │
│                                             │
│  ─────────────────────────────────────────  │
│  🔒 Todos nuestros envíos son 100% discretos│
│  El remitente no revela el contenido        │
└─────────────────────────────────────────────┘
```

### Design Tokens (Neon)

- **Card background**: `--color-base-800`
- **Selected border**: `--color-neon-cyan-500` with `--glow-cyan-sm`
- **Carrier logo**: Grayscale by default, color on selection
- **"Embalaje discreto" badge**: `--color-neon-lime-500` text, small caps
- **Price**: `--color-base-100` (white), bold
- **Delivery estimate**: `--color-base-250` (gray)

### Interaction

- Radio button replaced with neon cyan border on selection
- Subtle glow animation on select (200ms)
- Carrier logos animate from grayscale to color
- "Embalaje discreto" checkmark uses neon lime

---

## Copy Guidelines

### DO Say

- "Embalaje discreto" (discreet packaging)
- "Envío confidencial" (confidential shipping)
- "Sin identificación externa" (no external identification)
- "Remitente neutro" (neutral sender)
- "Tu privacidad es nuestra prioridad" (your privacy is our priority)
- "Empaque sin logos ni marcas" (packaging without logos or brands)

### DON'T Say

- "Empaque para productos adultos" (packaging for adult products)
- "Discreto por la naturaleza del producto" (discreet due to product nature)
- "Nadie sabrá qué compraste" (nobody will know what you bought)
- "Empaque vergonzoso" (embarrassing packaging)
- Anything that implies shame or embarrassment

### Tone

- **Normalize**: "Todos nuestros envíos son discretos" (all our shipments are discreet)
- **Professional**: "Política de privacidad en cada envío" (privacy policy in every shipment)
- **Reassuring**: "Tu pedido llega de forma segura y privada" (your order arrives safely and privately)

---

## Packaging Details Page

### Expandable Section

```
┌─────────────────────────────────────────────┐
│  📦 ¿Cómo es nuestro embalaje?          ▼   │
│  ─────────────────────────────────────────  │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │  [Image: plain brown box]           │    │
│  │                                     │    │
│  │  • Caja de cartón corrugado         │    │
│  │  • Sin logos ni marcas externas     │    │
│  │  • Remitente: "CS Logistics"        │    │
│  │  • Sin descripción del contenido    │    │
│  │  • Sellado con cinta neutra         │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  Tu pedido llega en un empaque genérico     │
│  que no revela su contenido. Ni el          │
│  transportista ni tus vecinos sabrán        │
│  qué contiene.                              │
└─────────────────────────────────────────────┘
```

### Design

- **Accordion**: Collapsed by default, expandable on click
- **Image**: Illustration style, not photo (more approachable)
- **Bullet points**: Neon lime checkmarks
- **"CS Logistics"**: Fictional sender name (neutral, professional)
- **Text**: `--color-base-250`, not too prominent

---

## Tracking UI

### Order Tracking Page

```
┌─────────────────────────────────────────────┐
│  📍 Seguimiento de Pedido                   │
│  ─────────────────────────────────────────  │
│  Pedido #CS-2024-12345                      │
│                                             │
│  ✅ Pedido confirmado        Ayer 14:30     │
│  ✅ En preparación           Ayer 16:45     │
│  ✅ Despachado               Hoy 09:00      │
│  ○ En tránsito               -              │
│  ○ Entregado                 -              │
│                                             │
│  ─────────────────────────────────────────  │
│  Transportista: Chilexpress                 │
│  Código de seguimiento:                     │
│  CLX-1234567890 [Copiar]                    │
│                                             │
│  [Rastrear en Chilexpress ↗]                │
│                                             │
│  ─────────────────────────────────────────  │
│  📦 Tu paquete viaja en embalaje discreto   │
└─────────────────────────────────────────────┘
```

### Design

- **Timeline**: Vertical, neon cyan for completed steps
- **Current step**: Neon magenta pulse animation
- **Pending steps**: `--color-base-500` (gray)
- **Tracking code**: Monospace font, copy button with neon lime feedback
- **External link**: Opens carrier site in new tab
- **Discreet reminder**: Subtle, at bottom, `--color-base-300`

---

## Email Notifications

### Subject Lines (Discreet)

- **Order confirmed**: "Tu pedido #12345 ha sido confirmado"
- **Shipped**: "Tu pedido #12345 está en camino"
- **Out for delivery**: "Tu pedido #12345 llega hoy"
- **Delivered**: "Tu pedido #12345 fue entregado"

### Email Content

```
Hola [Nombre],

Tu pedido #CS-2024-12345 fue despachado hoy.

Transportista: Chilexpress
Código de seguimiento: CLX-1234567890
Rastrear: [link]

Tu paquete viaja en embalaje discreto.
El remitente es "CS Logistics".

¿Preguntas? Responde este email.

— Equipo Código Secreto
```

### Design

- **Plain text option**: Available for maximum privacy
- **HTML version**: Minimal branding, no product images
- **Sender name**: "Código Secreto" (not explicit)
- **No product details**: Only order number and tracking

---

## SMS Notifications (Optional)

### Opt-in Language

```
□ Recibir actualizaciones por SMS
  (Solo mensajes genéricos: "Tu pedido está en camino")
```

### Message Templates

- **Shipped**: "Tu pedido #12345 fue despachado. Rastreo: [link]"
- **Out for delivery**: "Tu pedido #12345 llega hoy."
- **Delivered**: "Tu pedido #12345 fue entregado."

### Rules

- **No product names**: Only order number
- **No brand name**: Generic "tu pedido"
- **Opt-in only**: Never send without explicit consent
- **Stop option**: "Responde STOP para cancelar"

---

## Delivery Instructions

### Optional Field

```
┌─────────────────────────────────────────────┐
│  📝 Instrucciones de entrega (opcional)     │
│  ─────────────────────────────────────────  │
│  ┌─────────────────────────────────────┐    │
│  │ Ej: Dejar en conserjería, no tocar  │    │
│  │ el timbre, llamar antes de llegar   │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  💡 Estas instrucciones son confidenciales  │
│  y solo las verá el repartidor              │
└─────────────────────────────────────────────┘
```

### Common Suggestions (Autocomplete)

- "Dejar en conserjería"
- "No tocar timbre, llamar al [phone]"
- "Dejar detrás de la maceta"
- "Entregar solo a [name]"
- "Llamar 15 minutos antes"

---

## Pickup Points (Retiro en Tienda)

### Selection UI

```
┌─────────────────────────────────────────────┐
│  🏪 Retiro en Tienda (Gratis)               │
│  ─────────────────────────────────────────  │
│                                             │
│  ○ 📍 Santiago Centro                       │
│    Huérfanos 1234, Local 56                 │
│    Lun-Vie 10:00-19:00, Sáb 10:00-14:00     │
│    Disponible en 24 horas                   │
│                                             │
│  ○ 📍 Providencia                           │
│    Av. Providencia 5678, Of. 12             │
│    Lun-Vie 09:00-18:00                      │
│    Disponible en 24 horas                   │
│                                             │
│  ─────────────────────────────────────────  │
│  📦 Retiro discreto: paquete genérico       │
│  🪪 Solo necesitas tu cédula y código       │
└─────────────────────────────────────────────┘
```

### Pickup Process

1. **Notification**: "Tu pedido está listo para retiro"
2. **Code**: 6-digit pickup code (SMS + email)
3. **ID required**: Cédula de identidad
4. **Discreet handoff**: Package in generic bag, no branding
5. **No questions asked**: Staff trained for privacy

---

## International Shipping (Future)

### Considerations

- **Customs declaration**: "Personal care items" or "Health products"
- **No explicit descriptions**: Never "adult toys" or "sexshop"
- **Neutral packaging**: Same as domestic
- **Longer delivery**: 7-15 business days
- **Higher cost**: $15.000-25.000 CLP

---

## Accessibility

- **Screen readers**: Announce "embalaje discreto incluido" on shipping selection
- **Icons**: All carrier logos have alt text
- **Copy button**: Announces "código copiado" on click
- **Tracking timeline**: Each step has descriptive label

---

## Mobile-Specific

- **Carrier logos**: Smaller, stack vertically
- **Price**: Right-aligned, larger font
- **Selection**: Full-width tap target
- **Tracking**: Horizontal scrollable timeline
- **Copy button**: Larger, easier to tap

---

## Testing Checklist

- [ ] All shipping methods display correctly
- [ ] Prices calculated by comuna (backend)
- [ ] "Embalaje discreto" badge visible on all options
- [ ] Tracking code copy works
- [ ] External tracking links open correctly
- [ ] Email notifications send at correct stages
- [ ] SMS opt-in/opt-out works
- [ ] Pickup points show correct hours
- [ ] Delivery instructions save correctly
- [ ] All copy follows guidelines (no shame language)
