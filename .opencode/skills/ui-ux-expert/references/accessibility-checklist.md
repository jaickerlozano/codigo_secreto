# Accessibility Checklist — WCAG AAA Compliance

## Color & Contrast

- [ ] All text meets 7:1 contrast ratio against background
- [ ] Large text (18pt+ or 14pt+ bold) meets 4.5:1 ratio
- [ ] UI components (buttons, inputs) meet 3:1 ratio
- [ ] Graphical objects (icons, charts) meet 3:1 ratio
- [ ] Color is never the only means of conveying information
- [ ] Focus indicators visible (3px outline, high contrast)
- [ ] Error states use icon + color, not color alone

## Typography

- [ ] Body text minimum 16px (1rem)
- [ ] Line height minimum 1.5 for body text
- [ ] Paragraph spacing minimum 1.5x line height
- [ ] Text can be resized up to 200% without loss of content
- [ ] No justified text (uneven spacing)
- [ ] Letter spacing adjustable by user
- [ ] Font family: sans-serif for UI, serif only for headlines

## Keyboard Navigation

- [ ] All interactive elements keyboard accessible
- [ ] Tab order follows visual order
- [ ] Focus visible on all interactive elements
- [ ] No keyboard traps (can always tab away)
- [ ] Skip navigation link available
- [ ] Escape key closes modals/dropdowns
- [ ] Arrow keys navigate within components (menus, tabs)

## Forms

- [ ] All inputs have visible labels (not placeholder-only)
- [ ] Labels positioned above or floating
- [ ] Required fields marked with asterisk + "requerido" text
- [ ] Error messages inline, below input
- [ ] Error messages specific (not "invalid input")
- [ ] Autocomplete enabled where appropriate
- [ ] Fieldsets group related inputs (radio, checkbox)
- [ ] Submit button not disabled until form valid

## Images & Media

- [ ] All images have alt text (descriptive, not "image")
- [ ] Decorative images have empty alt (alt="")
- [ ] Complex images have long description
- [ ] Videos have captions
- [ ] Audio has transcript
- [ ] No auto-playing media
- [ ] Media controls accessible

## Interactive Components

### Buttons
- [ ] Minimum 44x44px touch target
- [ ] Clear label (not icon-only without aria-label)
- [ ] Loading state announced to screen readers
- [ ] Disabled state visually distinct

### Links
- [ ] Underlined or clearly distinguished from text
- [ ] External links indicated (aria-label or icon)
- [ ] "Opens in new tab" announced

### Modals
- [ ] Focus trapped within modal
- [ ] Escape key closes modal
- [ ] Close button accessible
- [ ] Modal title announced
- [ ] Background content inert (aria-hidden)

### Dropdowns
- [ ] Arrow keys navigate options
- [ ] Enter/Space selects option
- [ ] Escape closes dropdown
- [ ] Selected state announced

### Tabs
- [ ] Arrow keys navigate tabs
- [ ] Tab panels associated with tabs (aria-controls)
- [ ] Active tab indicated visually and to screen readers

## Motion & Animation

- [ ] Respects prefers-reduced-motion
- [ ] No flashing content (3+ flashes per second)
- [ ] Animations can be paused/stopped
- [ ] Auto-rotating carousels have pause button
- [ ] Transitions under 250ms (not distracting)

## Responsive Design

- [ ] Content reflows at 320px width
- [ ] No horizontal scrolling at any breakpoint
- [ ] Touch targets minimum 44x44px on mobile
- [ ] Font sizes scale appropriately
- [ ] Images scale without loss of information

## Screen Readers

- [ ] Page title descriptive
- [ ] Headings hierarchical (h1 → h2 → h3)
- [ ] Landmarks defined (header, main, nav, footer)
- [ ] Live regions for dynamic content (aria-live)
- [ ] Status messages announced (role="status")
- [ ] Error messages announced (role="alert")
- [ ] Language declared (lang="es-CL")

## Testing Tools

### Automated
- [ ] axe DevTools: 0 critical/serious violations
- [ ] Lighthouse Accessibility: 90+ score
- [ ] WAVE: 0 errors

### Manual
- [ ] Keyboard-only navigation test completed
- [ ] Screen reader test (NVDA/VoiceOver) completed
- [ ] Zoom to 200% test completed
- [ ] High contrast mode test completed
- [ ] Reduced motion test completed

## Chilean Context

- [ ] RUT field validation accessible (format: 12.345.678-9)
- [ ] Phone field accepts Chilean format (+56 9 1234 5678)
- [ ] Address fields accommodate Chilean format (calle, número, depto)
- [ ] Region/Comuna dropdowns accessible
- [ ] Currency formatting accessible (CLP: $12.345)
