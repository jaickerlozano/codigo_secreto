# Guest email tracking link

## Objective

After a guest customer completes a purchase, send a confirmation email containing a secure link that lets that customer track the order without an account.

## Authorization and scope

- The user explicitly authorized this customer-facing feature on 2026-09-28.
- The link must use the existing capability-based guest access model; never expose a lookup by order number alone, credentials, tokens, or personally identifiable data in logs.
- The feature must work after the customer leaves the checkout confirmation page or uses another browser/device.
- Excluded until mapped: any production email provider configuration, remote delivery, `backend/.env`, Cloudinary, Neon, payments, tariff/catalog/image changes, and unrelated frontend work.

## Work items

- [ ] GUEST-TRACK-01 — Map the existing order confirmation, notification/email delivery, guest capability, and tracking-route flow.
- [ ] GUEST-TRACK-02 — Add a secure tracking URL to the appropriate guest confirmation email without changing account-holder behavior unnecessarily.
- [ ] GUEST-TRACK-03 — Add focused backend and frontend/contract tests for generation, delivery, access exchange, and invalid/missing capabilities.
- [ ] GUEST-TRACK-04 — Run applicable local verification, document results, and commit the completed work unit.

## Current evidence and constraints

- Existing frontend route: `/order/:orderNumber`; the initial guest capability is handled from a URL fragment (`#access=...`) and is removed after exchange.
- Current tracking statuses are `PAID`, `SHIPPED`, `DELIVERED`, and `CANCELLED`; the page already refreshes order data every 30 seconds.
- Local environment only: never auto-load `backend/.env`. Django commands require `PIPENV_DONT_LOAD_ENV=1`, `DJANGO_READ_DOTENV=0`, `DJANGO_SETTINGS_MODULE=core.settings_local`, and the project virtualenv.
- Branch: `feat/managed-postgresql-runtime`; local orders migration `0009_order_delivered_at` is applied. RDD clone-local mode is off and TDD is disabled by source #144.
- Prior fulfillment work is committed as `dcd69b4`; its local server is running at `127.0.0.1:8000` and the frontend at `127.0.0.1:5173`.

## Session handoff

- No source code has been changed for this feature.
- Required read-only mapping was delegated three times because it spans more than four files. Two attempts were rejected before execution with `Insufficient account funds`; the third was cancelled before returning a result.
- Do not retry blindly. On a new session, first map the flow in GUEST-TRACK-01, then update this document and its Engram mirror before the first source write.
- Engram mirror: observation `#1150`, topic `odd/guest-email-tracking/tasks`. Related historical context is recorded in observations `#279`, `#280`, and `#609`; verify it against current code before relying on it.

## Verification and rollback

- Verification is pending until the actual mail/notification integration is mapped. Use a local test backend or mock delivery only; do not send external mail without explicit remote authorization.
- Rollback boundary: revert only the eventual guest-email tracking-link work-unit commit. This tracking document can be removed independently if the feature is abandoned.
