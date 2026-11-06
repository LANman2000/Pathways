# Commit this work when the team is ready

This module is under `apps/account-access/` on the local `feature/email-password-auth` branch of the team repository. The original standalone preview is separate. No branch has been pushed yet. A commit records a local change; pushing uploads it; a pull request asks the team to review it.

## Use the existing team repository

1. Confirm the current team repository URL and the branch the team develops against.
2. In VS Code, run **Git: Clone** from the Command Palette, paste that URL, and open the cloned folder. If you already have the correct repository locally, open it instead and update the team's base branch before starting.
3. Create a feature branch, for example `feature/email-password-auth`, using the branch control at the lower left.
4. If the repo already has a working app, integrate `src/auth/` and the documented API contract into its existing structure. Do not replace its App.tsx, package.json, or configuration with this standalone project's versions. Add only the dependencies/configuration it needs, and agree with the backend teammate how authentication will be hosted.
5. If the team wants this as a standalone module in a mostly empty repo, copy the source under an agreed folder such as `apps/account-access/`. Include src, server source/tests, scripts, docs, .vscode/settings.json, .gitignore, index.html, package.json, package-lock.json, tsconfig.json, vite.config.ts, and README.md. Exclude node_modules, dist, server/data, caches, environment files, and ZIPs. Preserve the folder's .gitignore.
6. Run the module's tests and build from its folder.
7. Open VS Code **Source Control**, review the changed files, and stage only the intended module/integration changes. Check that no local accounts, secrets, or unrelated team changes are included.
8. Enter a commit message such as `Add email/password account access and team handoff`, then click **Commit**.
9. Click **Publish Branch** (or push the feature branch). This uploads the commit to the existing team's repository. Do not use **Publish to GitHub** to create a separate repository for this module.
10. Open a pull request against the team's agreed base branch. Describe the scope boundary and link the handoff. Let the team review it before merging.

## Suggested pull request description

Adds the updated Figma welcome, signup, and email/password sign-in screens, plus a local SQLite authentication service with hashed passwords and cookie sessions.

Scope ends at authenticated account confirmation. Onboarding and the remaining career workflow are owned by other contributors and are not implemented here. See docs/HANDOFF.md for integration points, the API contract, and production work still needed.

Validation: run the account integration tests and frontend build on the final integration branch; record those results in the pull request.

## Official guides

- [VS Code repositories and remotes](https://code.visualstudio.com/docs/sourcecontrol/repos-remotes)
- [GitHub pull request quickstart](https://docs.github.com/en/pull-requests/get-started/pull-request-quickstart)
