# Guest email tracking link

## Objective

After a guest customer completes a purchase, send a confirmation email containing a secure link that lets that customer track the order without an account.

## Authorization and scope

- The user explicitly authorized this customer-facing feature on 2026-09-28.
- The link must use the existing capability-based guest access model; never expose a lookup by order number alone, credentials, tokens, or personally identifiable data in logs.
- The feature must work after the customer leaves the checkout confirmation page or uses another browser/device.
- Excluded until mapped: any production email provider configuration, remote delivery, `backend/.env`, Cloudinary, Neon, payments, tariff/catalog/image changes, and unrelated frontend work.
- Approved SMTP extension: configure Django email only through explicitly supplied environment settings. The future Gmail SMTP sender is authorized by the account holder, but no credential exists yet; this work must remain local and must not read or modify any real `.env`, authenticate to, connect to, or send through Gmail/SMTP.
- Account-holder extension: payment-confirmation email for an authenticated order may include the normal frontend order route without a ticket or fragment. Existing authenticated backend authorization remains the boundary; an order number alone must not disclose an order to an unauthenticated recipient.

## Work items

- [x] GUEST-TRACK-01 — Map the existing order confirmation, notification/email delivery, guest capability, and tracking-route flow.
- [x] GUEST-TRACK-02 — Add a secure tracking URL to the appropriate guest confirmation email without changing account-holder behavior unnecessarily.
- [x] GUEST-TRACK-03 — Add focused backend and frontend/contract tests for generation, delivery, access exchange, and invalid/missing capabilities.
- [x] GUEST-TRACK-04 — Run applicable local verification, document results, and commit the completed work unit.
- [x] GUEST-TRACK-05 — Add environment-backed SMTP settings with safe local fallback and fail-closed production behavior.
- [x] GUEST-TRACK-06 — Add the capability-free authenticated account-holder payment-confirmation order link.
- [x] GUEST-TRACK-07 — Add focused SMTP configuration and guest/account-holder email-body tests without network delivery.
- [x] GUEST-TRACK-08 — Run required local verification and commit this SMTP/account-holder extension as one work unit.
- [x] GUEST-TRACK-10 — Add isolated `core.settings_local` integration coverage for console fallback, explicit SMTP preservation, and the test-only locmem override without loading dotenv files or making network connections.
- [ ] GUEST-TRACK-09 — Perform a credential-gated live Gmail SMTP verification only after the account holder adds credentials locally and explicitly authorizes the connection.

## Final evidence and constraints

- Existing frontend route: `/order/:orderNumber`; the initial guest capability is handled from a URL fragment (`#access=...`) and is removed after exchange.
- Current tracking statuses are `PAID`, `SHIPPED`, `DELIVERED`, and `CANCELLED`; the page already refreshes order data every 30 seconds.
- Local environment only: never auto-load `backend/.env`. Django commands require `PIPENV_DONT_LOAD_ENV=1`, `DJANGO_READ_DOTENV=0`, `DJANGO_SETTINGS_MODULE=core.settings_local`, and the project virtualenv.
- Branch: `feat/managed-postgresql-runtime`; local orders migration `0009_order_delivered_at` is applied. RDD mode is `off` (`clone_local`), so review is intentionally unmanaged and must not be invoked or enabled.
- Prior fulfillment work is committed as `dcd69b4`; its local server is running at `127.0.0.1:8000` and the frontend at `127.0.0.1:5173`.
- Verified map: guest checkout creates one opaque 90-day capability and stores only its SHA-256 digest. The raw token cannot be recovered after checkout. Payment approval synchronously schedules confirmation after commit. The frontend exchanges `#access=...` only through `X-Order-Capability`, removes the fragment, and receives the existing Strict HttpOnly access cookie. Opaque capability validation and masked-404 behavior remain unchanged.
- GUEST-TRACK-01 (delegated mapping) route/trigger evidence: the cross-file map established that payment approval triggers the guest `payment_confirmation` notification in `backend/apps/orders/notifications.py`; the backend header exchange is the only acceptance boundary; the existing frontend tracking route consumes and clears the fragment.
- GUEST-TRACK-02 (direct implementation evidence) route/trigger: commit `4fdf814` adds the guest-only signed email capability and injects it into the `payment_confirmation` delivery path that payment approval triggers; account-holder behavior remains unchanged.
- GUEST-TRACK-03 (direct test evidence) route/trigger: commit `4fdf814` adds backend coverage for signed-ticket generation, guest delivery, header exchange, invalid capability handling, revocation, retry stability, and redaction; the unchanged frontend contract test remains the proof for fragment-to-header exchange and fragment cleanup.
- GUEST-TRACK-04 (direct evidence update) route/trigger: this tracker records the completed implementation and verification evidence below, while deployment must apply the pending migration through the normal process.
- GUEST-TRACK-05 through GUEST-TRACK-08 (delegated route/trigger evidence): this extension spans Django settings and local-settings behavior, order notification rendering/delivery, and focused configuration/notification tests. The exact remote authorization boundary is local-only work: do not read, create, or modify real `.env` files; do not access, authenticate to, connect to, or send through Gmail/SMTP. Live verification is deferred to GUEST-TRACK-09 after credentials are added by the account holder and a new explicit authorization is provided.
- Email-link constraints: use a separate signed email-channel capability with its own Order version/revocation state; never persist or log its raw ticket, do not rotate opaque guest capability tokens on delivery retries, and use only local/locmem or mocked delivery.

## Implementation evidence

- Implementation: `Order` now holds a separate email-link version and revocation timestamp. Django timestamp signing uses the purpose-specific `orders.guest-email-access` salt and the existing 90-day guest policy. Only the header exchange action accepts this ticket, then issues the existing Strict HttpOnly cookie; opaque capability behavior is unchanged.
- Delivery: guest `payment_confirmation` bodies retain `ORDER_TRACKING_PUBLIC_ORIGIN/order/<order-number>#access=<ticket>`. Authenticated account-holder bodies include the same normal route without a ticket or fragment; the existing owner/staff authorization and masked 404 remain the access boundary. Dispatch emails remain unchanged. Retry creates a current signed ticket without rotating either version, and ticket-bearing delivery exceptions are redacted from persisted errors and logs.
- SMTP configuration: the supported production contract now requires `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS=True`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and `DEFAULT_FROM_EMAIL`. Development retains console delivery when SMTP is absent; `settings_local` preserves explicitly supplied SMTP values, while `LOCAL_TEST_DATABASE=1` always uses locmem. Production rejects absent, console, or non-TLS email configuration during settings load.
- Tests: `test_guest_email_tracking.py` covers signed payload creation, guest/account-holder link separation, header-only exchange with empty response, masked tampering/expiry/revocation/foreign-ticket failures, version invalidation, retry stability, and error redaction. `core/tests/test_email_settings.py` and `core/tests/test_security_settings.py` cover explicit backend selection, safe fallback, and production rejection. Existing `frontend/src/features/orders/api/orders.api.test.ts` remains the contract proof that fragment-only values go to `X-Order-Capability`, are removed, and query/path proofs are not exchanged; no frontend source changed.
- GUEST-TRACK-10: isolated subprocess imports of `core.settings_local` now prove console fallback with no SMTP values, preservation of explicit safe test SMTP values, and locmem precedence when `LOCAL_TEST_DATABASE=1`. The tests only load settings and never instantiate an SMTP connection; production settings remain unchanged because the intended behavior is present.

## Verification and rollback

- Mapping evidence: GUEST-TRACK-01 completed through delegated cross-file mapping.
- Commit evidence: GUEST-TRACK-02 and GUEST-TRACK-03 completed in `4fdf814`; earlier evidence was recorded in `c7fee0d`.
- Final functional spot check, from `backend/`: `LOCAL_TEST_DATABASE=1 PIPENV_DONT_LOAD_ENV=1 DJANGO_READ_DOTENV=0 DJANGO_SETTINGS_MODULE=core.settings_local pipenv run pytest apps/orders` — `210 passed, 1 skipped in 14.21s`. The `LOCAL_TEST_DATABASE=1` override is required because the local profile otherwise intentionally opens PostgreSQL read-only and pytest cannot create its disposable database.
- Frontend build: N/A; no frontend source or test changed. Narrow frontend test: N/A for the same reason; its existing fragment/header/cleanup contract test remains unchanged.
- Native assessment against base `c85bb47` and committed work reported risk `medium`, 9 paths, 272 changed lines, and `review_due: false` with `review_due_reason: under_budget`. RDD is disabled, so review remains intentionally unmanaged; no review was invoked or enabled.
- Pending operational action: apply migration `0010_order_guest_email_access` during the normal deployment process.
- Required verification, from `backend/`: `LOCAL_TEST_DATABASE=1 PIPENV_DONT_LOAD_ENV=1 DJANGO_READ_DOTENV=0 DJANGO_SETTINGS_MODULE=core.settings_local pipenv run pytest apps/orders core/tests` — `344 passed, 1 skipped in 20.02s`. The full target includes the new settings tests, so no narrower settings command was needed. No SMTP network connection was attempted.
- Frontend build: N/A; no frontend source changed, because the existing `/order/:orderNumber` route already enforces authenticated authorization through the backend.
- Delivery forecast: one Conventional Commit work unit, under the 400-line review budget; final changed-line count and commit hash are recorded in the delivery report because a commit cannot contain its own hash.
- RDD remains disabled and unmanaged (`clone_local`); no RDD review was invoked or enabled.
- Pending user action: add the documented Gmail TLS variables to the untracked local `.env`, then explicitly authorize GUEST-TRACK-09 before any live SMTP verification. The app password must never be committed, logged, or supplied to an agent.
- Rollback boundary: revert this extension commit to remove SMTP contract validation, local SMTP preservation, account-holder route-only links, tests, and documentation without changing the prior guest ticket implementation. Revert `4fdf814` separately only to remove the earlier guest-email capability feature.
- GUEST-TRACK-10 verification, from `backend/`: `LOCAL_TEST_DATABASE=1 PIPENV_DONT_LOAD_ENV=1 DJANGO_READ_DOTENV=0 DJANGO_SETTINGS_MODULE=core.settings_local pipenv run pytest apps/orders core/tests` — `347 passed, 1 skipped in 18.23s`. No SMTP connection, migration, or business-data mutation was attempted. RDD remains disabled and unmanaged (`clone_local`); native assessment is unassessable, and no review was invoked or enabled. Rollback boundary: revert the corrective commit to remove only the isolated settings tests and this tracker evidence; production settings are unchanged.
