# PennyPilot

Personal finance monorepo: **Next.js on Vercel → HTTP API → FastAPI on Render → persistent Render PostgreSQL**.

## Delivery status

Actual source files, normalized SQLAlchemy models, an explicit Alembic migration, automated tests, responsive frontend, deployment configuration and guides are included. No GitHub repository or cloud service was created by this delivery. **Read [verification](docs/VERIFICATION.md) and [limitations](docs/LIMITATIONS.md) before storing real financial information.** A successful production frontend build and live deployment must not be assumed from source delivery.

## Included

- Registration, Argon2 passwords, expiring/revocable opaque bearer sessions, server-side ownership checks, exact-origin CORS.
- Accounts, income, expenses, refunds, adjustments and atomic single-record transfers. Card payments are transfers, not new expenses.
- Transaction edit/delete/duplicate, tags, purpose, notes, UPI and other payment methods, search, filters, sorting, pagination, bulk categorization.
- Validated atomic CSV imports with exact-file duplicate protection; Excel-compatible UTF-8 CSV export; full JSON data/receipt export.
- Private PNG/JPEG receipts stored in PostgreSQL, never an ephemeral disk.
- Category/subcategory budgets, custom/monthly periods, signed rollover, alerts and history; optional zero-based income-allocation guide.
- Savings goals and contribution history, recurring schedules and explicit idempotent paid recording, projected cash flow.
- Database-derived dashboard, comparison period, category/merchant/income/weekday charts, savings and cash-flow trends, current assets/liabilities/net worth, explicit net-worth snapshots.
- INR defaults, Indian number display, DD MMM YYYY, configurable timezone/currency. No mixed-currency totals or unsupported FX conversion.

## Repository

```text
frontend/                 Next.js App Router, TypeScript, Tailwind, Radix, Recharts
backend/app/              FastAPI routers, models, validation, security, services
backend/migrations/       Alembic revision history
backend/tests/            Pytest financial and security integration tests
backend/scripts/          Explicit synthetic development seed
.github/workflows/ci.yml  PostgreSQL tests and frontend build checks
render.yaml               Render API + PostgreSQL Blueprint
compose.yaml              Optional local PostgreSQL
 docs/                    Deployment, security, calculations, CSV, verification
```

## Requirements

Python 3.12, Node.js 22 LTS, npm, Git and PostgreSQL 16. Docker is optional. Never point tests at a production database: test fixtures intentionally destroy the test schema.

## Local setup: Windows PowerShell

Extract the ZIP, then open a terminal in the `pennypilot` folder.

### 1. PostgreSQL

**Option A, Docker:** choose a local password in your terminal, not in chat:

```powershell
$env:POSTGRES_PASSWORD = Read-Host "Local PostgreSQL password"
docker compose up -d db
```

**Option B, native PostgreSQL:** install PostgreSQL, open SQL Shell or pgAdmin as the database administrator, then run:

```sql
CREATE USER pennypilot WITH PASSWORD 'YOUR_LOCAL_PASSWORD';
CREATE DATABASE pennypilot OWNER pennypilot;
```

Replace the placeholder locally. If the password contains reserved URL characters, URL-encode it when setting DATABASE_URL. Use a separate database for tests.

### 2. Backend

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env`: set DATABASE_URL to your local PostgreSQL database and SESSION_SECRET to a random value. Generate a secret locally:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

If activation is blocked, run `.\.venv\Scripts\python.exe` directly instead of changing machine-wide execution policy.

API documentation is at [local API docs](http://localhost:8000/docs), liveness at [health](http://localhost:8000/health), database/schema readiness at [ready](http://localhost:8000/ready).

### 3. Frontend, second terminal

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

Open [local PennyPilot](http://localhost:3000). Register, create an account with its opening date/balance, then add transactions. Empty accounts have no fake history.

On macOS/Linux use `python3 -m venv .venv`, `source .venv/bin/activate`, and `cp` instead of `Copy-Item`.

### 4. Verification

```powershell
# Backend directory, disposable SQLite test database by default:
python -m pytest -q
# PostgreSQL test database, never your real database:
$env:DATABASE_URL = "postgresql+psycopg://TEST_USER:TEST_PASSWORD@localhost:5432/pennypilot_test"
$env:APP_ENV = "test"
python -m alembic upgrade head
python -m alembic check
python -m pytest -q
# Remove the shell override before restarting your normal backend:
Remove-Item Env:DATABASE_URL
Remove-Item Env:APP_ENV
# Frontend directory:
npm run typecheck
npm run build
```

### Optional synthetic demo

Use a separate development database, migrate it, then from `backend` run `python -m scripts.seed --confirm-synthetic`. It prompts locally for a password, labels records SYNTHETIC DEMO, refuses non-development environments and never runs on deploy.

## Deploy

Follow [GitHub, Render and Vercel deployment](docs/DEPLOYMENT.md). Root directories are **backend** on Render and **frontend** on Vercel. The frontend API origin is configured in the Vercel dashboard, not hardcoded in source. Financial data persists in PostgreSQL across code deployments.

## First-use workflow

1. Register and add each account. For a credit card, opening debt is negative.
2. Record purchases on the account actually charged. Record card bill payments as bank-to-card transfers.
3. Create categories/subcategories and period budgets. Avoid overlapping budgets.
4. Add goals; contributions earmark money, they do not move cash.
5. Add recurring schedules. Select Record paid only when actually paid; repeated requests for the same due date return the original payment.
6. Use date presets/custom ranges, chart drilldowns and filtered exports. Save net-worth snapshots on different dates to build genuine history.

## Troubleshooting

- **API unreachable / CORS:** verify Render `/ready`, Vercel API variable, and exact Vercel origin in FRONTEND_ORIGINS. No paths/trailing slash in origins. Redeploy frontend after changing public variables.
- **Relation does not exist:** run Alembic against the correct database. Never use drop/create in production.
- **Database login fails:** verify user/password/database and URL encoding. Render internal URLs are for services on Render's private network, not your laptop.
- **401:** sign in again. Tokens are memory-only and expire; a page reload deliberately clears the browser session.
- **409:** a duplicate, protected historical record or referenced account/category cannot be changed/deleted. Keep historical records; use an adjustment/refund when appropriate.
- **422:** read the field validation message. Amounts have at most two decimal places, timestamps require an offset, account currency must match, transfers need a different destination.
- **CSV fails:** use the documented headers and your own account/category IDs. Entire invalid imports roll back.
- **Port already in use:** change the local port and matching frontend/CORS configuration.
- **npm registry failure:** retry from your normal network, use Node 22, and run `npm install` before build. Do not commit node_modules.

See [calculations](docs/CALCULATIONS.md), [security](docs/SECURITY.md), [CSV format](docs/CSV.md), [API](docs/API.md), and [product research](docs/PRODUCT_RESEARCH.md).
