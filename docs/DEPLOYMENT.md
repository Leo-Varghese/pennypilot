# GitHub → Render + Vercel

No cloud account was connected or deployment created during source generation. These steps are the handoff. Do not use real financial data until the CI checks and your deployed smoke test pass. Review current plan charges before creating services. The Blueprint deliberately selects paid persistent services; it is not a promise of free hosting.

## 1. GitHub

Extract the ZIP. Open PowerShell inside `pennypilot`.

```powershell
git init -b main
git add .
git commit -m "Initial PennyPilot application"
```

If Git asks for your identity, configure your own name and email locally. Do not put tokens in remote URLs.

### Recommended: GitHub CLI, authorized browser sign-in

Install GitHub CLI, then:

```powershell
gh auth login
gh repo create pennypilot --private --source=. --remote=origin --push
```

Choose GitHub.com, HTTPS and browser authentication. The command prints your real repository link after success. This delivery does not invent one.

### Alternative: GitHub website

1. Sign in, choose New repository, name `pennypilot`, select Private.
2. Do not initialize a README, license or gitignore because this project already contains its files.
3. Copy the exact repository HTTPS clone URL from the page.
4. Replace YOUR_REPOSITORY_URL below locally:

```powershell
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

Use Git Credential Manager's browser authentication if prompted. Never share credentials in chat. Confirm `frontend`, `backend`, `render.yaml` and `.github/workflows/ci.yml` appear on GitHub. Review Actions results. The workflow runs real PostgreSQL tests and frontend checks; its existence does not mean it has already passed.

## 2. Render Blueprint (recommended)

1. Sign in to Render. Choose New → Blueprint. Connect GitHub through Render's authorization flow and grant access only to `pennypilot` if possible.
2. Select the repository and branch `main`; Blueprint path is root `render.yaml`.
3. Review the API and PostgreSQL plans/charges. Both use Singapore. The API's Root Directory is `backend`.
4. Supply FRONTEND_ORIGINS with an exact HTTPS origin you control. If Vercel is not created yet, use an owned origin temporarily and replace it with the actual Vercel production origin before using the app. No wildcard and no path.
5. Apply the Blueprint. Render generates SESSION_SECRET and connects DATABASE_URL using the database's connectionString. Keep both secret.
6. The build installs `requirements.txt`. The pre-deploy command runs `alembic upgrade head`. The start command runs the actual module `app.main:app` on `$PORT`.
7. Inspect build, migration and runtime logs. Do not run seed in production.
8. Open the actual service origin with `/health` and `/ready` appended. Both should return 200. Open `/docs` to verify the versioned API.
9. Copy the exact Render service origin from its dashboard for Vercel. Do not append `/api/v1`; the frontend client adds that path.

Blueprint database `ipAllowList: []` disables public database access; the API uses the internal network. If you need a temporary administrative external connection, explicitly allow only your IP and remove the rule afterward.

### Manual Render setup: New Web Service / Connect Repository

1. Create Render PostgreSQL first: name `pennypilot-db`, database/user `pennypilot`, Singapore region, persistent plan appropriate for your needs. Save its internal database URL in Render settings, never source code.
2. Choose New → Web Service → Connect Repository. Authorize the same GitHub repository.
3. Set Name `pennypilot-api`, branch `main`, Runtime Python 3, Region Singapore, **Root Directory `backend`**.
4. Build Command: `pip install -r requirements.txt`.
5. Pre-Deploy Command: `alembic upgrade head` on a plan supporting pre-deploy commands.
6. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
7. Health Check Path: `/ready`.
8. Set environment variables from the table below. DATABASE_URL is the internal URL of the attached PostgreSQL database. `postgres://` and `postgresql://` are normalized to the psycopg driver by the app.
9. Enable automatic deploys for `main`. Create service, inspect logs and verify `/health`, `/ready`, `/docs`.

If your plan does not support pre-deploy commands, run `alembic upgrade head` once in a controlled Render shell/job before starting the new release. For a single-instance initial deployment only, an alternative Start Command is `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Do not run concurrent migration processes. Prefer the dedicated pre-deploy command for ongoing use.

## 3. Vercel

1. Sign in to Vercel and choose Add New → Project.
2. Connect GitHub and import the **same** private `pennypilot` repository.
3. Set Framework Preset **Next.js** and **Root Directory `frontend`**.
4. Node.js: 22 LTS. Install Command: `npm install` (or `npm ci` after generating and committing a verified lockfile). Build Command: `npm run build`. Keep Next.js's default output directory.
5. Add `NEXT_PUBLIC_API_BASE_URL` in Vercel environment settings. Its value must be the **actual Render API origin** copied above, HTTPS, no `/api/v1` suffix. Apply it to Production; add it separately to Preview if previews should use an API.
6. Deploy. A public Next.js variable is embedded at build time, so redeploy after changing it.
7. Copy the actual Vercel production origin. In Render, set FRONTEND_ORIGINS to that exact origin. Redeploy the API after environment changes.
8. Open the frontend, register, create an account, record income/expense and a transfer. Verify totals and persistence after a redeploy. Use browser Network tools to confirm requests go to the real Render API, not localhost.
9. In Vercel Git settings, use `main` as the production branch. GitHub pushes then trigger deployments on both platforms according to their Git settings.

### Preview origins

Use a separate staging API/database for preview branches where practical. If allowing a preview on the production API, explicitly add that **exact** preview origin to FRONTEND_ORIGINS, comma-separated with the production origin. Never allow all `*.vercel.app` origins or a broad regex. Remove obsolete previews. Preview access to the API is not authorization to another user's records; bearer sessions and ownership still apply.

## Environment variables

| Name | Where | Secret? | Purpose |
|---|---|---|---|
| NEXT_PUBLIC_API_BASE_URL | Vercel / frontend .env.local | No | Actual API origin; never database credentials |
| DATABASE_URL | Render API / backend .env | **Yes** | PostgreSQL connection string; internal URL in production |
| SESSION_SECRET | Render API / backend .env | **Yes** | Random 32+ character HMAC key for opaque session token hashes; rotation revokes all sessions |
| SESSION_HOURS | Render API | No | Session lifetime, default 12 hours |
| FRONTEND_ORIGINS | Render API | No | Comma-separated exact permitted frontend origins |
| APP_ENV | Render API | No | `production` enables HTTPS-origin, secret and PostgreSQL validation |
| PYTHON_VERSION | Render runtime | No | Python runtime, configured in Blueprint |
| POSTGRES_PASSWORD | Local Docker shell | **Yes** | Optional local database password only |

`.env.example` files contain placeholders only. Dashboard values are not committed. Source code contains root-directory/build/migration settings; actual URLs, allowed origins and secrets belong in platform dashboards.

## Updates and migrations

```powershell
git add .
git commit -m "Describe your change"
git push origin main
```

Review CI and deployment logs. Never delete the database to update code. For a schema change, create and review a new migration locally: `alembic revision --autogenerate -m "describe change"`. Commit it with code. Back up before applying. Use additive, backward-compatible migrations when old/new application instances can overlap. The application never calls `create_all` or `drop_all` on production startup.

## Smoke-test checklist

- `/ready` returns 200 and no secrets.
- Registration/login/logout work; a logged-out request returns 401.
- A second account cannot see or mutate the first account's records.
- INR totals match your known test records; transfers do not increase spending.
- Credit-card purchase counted once; card payment is a transfer.
- CSV export and private receipt download require authentication.
- Browser console has no mixed-content/CORS errors.
- A code redeploy retains all PostgreSQL records.
- Configure database backups and verify a restore before relying on the service.

## Official deployment references

- [Render FastAPI guide](https://render.com/docs/deploy-fastapi)
- [Render Blueprint reference](https://render.com/docs/blueprint-spec)
- [Vercel monorepo root directories](https://vercel.com/docs/monorepos)
