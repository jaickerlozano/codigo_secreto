# Production security configuration

Production deployment remains blocked until the deployment owner supplies the approved topology and the release owner records the required evidence. This runbook documents formats and responsibilities only; it contains no secrets and API hostname remains unassigned.

## Quick path

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

## Rollback

Roll back code and the validated environment snapshot together while preserving HTTPS. Do not weaken cookie, origin, proxy, or documentation-boundary controls to make a release proceed; correct the supplied topology or evidence first.
