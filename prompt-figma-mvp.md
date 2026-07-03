# Prompt para Diseño UI/UX — Código Secreto (MVP)

## Contexto del Proyecto

**Código Secreto** es una tienda online de bienestar íntimo (sexshop) para el mercado chileno. El diseño debe transmitir confianza, discreción y modernidad, manteniendo un tono profesional pero acogedor.

**Audiencia objetivo**: Adultos 25-45 años en Chile, principalmente Región Metropolitana, que buscan productos de calidad con envío discreto y rápido.

---

## Identidad Visual

### Paleta de Colores (Neon Dark-First)

**Fondo principal**: Negro profundo (#0A0A0A) o gris muy oscuro (#1A1A1A)
**Texto principal**: Blanco (#FFFFFF) o gris claro (#E5E5E5)
**Acentos neón** (usar con moderación para CTAs y elementos interactivos):
- **Magenta**: #FF00FF o #E91E63 (CTAs principales, ofertas)
- **Cyan**: #00FFFF o #00BCD4 (links, información)
- **Violeta**: #9C27B0 o #7B1FA2 (categorías, badges)
- **Lime**: #CDDC39 o #8BC34A (éxito, stock disponible)

**Regla de uso**: Los acentos neón deben usarse SOLO en elementos interactivos (botones, links, badges importantes). El resto del diseño debe ser minimalista y oscuro para reducir fatiga visual y transmitir elegancia.

### Tipografía

- **Headings**: Sans-serif moderna, bold (ej: Inter, Poppins, o similar)
- **Body**: Sans-serif legible (ej: Inter, Roboto)
- **Tamaños**: Jerarquía clara (H1: 32-40px, H2: 24-28px, Body: 16px, Small: 14px)

### Estilo Visual

- **Bordes**: Redondeados suaves (8-12px para cards, 4-8px para botones)
- **Sombras**: Sutiles, solo para elevar elementos interactivos
- **Espaciado**: Generoso (padding 16-24px en cards, 32-48px entre secciones)
- **Iconografía**: Línea fina, minimalista, coherente con el tono neón

---

## Páginas Clave del MVP

### 1. **Homepage (Página de Inicio)**

**Estructura**:

```
[HEADER]
- Logo "Código Secreto" (izquierda)
- Barra de búsqueda centrada (placeholder: "¿Qué estás buscando?")
- Iconos: Cuenta | Favoritos | Carrito (con badge de cantidad)
- Menú de categorías (hover o click para desplegar)

[HERO SECTION]
- Banner principal con mensaje de valor:
  "Bienestar íntimo, entrega discreta"
  Subtítulo: "Envío mismo día en Santiago • 100% discreto"
- CTA principal: "Ver catálogo" (botón magenta neón)
- Badge de confianza: "🔒 Pago seguro con Webpay"

[BARRA DE BENEFICIOS]
- 3-4 iconos horizontales:
  ✓ Envío discreto
  ✓ Entrega mismo día
  ✓ Pago seguro
  ✓ Atención personalizada

[CATEGORÍAS DESTACADAS]
- Grid de 6-8 categorías principales con imágenes:
  • Vibradores
  • Lubricantes
  • Juguetes para parejas
  • Lencería
  • Bondage
  • Bienestar íntimo
- Cada card: imagen + nombre de categoría
- Hover: borde neón sutil (cyan o violeta)

[PRODUCTOS POPULARES]
- Título: "Los más vendidos"
- Grid de 4-8 productos (2 filas en desktop, scroll horizontal en mobile)
- Cada card de producto:
  • Imagen del producto (fondo blanco o gris claro para contraste)
  • Nombre del producto
  • Precio (formato CLP: $12.345)
  • Precio tachado si hay descuento + badge "% OFF" en magenta
  • Botón "Agregar al carrito" (aparece en hover)
  • Badge "Nuevo" o "Popular" si aplica

[SECCIÓN DE CONFIANZA]
- Título: "Tu privacidad es nuestra prioridad"
- 3 columnas con iconos:
  📦 Empaque 100% discreto (sin logos ni identificación)
  🔒 Pago seguro (Webpay, Flow, MercadoPago)
  🚚 Envío rápido (mismo día en Santiago)

[RESEÑAS DE CLIENTES]
- Carrusel de 3-4 testimonios
- Cada reseña:
  • Estrellas (4-5)
  • Texto breve (2-3 líneas)
  • Nombre (solo iniciales: "Valentina G.")
  • Badge "Compra verificada"

[FOOTER]
- 4 columnas:
  1. Sobre nosotros (breve descripción + logo)
  2. Categorías (links principales)
  3. Ayuda (FAQ, contacto, políticas)
  4. Contacto (email, WhatsApp, Instagram)
- Métodos de pago (logos: Webpay, Flow, MercadoPago, transferencia)
- Badges de seguridad (SSL, pago seguro)
- Copyright + links legales
```

---

### 2. **Página de Categoría**

**Estructura**:

```
[HEADER] (igual que homepage)

[BREADCRUMB]
- Inicio > Categoría > Subcategoría

[FILTROS Y ORDENAMIENTO]
- Sidebar izquierdo (desktop) o botón "Filtros" (mobile):
  • Precio (rango con slider)
  • Marca
  • Material
  • Color
  • Disponibilidad
- Ordenar por: Relevancia | Precio menor | Precio mayor | Más vendidos

[GRID DE PRODUCTOS]
- 3 columnas en desktop, 2 en tablet, 1 en mobile
- Cards de producto (igual que homepage)
- Paginación o scroll infinito

[SECCIÓN INFORMATIVA] (opcional)
- Texto SEO sobre la categoría
- Guía de compra breve
```

---

### 3. **Página de Producto**

**Estructura**:

```
[HEADER] (igual que homepage)

[BREADCRUMB]
- Inicio > Categoría > Producto

[GALERÍA DE IMÁGENES]
- Imagen principal grande (izquierda)
- Thumbnails verticales (4-6 imágenes)
- Zoom en hover
- Badge "Discreto" en esquina (ícono de caja cerrada)

[INFO DEL PRODUCTO]
- Nombre del producto (H1)
- Rating con estrellas + número de reseñas (link a reseñas)
- Precio: $XX.XXX (formato CLP)
- Precio tachado si hay descuento + badge "% OFF"
- Cuotas: "3 cuotas sin interés de $X.XXX" (si aplica)
- Stock: "✓ Disponible" (lime) o "Agotado" (gris)

[OPCIONES]
- Variantes (color, talla) si aplica
- Cantidad (selector +/-)

[CTAs]
- Botón principal: "Agregar al carrito" (magenta neón, grande)
- Botón secundario: "Agregar a favoritos" (ícono corazón)

[BENEFICIOS RÁPIDOS]
- 3 iconos pequeños:
  📦 Envío discreto
  🚚 Entrega mismo día
  🔒 Pago seguro

[DESCRIPCIÓN]
- Tabs: Descripción | Especificaciones | Reseñas
- Contenido claro, profesional, sin lenguaje explícito

[PRODUCTOS RELACIONADOS]
- "También te puede interesar"
- Grid de 4 productos similares
```

---

### 4. **Carrito de Compras**

**Estructura**:

```
[HEADER] (igual que homepage)

[TÍTULO]
- "Tu carrito" + número de items

[LISTA DE PRODUCTOS]
- Cada item:
  • Imagen pequeña
  • Nombre + variante (si aplica)
  • Precio unitario
  • Selector de cantidad (+/-)
  • Subtotal
  • Botón eliminar (ícono papelera)

[RESUMEN DEL PEDIDO]
- Subtotal: $XX.XXX
- Envío: $X.XXX (o "Gratis" si aplica)
- Descuento (si hay cupón): -$X.XXX
- **Total: $XX.XXX** (destacado, tamaño grande)

[CTAs]
- Botón principal: "Continuar al pago" (magenta neón)
- Botón secundario: "Seguir comprando" (texto)

[BADGES DE CONFIANZA]
- "🔒 Pago 100% seguro y encriptado"
- "Nunca almacenamos tus datos de tarjeta"
- Logos de métodos de pago
```

---

### 5. **Checkout (Pago)**

**Estructura**:

```
[HEADER SIMPLIFICADO]
- Logo centrado
- Sin menú de navegación (para evitar distracciones)

[PROGRESO]
- Steps: 1. Datos → 2. Envío → 3. Pago

[FORMULARIO DE DATOS]
- Nombre completo
- Email
- Teléfono
- Dirección (calle, número, depto, comuna, ciudad)
- Notas de entrega (opcional)

[OPCIONES DE ENVÍO]
- Envío estándar: $X.XXX (2-3 días)
- Envío express: $X.XXX (mismo día, antes de las 16:00)
- Badge: "📦 Empaque 100% discreto"

[MÉTODOS DE PAGO]
- Título: "Elige tu método de pago"
- Opciones (radio buttons):
  
  ○ 💳 Webpay (recomendado)
    Pago seguro con tarjetas
    [Logos: Visa, Mastercard, Amex, Diners]
    "Nunca almacenamos tus datos de tarjeta"
  
  ○ 🌊 Flow
    Múltiples métodos de pago
    "Acepta tarjetas, transferencia y más"
  
  ○ 💙 MercadoPago
    Hasta 12 cuotas sin interés
    "Protección al comprador incluida"
  
  ○ 🏦 Transferencia Bancaria
    Pago manual
    "Confirmación en 24-48 horas hábiles"

[RESUMEN DEL PEDIDO]
- Lista de productos (imagen pequeña + nombre + cantidad + precio)
- Subtotal, envío, total
- Checkbox: "Acepto los términos y condiciones"

[BOTÓN DE PAGO]
- "Pagar $XX.XXX" (magenta neón, grande)
- Badge: "🔒 Pago seguro SSL"

[SEÑALES DE CONFIANZA]
- "Tus datos están protegidos con encriptación SSL"
- "Empaque discreto garantizado"
- "Soporte: contacto@codigosecreto.cl"
```

---

### 6. **Página de Confirmación**

**Estructura**:

```
[HEADER SIMPLIFICADO]

[MENSAJE DE ÉXITO]
- Ícono de check (lime neón)
- "¡Pedido confirmado!"
- Número de orden: #12345
- "Te enviamos un email con los detalles"

[RESUMEN DEL PEDIDO]
- Productos comprados
- Total pagado
- Método de pago usado
- Dirección de envío

[PRÓXIMOS PASOS]
- "Tu pedido será enviado en empaque discreto"
- "Recibirás un código de seguimiento por email"
- "Entrega estimada: [fecha]"

[CTAs]
- "Ver estado del pedido"
- "Seguir comprando"
```

---

## Mejoras sobre la Referencia (sexshop-santiago.cl)

### Lo que SÍ mantener:
- ✅ Estructura clara de categorías
- ✅ Productos destacados con precios tachados
- ✅ Reseñas de clientes
- ✅ Badges de confianza (pago seguro, envío discreto)
- ✅ Banner de envío mismo día

### Lo que MEJORAR:

1. **Hero Section**:
   - ❌ Referencia: Banner genérico con descuento
   - ✅ Mejora: Hero con mensaje de valor claro ("Bienestar íntimo, entrega discreta") + CTA directo + badge de confianza

2. **Navegación**:
   - ❌ Referencia: Menú de categorías muy largo y plano
   - ✅ Mejora: Menú con subcategorías organizadas, búsqueda prominente, iconos claros

3. **Cards de Producto**:
   - ❌ Referencia: Información básica, sin jerarquía visual
   - ✅ Mejora: Cards con hover state, badges de descuento/stock, botón "Agregar" que aparece en hover, mejor espaciado

4. **Sección de Confianza**:
   - ❌ Referencia: Información dispersa en el footer
   - ✅ Mejora: Sección dedicada con 3 pilares (discreción, seguridad, rapidez) + iconos neón

5. **Checkout**:
   - ❌ Referencia: Proceso de pago estándar
   - ✅ Mejora: Checkout simplificado con progreso visual, métodos de pago chilenos claros, señales de confianza en cada paso

6. **Mobile**:
   - ❌ Referencia: Adaptación básica
   - ✅ Mejora: Diseño mobile-first, touch targets grandes (min 44px), menú hamburguesa, búsqueda accesible

7. **Accesibilidad**:
   - ❌ Referencia: Contraste bajo en algunos textos
   - ✅ Mejora: Contraste AA mínimo, focus states visibles, labels claros en formularios

8. **Performance**:
   - ❌ Referencia: Imágenes sin optimizar
   - ✅ Mejora: Imágenes WebP, lazy loading, skeleton screens para carga

---

## Componentes Reutilizables

### Botones
- **Primary**: Fondo magenta neón, texto blanco, border-radius 8px, hover con brillo sutil
- **Secondary**: Borde cyan, texto cyan, fondo transparente, hover con fondo cyan transparente
- **Ghost**: Solo texto, hover con underline

### Cards
- **Producto**: Fondo gris oscuro (#1A1A1A), borde sutil, hover con elevación y borde neón
- **Categoría**: Imagen completa, overlay oscuro con texto blanco, hover con zoom suave

### Badges
- **Descuento**: Fondo magenta, texto blanco ("% OFF")
- **Nuevo**: Fondo violeta, texto blanco
- **Stock**: Fondo lime, texto oscuro ("Disponible")
- **Agotado**: Fondo gris, texto blanco

### Inputs
- Fondo gris oscuro (#2A2A2A), borde gris claro, focus con borde cyan
- Labels claros arriba del input
- Error: borde rojo + mensaje debajo

### Modales
- Fondo oscuro con blur
- Card centrada con bordes redondeados
- Botón de cerrar (X) en esquina superior derecha

---

## Moodboard y Referencias Visuales

**Inspiración de estilo**:
- Diseño dark mode moderno (ej: Linear, Vercel, Stripe)
- E-commerce de lujo minimalista (ej: Graza, Allbirds)
- Paleta neón sutil (ej: sitios de música electrónica, festivales)

**Tono visual**:
- Profesional pero acogedor
- Discreto pero no aburrido
- Moderno pero accesible
- Confiable pero no corporativo

---

## Entregables Esperados

1. **Homepage** (desktop + mobile)
2. **Página de Categoría** (desktop + mobile)
3. **Página de Producto** (desktop + mobile)
4. **Carrito** (desktop + mobile)
5. **Checkout** (desktop + mobile)
6. **Confirmación** (desktop + mobile)
7. **Componentes** (botones, cards, badges, inputs, modales)
8. **Guía de estilo** (colores, tipografía, espaciado, iconografía)

---

## Notas Finales

- **Privacidad**: El diseño debe transmitir discreción sin ser oscuro o intimidante
- **Confianza**: Badges de seguridad, reseñas, y señales de pago seguro son CRÍTICOS
- **Mobile-first**: La mayoría del tráfico será mobile, priorizar esa experiencia
- **Performance**: Diseño optimizado para carga rápida (imágenes, animaciones sutiles)
- **Accesibilidad**: Contraste AA, focus states, navegación por teclado

**Éxito del diseño**: Un usuario debe sentirse cómodo, seguro y en control durante toda la experiencia de compra, desde la navegación hasta el pago.
