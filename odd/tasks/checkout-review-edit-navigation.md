# Checkout Review Edit Navigation

## Goal
Every review Edit button must open its named section and retain existing checkout data.

## Evidence and decision
Review Contact and Address both emit step 1 (Datos). StepData chooses its internal contact/address form solely from authentication/phone validity, so authenticated users editing Contact land on Address and guests editing Address land on Contact. Shipping/payment already map to steps 2/3. The reported Address-to-Shipping route is not demonstrated by code. Keep the four existing steps; carry explicit section intent to StepData and orient focus to the intended form.

## Scope and constraints
Preserve entered fields, authentication/profile field rules, quote invalidation, inventory checks, server-owned totals, payment behavior and scroll restoration. No new endpoints/API types, backend/profile mutations, tokens/storage, step renumbering, real orders/payment/login actions, secrets or container lifecycle. Preserve unrelated README/bytecode/recovery-file changes. No commit/push without authorization.

## Execution
Delegated writer (multiple component/test edits), strict TDD disabled per existing ODD session mode; ordinary functional verification required. Forecast 100-250 authored diff lines; ask-on-risk delivery strategy, advisory size heuristic only.

## Tasks
- [x] EN-1: Thread explicit contact/address edit intent through review and page into StepData; preserve normal defaults and focus/state.
- [x] EN-2: Add regression tests for guest/authenticated contact/address and shipping/payment targets, data retention, default navigation, and accessible focus.
- [x] EN-3: Run focused/full tests, production build and assessment/independent verification as required.
- [x] EN-4: Commit/push authorized; correction published on `fix/checkout-review-edit-targets`.

## Verification
From frontend with LOCAL_NO_DOTENV=1: `pnpm exec vitest run src/features/checkout/components/steps/StepReview.test.tsx src/features/checkout/components/steps/StepData.test.tsx src/features/checkout/pages/CheckoutPage.test.tsx`; `pnpm exec vitest run`; `pnpm run build`. Targeted diff whitespace check on changed paths.

## Acceptance
Contact Edit opens Contact even for an authenticated valid-phone user. Address Edit opens Address for guest and authenticated buyers without discarding Contact. Shipping/Payment target their existing sections. Repeated edits/back navigation preserve form data and normal initialization; changing address retains existing quote/shipping invalidation behavior. Section focus is keyboard-accessible.

## Progress and evidence
EN-1/2/3 complete locally:
- Writer: 28 focused tests passed; full frontend suite 335 passed across 69 files; production build and targeted whitespace check passed.
- Independent verifier: 28 focused tests passed, build and whitespace check passed; intent targeting, focus, data retention, authenticated read-only rules and comuna invalidation confirmed.
- Parent readback: review emits Contact(1,contact), Address(1,address), Shipping(2), Payment(3) with distinct accessible labels.
- Edit intent expires after leaving Datos; internal Back retains address drafts. No profile, pricing, quote, inventory, payment or step-numbering changes.
- Native ASSESS unavailable due to untracked declarations; required independent verification completed. No native approved receipt claimed.
- Build emitted existing bundle-size/plugin-timing warnings, no errors. Browser/manual assistive-technology checks not performed.

## Next step
Manual review-button verification remains pending. Source commit `965abd7` pushed to `origin/fix/checkout-review-edit-targets`; local/remote source heads matched. Fresh independent verification of the committed range passed 28 tests and whitespace/scope checks. User selected separate deliveries to verified default `main` (`stacked-to-main`): checkout and virtualenv documentation are independent units. No PR or merge performed. Bytecode/recovery-task files excluded; virtualenv documentation delivered separately. Actual admin/frontend login verification remains separate; no real login/order/payment action performed.
