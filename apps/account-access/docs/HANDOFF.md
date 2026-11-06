# Account access

## Project structure

| File | Responsibility |
| --- | --- |
| `src/App.tsx` | Standalone application entry; mounts the account module |
| `src/auth/AccountFlow.tsx` | Welcome/signup/login views and account-session state |
| `src/auth/styles.css` | Account screen styles |
| `src/main.tsx` | React startup and stylesheet import |
| `server/auth.py` | Local account and session API; SQLite persistence |
| `server/test_auth.py` | Authentication integration tests using a temporary database |
| `scripts/dev.mjs` | Runs frontend and local auth service together |
| `docs/GITHUB.md` | Instructions for contributing this module to the team repo |

Package files, TypeScript/Vite configuration, index.html, and .gitignore are required project support files. VS Code hides generated dependencies, builds, caches, and account data; it does not delete them.

## Integration points

1. `AccountFlow` restores the account through `GET /api/session` on mount.
2. `submit` calls `/api/signup` or `/api/login` and sets `user` only after success. This is the explicit handoff point for the host app's router or shared auth provider.
3. The current `user` branch renders the confirmation. The onboarding developer can replace that branch with the host app's transition, without placing onboarding forms inside this module.
4. Restored sessions must follow the same routing decision as fresh logins. The host app must decide whether a returning user resumes onboarding or opens its dashboard; this module has no onboarding-completion flag.
5. `POST /api/logout` revokes the session. `POST /api/analyze` is proxied to the Flask API and verifies the same server-side session before processing. The browser's `user` object is display state, not authorization.

The stylesheet currently includes global element selectors, appropriate for this standalone preview. Scope those selectors or adopt the host app's design system when merging into a larger frontend to avoid changing teammates' screens.

## Local API contract

Requests are same-origin. Auth POST bodies use `Content-Type: application/json`. Analysis uses `multipart/form-data`; the browser attaches the HttpOnly session cookie automatically. Do not pass passwords or session tokens to later workflow components.

| Endpoint | Request | Success |
| --- | --- | --- |
| `POST /api/signup` | `{name, email, password}` | `{user: {name, email}}` and session cookie |
| `POST /api/login` | `{email, password}` | `{user: {name, email}}` and session cookie |
| `GET /api/session` | No body | `{user: {name, email}}` or `{user: null}` |
| `POST /api/logout` | `{}` | `{}` and cleared cookie |
| `POST /api/analyze` | Multipart form with `major` and optional `interests`, `goals`, `skills`, `certifications`, `volunteer_experience`, `transcript`, and `resume` | Validated pathway-analysis JSON; requires an active session |

Errors return `{error: string}` JSON with non-2xx status codes. No password/hash/token is returned in the JSON. SQLite user IDs are internal; a production integration should define a stable public user identifier before storing onboarding records, rather than using an email as a permanent database key.

## Running and checks

From this module's folder: install the root Python dependencies with `python -m pip install -r ../../requirements.txt`, then run `npm install` and `npm run dev`. The dev command starts the Vite frontend, auth service, and Flask analysis API. Open http://localhost:5173. Python 3.12+ and Node 20.19+ are required. Set `GROQ_API_KEY` in the repository-root `.env` to enable analysis. `npm test` runs the account tests. `npm run build` checks TypeScript and creates the frontend build. After building, `npm start` serves the local app and both APIs together.

## Deployment work remaining

This is a loopback-only local implementation. The team must arrange production hosting, HTTPS and secure production cookies, email verification, password recovery, production abuse protections, and integration with its actual backend/auth architecture before public use. The school-email field accepts valid email syntax and does not establish school enrollment or mailbox ownership. Local accounts live only on this computer; they are not a shared team database.

Do not commit or share `server/data/`, `.env` files, node_modules, or dist. The contribution is isolated on `feature/email-password-auth`; main and Design are unchanged.
