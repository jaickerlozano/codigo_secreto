# Production security configuration

Production deployment remains blocked until the deployment owner supplies the approved topology and the release owner records the required evidence. This runbook documents formats and responsibilities only; it contains no secrets and API hostname remains unassigned.

## Quick path

`core.settings_local` is intentionally incompatible with production: it forces
loopback PostgreSQL, mock payments, offline media storage, and email capture
through loopback Mailpit. It ignores inherited SMTP configuration and cannot be
redirected to an external SMTP host. Production must keep using `core.settings`
with deployment-injected values.

1. Use the environment examples only as local-development references and format guides.
2. Have the deployment owner and secret custodian supply approved values outside the repository.
3. Run the checks below, retain their outputs, and complete every rollout gate before release.

## Ownership and boundaries

| Owner            | Responsibility                                                                                             | Must not do                                                                                   |
| ---------------- | ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Deployment owner | Assign the API hostname, controlled parent domain, exact origins, cookie topology, and proxy/TLS behavior. | Infer an API hostname or relax a validation failure.                                          |
| Secret custodian | Inject runtime secrets through the approved secret manager.                                                | Put secrets in `.env.example`, frontend variables, documentation, source, or command history. |
| Release owner    | Retain check results, browser-journey evidence, and external documentation-denial evidence.                | Approve rollout from application routing alone.                                               |

## Required configuration

### Backend topology and policy

| Variable                                       | Safe format                            | Owner            | Validation                                                                 |
| ---------------------------------------------- | -------------------------------------- | ---------------- | -------------------------------------------------------------------------- |
| `ENVIRONMENT`                                  | `production`                           | Deployment owner | Production is explicit.                                                    |
| `DEBUG`                                        | `False`                                | Deployment owner | Production startup rejects enabled debug mode.                             |
| `FRONTEND_ORIGIN`                              | `https://<assigned-frontend-hostname>` | Deployment owner | Must be the exact trusted HTTPS origin.                                    |
| `API_HOSTNAME`, `ALLOWED_HOSTS`                | `<assigned-api-hostname>`              | Deployment owner | API hostname must be assigned and allowlisted.                             |
| `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` | `https://<assigned-frontend-hostname>` | Deployment owner | Must exactly match the approved frontend origin.                           |
| `COOKIE_TOPOLOGY`                              | `shared-parent`                        | Deployment owner | Current CSRF flow permits only the approved shared-parent topology.        |
| `COOKIE_SITE_DOMAIN`                           | `<controlled-parent-domain>`           | Deployment owner | Must be a controlled, non-public-suffix parent of both approved hosts.     |
| `TLS_TERMINATION`, `NUM_PROXIES`               | `proxy`, positive integer              | Deployment owner | The network boundary must strip spoofed forwarded headers.                 |
| `SECURE_HSTS_SECONDS`                          | positive integer, initially `3600`     | Release owner    | Increase only after HTTPS validation; review preload readiness separately. |
| `LOG_LEVEL`                                    | `INFO`, `WARNING`, or `ERROR`          | Deployment owner | Avoid debug logging in production.                                         |

### Secret-backed services

The following names identify required inputs, not values. Their values must be injected by the secret custodian and never committed.

| Variable group                                                                                     | Safe format                                                                            |
| -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `SECRET_KEY`                                                                                       | `<secret-manager-reference>`                                                           |
| `DATABASE_URL`                                                                                     | `postgresql://<db-user>:<secret-manager-reference>@<db-host>:5432/<db-name>`           |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`         | Approved SMTP host and account references; password uses `<secret-manager-reference>`. |
| `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `CLOUDINARY_UPLOAD_PRESET` | Approved storage identifiers; credential fields use `<secret-manager-reference>`.      |

### Brevo transactional-email contract

Brevo is the planned production SMTP provider; this is an environment contract,
not authorization to provision or contact the service. Do not create a Brevo
account, API key, SMTP key, sender identity, or DNS record from this repository.
The deployment owner must approve the provider account and sending domain, the
domain owner must publish Brevo's then-current SPF/DKIM records and review DMARC,
and the secret custodian must inject credentials through the approved secret
manager only after the sender domain is verified.

| Variable | Required production value |
| --- | --- |
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | `smtp-relay.brevo.com` |
| `EMAIL_PORT` | `587` |
| `EMAIL_USE_TLS` | `True` |
| `EMAIL_HOST_USER` | Brevo SMTP login supplied through the secret manager |
| `EMAIL_HOST_PASSWORD` | Brevo SMTP key supplied through the secret manager |
| `DEFAULT_FROM_EMAIL` | Approved sender address on the verified domain, optionally with a display name |

The application uses SMTP and does not need a Brevo HTTP API key. Never expose
any Brevo credential in frontend variables, repository files, command history,
logs, tickets, or retained validation output. Before release, prove with a
controlled non-customer recipient that Brevo accepts the verified sender and
that SPF/DKIM authentication passes; retain only redacted evidence. A failed or
unverified sender-domain check blocks production email rollout.

### Frontend public configuration

VITE_ variables are public build-time configuration. They are embedded in the browser bundle, so they must contain only public values and never secrets, tokens, passwords, private keys, or service credentials.

| Variable              | Safe format                       | Validation                                                                |
| --------------------- | --------------------------------- | ------------------------------------------------------------------------- |
| `VITE_API_URL`        | `https://<assigned-api-hostname>` | Required and HTTPS-only in production; embedded credentials are rejected. |
| `VITE_API_TIMEOUT_MS` | positive integer such as `10000`  | Invalid, zero, negative, and non-integer values are rejected.             |
| `VITE_SUPPORT_PHONE`  | Public support number             | Must remain public contact information.                                   |

Development and test retain the `http://localhost:8000` API fallback when `VITE_API_URL` is omitted. Production has no API URL fallback.

## Validation evidence

Run checks with deployment-injected values. Do not paste secrets into shell history, tickets, CI logs, or this document.

```bash
cd frontend
pnpm exec vitest run src/lib/env.test.ts
VITE_API_URL=https://api.example.test VITE_API_TIMEOUT_MS=10000 pnpm run build
```

`api.example.test` is a sanitized build fixture, not an assigned production hostname. For backend deployment validation, run the deployed configuration through `pipenv run python manage.py check --deploy`. When validating a manually supplied sanitized tuple, set `PIPENV_DONT_LOAD_ENV=1` so a local backend `.env` cannot replace it.

Retain successful backend security and cookie-flow tests, the deployment check, the frontend environment test, and the frontend production build as release evidence. Existing deployment-check warnings must be reviewed and dispositioned; they do not authorize rollout by themselves.

## Rollout gate

Do not release until all items are complete:

- [ ] The API hostname remains unassigned until the deployment owner approves it, along with the controlled shared-parent domain and exact frontend origin.
- [ ] The deployment owner records the cookie decision and proxy/TLS topology, including the network control that rejects spoofed forwarded-protocol headers.
- [ ] A real HTTPS browser journey on the assigned domains proves CSRF seed readability, login, a protected mutation, refresh/logout, and guest-order retrieval without browser token storage.
- [ ] An external probe proves unauthorized access to schema, Swagger, and Redoc is denied by hosting-platform or network controls. Django routing is not the control.
- [ ] The backend tests, deployment check, frontend environment test, and frontend production build have current successful evidence.

If the deployment cannot provide a controlled shared parent, stop rollout. A different cross-site CSRF architecture requires a separate specification and implementation change.

## Managed PostgreSQL release contract

This provider-neutral contract proves a supplied PostgreSQL target before starting application replicas. It does not select a database provider, deployment topology, or CI workflow.

### Prerequisites

- The secret custodian injects `DATABASE_URL` outside source control; operators must not print or paste it into command history or evidence.
- Validation uses a separate, empty, disposable PostgreSQL database and requires the explicit `--ack-disposable` flag.
- Release and startup use the approved target, a safe release ID, and writable owner-only paths for JSON result files.

### Required execution order

Run `validate → release-migrate → startup-check → server start`. The same release ID and migration-result file must flow from migration into startup approval:

```bash
cd backend
python -m core.managed_postgresql_runtime validate --ack-disposable --result /secure-path/validation.json
python -m core.managed_postgresql_runtime release-migrate --release-id <release-id> --result /secure-path/migration.json
python -m core.managed_postgresql_runtime startup-check --release-id <release-id> --migration-result /secure-path/migration.json --result /secure-path/startup.json
```

Start the server only when `startup-check` exits `0`. It validates canonical successful migration evidence for the same release ID, target reference, and migration graph, then confirms no migration is pending and runs Django's deployment check under the release lock.

### Failure and evidence handling

Any nonzero command result, missing or malformed evidence, stale graph, target mismatch, lock timeout, pending migration, or deployment-check error blocks the release: replicas **must not start**. Keep the bounded JSON files with release evidence under access controls; they contain credential-redacted target references and stage outcomes, never a database URL or password. Do not attempt to repair evidence, bypass a failed check, or substitute a local/shared target—correct the target or release state, then rerun the failed command.

## Rollback

Roll back code and the validated environment snapshot together while preserving HTTPS. Do not weaken cookie, origin, proxy, or documentation-boundary controls to make a release proceed; correct the supplied topology or evidence first.
