# User Journey Map — Código Secreto

Complete user flow from first visit to post-purchase, optimized for trust, discretion, and education.

## Stage 1: Discovery (Landing / Homepage)

**User goal**: Understand what this store is, feel safe exploring.

**Touchpoints**:
- Hero section: elegant imagery (lifestyle, not product close-ups), tagline emphasizing discretion
- Trust badges: "Envío discreto", "Pago seguro", "Atención confidencial"
- Featured categories: icon + text, no explicit product images in navigation
- Educational content: blog posts, guides (linked from footer)

**Emotional state**: Cautious, evaluating trustworthiness.

**Design priorities**:
- Professional photography, no stock-photo clichés
- Clear value proposition above the fold
- Privacy policy link in header (not just footer)
- No popup modals on first visit (respect user intent)

**Success metrics**:
- Bounce rate < 40%
- Time on page > 45 seconds
- Scroll depth > 60%

---

## Stage 2: Exploration (Category / Product Listing)

**User goal**: Find products that match their needs without feeling judged.

**Touchpoints**:
- Category page with mega-menu navigation (max 3 levels)
- Advanced filters: material, experience level, price, brand
- Product cards: image → name → short description → price → "Ver detalles"
- Sort options: relevance, price, popularity, new arrivals

**Emotional state**: Curious but private, wants control over what they see.

**Design priorities**:
- Filters accessible without page reload (faceted search)
- Product images: clean, clinical aesthetic (white background, soft lighting)
- No "adult" language in product names or descriptions
- Quick view modal for product details without leaving list
- Wishlist/save functionality (local storage, no account required)

**Success metrics**:
- Filter usage rate > 30%
- Product detail page views > 2 per session
- Add to wishlist rate > 10%

---

## Stage 3: Consideration (Product Detail Page)

**User goal**: Understand the product fully, feel confident it's right for them.

**Touchpoints**:
- Hero image gallery (zoom, multiple angles)
- Tabbed content: Description, Materials & Safety, Usage Guide, Reviews
- Size/variant selector (if applicable)
- Stock indicator (low stock = urgency, but not fake scarcity)
- Related products (complementary, not upsell)
- "Agregar al carrito" button (primary CTA)

**Emotional state**: Evaluating, needs reassurance.

**Design priorities**:
- Education-first layout: description before price
- Material safety info prominent (hypoallergenic, body-safe certifications)
- Usage guide with diagrams (tasteful, not explicit)
- Reviews with verified purchase badges, filter by rating
- No countdown timers or fake scarcity tactics
- Clear return/exchange policy link

**Success metrics**:
- Time on page > 90 seconds
- Tab interaction rate > 50%
- Add to cart rate > 8%

---

## Stage 4: Commitment (Cart)

**User goal**: Review selections, understand total cost, proceed confidently.

**Touchpoints**:
- Slide-in cart (right side, not full page)
- Line items: image, name, variant, quantity, price
- Subtotal, shipping estimate, total
- "Continuar al checkout" button (primary)
- "Seguir comprando" link (secondary)
- Trust badges: "Embalaje discreto garantizado", "Pago seguro"

**Emotional state**: Ready but cautious, needs final reassurance.

**Design priorities**:
- Cart updates with subtle animation (slide-in, not modal)
- Quantity controls: +/- buttons, not dropdown
- Remove item: "Quitar" link, not trash icon (less aggressive)
- Shipping estimate based on comuna (if location known)
- Guest checkout option prominent (no account required)
- "Checkout discreto" language, not "Finalizar compra"

**Success metrics**:
- Cart abandonment rate < 70%
- Proceed to checkout rate > 30%
- Average cart value > $25,000 CLP

---

## Stage 5: Checkout (5-Step Discrete Flow)

**User goal**: Complete purchase with minimal friction, maximum privacy.

### Step 5.1: Contact Information

**Fields**:
- Email (required, for order confirmation)
- Phone (optional, for shipping updates only)
- "Continuar como invitado" (no account creation forced)

**Design**:
- Floating labels, inline validation
- Email autocomplete enabled
- Clear privacy notice: "Solo usamos tu email para confirmación de pedido"

### Step 5.2: Shipping Address

**Fields**:
- Full name
- Address line 1, line 2 (optional)
- Region (dropdown, Chilean regions)
- Comuna (dropdown, filtered by region)
- Postal code (optional)

**Design**:
- Region → Comuna cascading dropdowns
- Address autocomplete (if API available)
- "Esta dirección es confidencial" badge
- Save address for future (only if logged in)

### Step 5.3: Shipping Method

**Options**:
- Starken (2-4 días hábiles)
- Chilexpress (1-2 días hábiles)
- Bluexpress (3-5 días hábiles)
- Retiro en tienda (si aplica)

**Design**:
- Each option shows: logo, estimated delivery, cost
- "Embalaje discreto" badge on all options
- No option reveals product nature on label
- Free shipping threshold indicator (if applicable)

### Step 5.4: Payment Method

**Options**:
- Webpay (credit/debit cards)
- Flow (multiple payment methods)
- MercadoPago (cards, bank transfer)
- Transferencia bancaria (manual)

**Design**:
- Payment logos (official brand guidelines)
- "Pago 100% seguro" badge
- SSL/security icon
- Clear total with breakdown
- No payment info stored on our servers

### Step 5.5: Review & Confirm

**Summary**:
- Order items (image, name, quantity, price)
- Shipping address (masked after first line)
- Shipping method
- Payment method (masked card number)
- Total breakdown: subtotal, shipping, total

**Design**:
- Edit links for each section
- "Confirmar pedido" button (primary)
- Terms & conditions checkbox (required)
- Privacy policy link
- "Tu pedido será enviado en embalaje discreto" reminder

**Success metrics**:
- Checkout completion rate > 60%
- Average checkout time < 5 minutes
- Payment success rate > 95%

---

## Stage 6: Confirmation (Post-Purchase)

**User goal**: Know order was successful, track delivery discreetly.

**Touchpoints**:
- Order confirmation page (order number, summary)
- Email confirmation (discreet subject line: "Tu pedido #12345")
- SMS notification (optional, generic: "Tu pedido está en camino")
- Tracking link (opens carrier site, not our domain)

**Design**:
- Confirmation page: clean, reassuring
- Email: plain text option available, no product images
- No retargeting ads based on purchase
- Unsubscribe option in all communications

**Emotional state**: Relieved, satisfied.

**Success metrics**:
- Email open rate > 70%
- Return visit rate > 20%
- Repeat purchase rate > 15%

---

## Stage 7: Retention (Post-Delivery)

**User goal**: Feel valued, return for future purchases.

**Touchpoints**:
- Delivery confirmation email
- Review request (7 days post-delivery)
- Loyalty program (optional, points-based)
- Educational content (care guides, new product announcements)

**Design**:
- Review request: gentle, not pushy
- Loyalty program: privacy-first (no public profile)
- Content: educational, not promotional
- Unsubscribe always available

**Emotional state**: Satisfied, trusted.

**Success metrics**:
- Review submission rate > 10%
- Loyalty program enrollment > 25%
- Customer lifetime value > $150,000 CLP

---

## Anti-Patterns to Avoid

1. **Fake urgency**: No countdown timers, no "only 2 left!" unless true
2. **Aggressive upsells**: No "customers also bought" during checkout
3. **Forced account creation**: Guest checkout always available
4. **Explicit imagery**: No product photos in emails, no "adult" language
5. **Data hoarding**: Collect only what's needed for fulfillment
6. **Retargeting**: No ads following users around the web
7. **Public reviews**: Reviews are anonymous, no user profiles
8. **Pushy notifications**: Opt-in only, generic language

---

## Mobile-Specific Considerations

- **Thumb zone**: Primary CTAs in bottom 40% of screen
- **Touch targets**: Minimum 48x48px
- **Forms**: Native input types (email, tel, number)
- **Payments**: Apple Pay, Google Pay when available
- **Images**: Lazy loading, WebP format
- **Navigation**: Bottom nav bar (home, search, cart, account)
- **Filters**: Sheet modal, not inline
- **Checkout**: Progress indicator always visible

---

## Accessibility Priorities

- **Screen readers**: All images have alt text, form labels explicit
- **Keyboard navigation**: Tab order logical, focus visible
- **Color contrast**: WCAG AAA (7:1 ratio)
- **Font sizes**: Never below 16px for body text
- **Motion**: Respect prefers-reduced-motion
- **Language**: Spanish (Chile), formal but warm tone
