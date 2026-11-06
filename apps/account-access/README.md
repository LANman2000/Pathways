# Pathways email and password login

Local implementation following the updated Pathways Figma welcome and account-creation frames. Microsoft login has been removed. This module is maintained on `feature/email-password-auth`.

## Team handoff

**Your contribution ends at account creation/sign-in and the authenticated confirmation.** Teammates take over major selection, profile setup, interests, uploads, analysis, recommendations, and later workflow.

- [Scope, integration points, and API contract](docs/HANDOFF.md)
- [How to commit to the team repository later](docs/GITHUB.md)

## Run

Requires Node 20.19+ and Python 3.12+ with SQLite and OpenSSL support.

```sh
npm install
npm run dev
```

Open http://localhost:5173. The command starts the React app, the loopback-only authentication service, and the Flask analysis API. From the welcome screen choose **Open the interactive career demo**, or after sign-up choose **Start your career profile**. The demo screens are served from `HTML/`; sign-up/sign-in, questionnaire answers, PDF uploads, analysis, recommendation selection, and saving a pathway are connected. Analysis and saved pathways require the signed-in session. No external registration or database installation is required.

```sh
npm test
npm run build
npm start
```

Install the root Python dependencies with `python -m pip install -r ../../requirements.txt`. To use pathway analysis, set `GROQ_API_KEY` in the
repository-root `.env` file. The account screens and session APIs work without
calling Groq.

## Scope and storage

The React account screen provides sign-up, sign-in, session restoration, inline errors, and sign-out. The linked interactive HTML demo contains the profile questions, PDF uploads, recommendations, and dashboard. Interim answers and selected files remain in this browser session until analysis is submitted; accounts and saved pathways persist in SQLite.

Accounts persist in `server/data/accounts.sqlite`, excluded from source archives and Git. Passwords are salted and hashed using scrypt (N=131072, r=8, p=1). Session tokens are random, stored hashed, expire after eight hours, and are delivered through an HttpOnly, SameSite=Strict cookie. Logout revokes the server-side session. Login and signup requests have validation, a local IP attempt limit, and an exact-origin check. Nothing is stored in browser localStorage.

This is a local development implementation, not a public authentication deployment. The school-email label does not verify enrollment or mailbox ownership; valid email addresses are accepted. Email verification, password recovery, production hosting/HTTPS, secure production cookies, and production abuse protections remain future deployment work. Do not expose Python's development HTTP servers to the internet. `npm start` serves the completed build, authentication, and analysis API together on port 5173. `npm run preview` previews static UI only and cannot serve API requests.

## Files

- `src/App.tsx`: small app entry that loads the account module.
- `src/auth/AccountFlow.tsx`: welcome, signup, login, and session state.
- `src/auth/styles.css`: Figma-based navy layout, pale blue form, and responsive styles.
- `server/auth.py`: local SQLite accounts and cookie sessions.
- `server/test_auth.py`: integration tests using a temporary database.
- `scripts/dev.mjs`: starts and stops the frontend, auth service, and analysis API.
- `../../HTML/`: demo screens; `demo.js` connects their forms and actions to the APIs.

Figma: https://www.figma.com/design/2d11dRtrHXkw8FQ10YpKx9/Pathways

Implementation references: [Python scrypt](https://docs.python.org/3.12/library/hashlib.html#hashlib.scrypt), [SQLite](https://docs.python.org/3.12/library/sqlite3.html).

Generated build files, installed dependencies, local account data, and caches are hidden from VS Code Explorer using `.vscode/settings.json`. They remain on disk because the app needs them; they are excluded from Git. The remaining files support this module.
