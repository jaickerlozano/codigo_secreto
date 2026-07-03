# Chilean Payment Patterns — UI Integration

## Overview

Chilean eCommerce payment landscape requires trust-first UI patterns. Users are cautious about online payments, especially for sensitive purchases.

## Payment Methods

### 1. Webpay (Transbank)

**Market share**: ~60% of Chilean eCommerce
**Types**: Credit cards, debit cards, prepaid cards

**UI Requirements**:
- Official Webpay logo (blue/white)
- "Pago seguro con Webpay" badge
- Card brand logos (Visa, Mastercard, Amex, Diners)
- SSL/security icon near payment button

**Integration Pattern**:
```
┌─────────────────────────────────────┐
│  💳 Pagar con Webpay                │
│  ─────────────────────────────────  │
│  [Visa] [Mastercard] [Amex] [Diners]│
│                                     │
│  Pago 100% seguro y encriptado      │
└─────────────────────────────────────┘
```

**User Flow**:
1. User clicks "Pagar con Webpay"
2. Redirect to Webpay secure page (webpay.cl)
3. User enters card details on Webpay site
4. Redirect back to confirmation page
5. Status check via webhook (backend)

**Trust Signals**:
- "Nunca almacenamos tus datos de tarjeta"
- "Transbank procesa tu pago de forma segura"
- Lock icon in browser address bar

---

### 2. Flow

**Market share**: ~25% of Chilean eCommerce
**Types**: Credit/debit cards, bank transfer, Flow balance

**UI Requirements**:
- Official Flow logo (green/white)
- "Paga con Flow" badge
- Multiple payment method icons

**Integration Pattern**:
```
┌─────────────────────────────────────┐
│  🌊 Pagar con Flow                  │
│  ─────────────────────────────────  │
│  [Tarjetas] [Transferencia] [Saldo] │
│                                     │
│  Múltiples métodos de pago          │
└─────────────────────────────────────┘
```

**User Flow**:
1. User clicks "Pagar con Flow"
2. Redirect to Flow checkout (flow.cl)
3. User selects payment method
4. Complete payment on Flow site
5. Redirect back + webhook confirmation

**Trust Signals**:
- "Flow es líder en pagos online en Chile"
- "Acepta tarjetas, transferencia y más"
- "Pago procesado de forma segura"

---

### 3. MercadoPago

**Market share**: ~10% of Chilean eCommerce
**Types**: Credit/debit cards, bank transfer, MercadoPago balance

**UI Requirements**:
- Official MercadoPago logo (blue/yellow)
- "Paga con MercadoPago" badge
- "Hasta 12 cuotas sin interés" (if applicable)

**Integration Pattern**:
```
┌─────────────────────────────────────┐
│  💙 Pagar con MercadoPago           │
│  ─────────────────────────────────  │
│  [Tarjetas] [Transferencia] [Saldo] │
│                                     │
│  Hasta 12 cuotas sin interés        │
└─────────────────────────────────────┘
```

**User Flow**:
1. User clicks "Pagar con MercadoPago"
2. Redirect to MercadoPago checkout
3. Login to MercadoPago account (or guest)
4. Select payment method
5. Redirect back + webhook confirmation

**Trust Signals**:
- "MercadoPago protege tu compra"
- "Programa de protección al comprador"
- "Millones de usuarios en Latinoamérica"

---

### 4. Transferencia Bancaria

**Market share**: ~5% of Chilean eCommerce
**Types**: Manual bank transfer

**UI Requirements**:
- Bank logos (Banco de Chile, Santander, BCI, etc.)
- Clear instructions with account details
- "Pago manual" label

**Integration Pattern**:
```
┌─────────────────────────────────────┐
│  🏦 Transferencia Bancaria          │
│  ─────────────────────────────────  │
│  Banco: Banco Estado                │
│  Tipo cuenta: Cuenta Vista          │
│  Número: 12345678901                │
│  RUT: 12.345.678-9                  │
│  Email: pagos@codigosecreto.cl      │
│                                     │
│  Envía comprobante a:               │
│  pagos@codigosecreto.cl             │
└─────────────────────────────────────┘
```

**User Flow**:
1. User selects "Transferencia Bancaria"
2. Order created with status PENDING
3. User receives email with bank details
4. User completes transfer manually
5. User sends proof of payment
6. Admin verifies and updates order status

**Trust Signals**:
- "Pago directo, sin intermediarios"
- "Confirmación en 24-48 horas hábiles"
- "Soporte personalizado"

---

## Payment Selection UI

### Layout Pattern

```
┌─────────────────────────────────────────────┐
│  Método de Pago                             │
│  ─────────────────────────────────────────  │
│                                             │
│  ○ 💳 Webpay (recomendado)                  │
│    Pago seguro con tarjetas                 │
│                                             │
│  ○ 🌊 Flow                                  │
│    Múltiples métodos de pago                │
│                                             │
│  ○ 💙 MercadoPago                           │
│    Hasta 12 cuotas sin interés              │
│                                             │
│  ○ 🏦 Transferencia Bancaria                │
│    Pago manual                              │
│                                             │
│  ─────────────────────────────────────────  │
│  🔒 Pago 100% seguro y encriptado           │
│  Nunca almacenamos tus datos de tarjeta     │
└─────────────────────────────────────────────┘
```

### Design Principles

1. **Recommended option first**: Webpay (most trusted)
2. **Clear descriptions**: What each method accepts
3. **Trust badges**: Security icons, encryption mentions
4. **No hidden fees**: Show total before payment
5. **Mobile-friendly**: Large touch targets, clear labels

---

## Error Handling

### Payment Failed

```
┌─────────────────────────────────────────────┐
│  ⚠️ Pago no aprobado                        │
│  ─────────────────────────────────────────  │
│  Tu pago no pudo ser procesado.             │
│                                             │
│  Posibles causas:                           │
│  • Saldo insuficiente                       │
│  • Tarjeta bloqueada                        │
│  • Datos incorrectos                        │
│                                             │
│  [Intentar nuevamente] [Cambiar método]     │
│                                             │
│  ¿Necesitas ayuda? Contáctanos              │
└─────────────────────────────────────────────┘
```

### Payment Pending (Bank Transfer)

```
┌─────────────────────────────────────────────┐
│  ⏳ Pago pendiente                          │
│  ─────────────────────────────────────────  │
│  Tu pedido está en espera de pago.          │
│                                             │
│  Realiza la transferencia en 48 horas       │
│  para mantener tu pedido activo.            │
│                                             │
│  [Ver instrucciones] [Cancelar pedido]      │
└─────────────────────────────────────────────┘
```

---

## Security Badges

### Placement

- **Checkout page**: Near payment selection
- **Cart page**: Below total
- **Footer**: Site-wide trust signals

### Badge Examples

```
🔒 Pago seguro SSL
🛡️ Datos protegidos
✓ Transbank certificado
✓ Flow verificado
```

---

## Currency Formatting

### Chilean Peso (CLP)

- **Symbol**: $ (before number)
- **Separator**: . (dot for thousands)
- **No decimals**: $12.345 (not $12.345,00)

### Examples

```
$1.234      (mil doscientos treinta y cuatro)
$12.345     (doce mil trescientos cuarenta y cinco)
$123.456    (ciento veintitrés mil cuatrocientos cincuenta y seis)
$1.234.567  (un millón doscientos treinta y cuatro mil quinientos sesenta y siete)
```

### UI Pattern

```
Subtotal:        $45.990
Envío:           $3.500
─────────────────────────
Total:           $49.490
```

---

## Installments (Cuotas)

### Display Pattern

```
┌─────────────────────────────────────────────┐
│  💳 Opciones de pago                        │
│  ─────────────────────────────────────────  │
│  1 cuota de $49.490                         │
│  3 cuotas sin interés de $16.497            │
│  6 cuotas sin interés de $8.249             │
│  12 cuotas sin interés de $4.125            │
└─────────────────────────────────────────────┘
```

### Rules

- **Sin interés**: No interest charged
- **Con interés**: Interest applies (show total)
- **Minimum installment**: $3.000 CLP (typical)
- **Always show**: Number of installments + amount per installment

---

## Mobile Payment Patterns

### Apple Pay / Google Pay

```
┌─────────────────────────────────────────────┐
│  [ Apple Pay ]  [ Google Pay ]              │
│  ─────────────────────────────────────────  │
│  Pago rápido y seguro                       │
└─────────────────────────────────────────────┘
```

### Placement

- **Above other methods**: Fastest option first
- **Product page**: "Buy Now" button (if applicable)
- **Cart page**: Express checkout option

---

## Testing Checklist

- [ ] All payment methods displayed correctly
- [ ] Logos load from CDN (not local)
- [ ] Currency formatted correctly (CLP)
- [ ] Installments calculated correctly
- [ ] Error messages clear and helpful
- [ ] Success flow redirects correctly
- [ ] Webhook endpoints configured (staging + production)
- [ ] Test mode enabled in development
- [ ] SSL certificate valid
- [ ] PCI compliance documented
