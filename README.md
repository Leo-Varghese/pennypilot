# PennyPilot

> A modern, AI-assisted personal finance tracker built as my first full-stack software project.

PennyPilot helps users record income and expenses, understand spending patterns, manage budgets, monitor savings goals, track recurring payments, and review financial insights from one responsive dashboard.

The application combines a Next.js frontend, a FastAPI backend, a persistent PostgreSQL database hosted on Neon, and a read-only AI financial explanation assistant powered through GroqCloud.

## Project Author

**Name:** Leo Varghese  
**Registration Number:** 2602050956  
**Programme:** B.Tech in Computer Science and Engineering  
**Institution:** Manipal University Jaipur  
**Project milestone:** My first complete full-stack project

PennyPilot represents my first attempt at designing, building, securing, testing, and deploying a complete web application across the frontend, backend, database, analytics, and cloud deployment layers.

## Live Architecture

```text
User Browser
    |
    v
Next.js Frontend on Vercel
    |
    | HTTPS REST API
    v
FastAPI Backend on Render
    |                 |
    |                 | Aggregated, read-only financial summary
    v                 v
Neon PostgreSQL     GroqCloud AI
```

- **Frontend:** Next.js App Router, React, TypeScript, Tailwind CSS, Recharts, Lucide icons, React Hook Form, and Zod
- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic, and Pytest
- **Database:** Persistent PostgreSQL hosted on Neon
- **AI assistant:** GroqCloud through a protected FastAPI route
- **Frontend deployment:** Vercel
- **Backend deployment:** Render
- **Source control:** GitHub monorepo

## Core Features

### Financial dashboard

- Total income and net expenses
- Actual savings and net cash flow
- Savings rate
- Current account balances
- Budget remaining
- Savings-goal progress
- Upcoming recurring payments
- Assets, liabilities, and net worth
- Comparison with the preceding equivalent period
- Daily, weekly, monthly, quarterly, yearly, and custom date ranges

### Transactions

- Income, expenses, transfers, refunds, and balance adjustments
- INR as the default currency
- UPI, cash, debit card, credit card, wallet, bank transfer, and other payment methods
- Categories, subcategories, merchants, purposes, locations, notes, and tags
- Add, edit, delete, duplicate, search, filter, sort, and paginate records
- Bulk categorisation
- CSV import and Excel-compatible CSV export
- Private PNG and JPEG receipt attachments

### Accounts

- Cash, savings, current, credit-card, wallet, investment, and custom accounts
- Opening balance and current balance tracking
- Account-level transaction history
- Transfers excluded from income and spending totals
- Credit-card purchases recorded once as expenses
- Credit-card bill payments treated as transfers rather than duplicate expenses

### Budgeting and goals

- Monthly and custom-period budgets
- Category allocations and planned-versus-actual spending
- Signed budget rollover
- Budget alerts and retained budget history
- Optional zero-based income-allocation guide
- Savings goals with target values, target dates, priorities, contribution history, progress, and estimated monthly contribution
- Goal contributions treated as allocations rather than duplicate expenses

### Recurring payments

- Recurring income, bills, subscriptions, and expected expenses
- Projected future cash flow
- Explicit separation between scheduled and paid transactions
- Idempotent paid-record creation to reduce duplicate transactions

### Analytics and reports

- Income versus expenses
- Spending by category, subcategory, and merchant
- Savings and savings-rate trends
- Budgeted versus recorded spending
- Income sources and weekday spending patterns
- Current net worth and explicit historical snapshots
- Interactive chart drill-down into matching transactions
- Browser print or Save as PDF
- Filtered CSV reports and complete JSON data export

## PennyPilot AI Coach

PennyPilot includes a fast, read-only AI financial explanation assistant.

The AI Coach can:

- Summarise the financial period currently visible on the dashboard
- Explain changes between the selected and comparison periods
- Identify categories and budgets that may need attention
- Provide practical, non-investment savings suggestions based on recorded aggregates
- Explain when the available data is insufficient to establish a reason

### AI privacy and safety design

- The browser sends the question to PennyPilot's authenticated FastAPI endpoint.
- FastAPI sends only a limited aggregated dashboard summary to GroqCloud.
- Passwords, session tokens, receipts, notes, locations, database credentials, and raw transaction rows are excluded.
- The Groq API key is stored only in the Render environment configuration.
- No `NEXT_PUBLIC_GROQ_API_KEY` is used.
- The assistant is read-only and cannot add, edit, or delete financial records.
- Output is limited, timed out, and rate-limited on a best-effort per-user basis.
- The application has no automatic paid AI fallback.

The AI feature is free only while the project remains within GroqCloud's free-plan quotas. If the shared quota is exhausted, the finance tracker continues to work and only the AI Coach becomes temporarily unavailable.

## Free-Tier Startup Notice

PennyPilot currently uses free cloud service tiers. After a period of inactivity, the backend or database may need time to wake up.

When signing in:

1. Submit valid credentials once.
2. Allow up to approximately 60 seconds for the services to wake.
3. If the connection does not complete, wait a few seconds and retry once.
4. Avoid making more than two immediate attempts.

This delay is a free-tier cold start, not an indication that the account or financial records have been lost.

## Financial Calculation Rules

PennyPilot uses PostgreSQL `NUMERIC(20,2)` values and Python `Decimal` arithmetic for authoritative money calculations.

```text
Net expenses = recorded expenses - recorded refunds
Actual savings = recorded income - net expenses
Savings rate = actual savings / recorded income x 100
```

The savings rate is unavailable when recorded income is zero.

Transfers, balance adjustments, savings-goal allocations, and projected recurring items are excluded from income and expense totals. Current balances and current net worth are distinct from filtered-period cash-flow calculations.

Currencies are never combined unless a valid conversion system is available. PennyPilot currently rejects unsupported cross-currency transfers rather than inventing exchange rates.

## Security Highlights

- Argon2 password hashing
- Expiring and revocable opaque bearer sessions
- Server-side ownership checks on financial records
- Exact-origin CORS configuration
- Parameterised SQLAlchemy queries
- Pydantic request validation
- Authentication rate limiting
- Private receipt access
- CSV size and row limits
- Spreadsheet-formula neutralisation during CSV export
- Security headers and no-store responses
- Password-confirmed account deletion
- No secrets committed to the repository

PennyPilot is an educational portfolio project and has not undergone an independent security audit. Do not treat the application as a bank, investment adviser, tax adviser, or regulated financial institution.

## Repository Structure

```text
pennypilot/
├── frontend/                 # Next.js website deployed on Vercel
├── backend/                  # FastAPI service deployed on Render
│   ├── app/
│   ├── migrations/
│   ├── scripts/
│   └── tests/
├── .github/workflows/        # Automated verification
├── docs/                     # Architecture, calculations, security, and deployment guides
├── render.yaml               # Render service configuration
├── compose.yaml              # Optional local PostgreSQL setup
├── .gitignore
└── README.md
```

## Local Development

### Requirements

- Python 3.12
- Node.js 22 LTS
- npm
- Git
- PostgreSQL 16, or Docker for an optional local database

### 1. Clone the repository

```powershell
git clone YOUR_GITHUB_REPOSITORY_URL
cd pennypilot
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with the actual repository URL shown on GitHub.

### 2. Start the backend

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Configure `backend/.env` locally:

```env
DATABASE_URL=postgresql+psycopg://YOUR_LOCAL_USER:YOUR_LOCAL_PASSWORD@localhost:5432/pennypilot
APP_ENV=development
SESSION_SECRET=replace-with-a-random-secret-at-least-32-characters
SESSION_HOURS=12
FRONTEND_ORIGINS=http://localhost:3000
GROQ_API_KEY=your-local-development-key
GROQ_MODEL=openai/gpt-oss-20b
```

Generate a local session secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Apply migrations and start FastAPI:

```powershell
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

Useful local endpoints:

- API documentation: `http://localhost:8000/docs`
- Liveness: `http://localhost:8000/health`
- Readiness: `http://localhost:8000/ready`

### 3. Start the frontend

Open a second PowerShell terminal:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

Open `http://localhost:3000`.

The frontend environment file should contain:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Never place the Groq API key in the frontend environment file.

## Verification

### Backend

Run from `backend` using a disposable test database only:

```powershell
python -m pytest -q
python -m alembic check
```

The test suite covers authentication, ownership isolation, transaction calculations, transfers, refunds, credit-card handling, budgets, savings goals, time zones, CSV operations, CORS, private receipts, exports, and account deletion.

### Frontend

Run from `frontend`:

```powershell
npm run typecheck
npm run build
```

Do not deploy a frontend commit if either command fails.

## Deployment

### Frontend on Vercel

- Import this GitHub repository into Vercel.
- Set the Root Directory to `frontend`.
- Set `NEXT_PUBLIC_API_BASE_URL` to the actual Render backend origin.
- Do not append `/api/v1` because the frontend client adds it.
- Do not add the Groq API key to Vercel.
- Enable automatic production deployments from `main`.

### Backend on Render

- Connect the same GitHub repository.
- Set the Root Directory to `backend`.
- Build command:

  ```text
  pip install -r requirements.txt
  ```

- Pre-deploy command:

  ```text
  alembic upgrade head
  ```

- Start command:

  ```text
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```

- Health-check path:

  ```text
  /ready
  ```

Required Render environment variables:

```text
DATABASE_URL             Neon PostgreSQL connection string, secret
SESSION_SECRET           Random secret, secret
SESSION_HOURS            Session lifetime, default 12
FRONTEND_ORIGINS         Exact Vercel production origin
APP_ENV                  production
GROQ_API_KEY             GroqCloud API key, secret
GROQ_MODEL               openai/gpt-oss-20b
```

Use Neon's pooled connection string if recommended for the deployed FastAPI workload. Keep all credentials exclusively in platform environment settings.

## Updating the Application

```powershell
git add .
git commit -m "Describe the update"
git push origin main
```

GitHub pushes to `main` trigger the configured Vercel and Render deployments. PostgreSQL records remain in Neon and are not rebuilt during normal code deployments.

## Current Limitations

- AI availability depends on shared GroqCloud free-plan quotas.
- Render and Neon free-tier cold starts can delay the first request.
- AI rate limiting is best-effort and resets when the single backend process restarts.
- No bank synchronization or automatic transaction import.
- No foreign-exchange conversion engine.
- No split transactions.
- No email verification, password recovery, or multi-factor authentication.
- Receipt support is limited to authenticated PNG and JPEG files.
- Reports use CSV and browser print or Save as PDF, not native XLSX or server-generated PDF files.
- PennyPilot is a student portfolio application, not independently audited financial software.

## Project Journey

PennyPilot began as my first full-stack project and became an opportunity to learn how a real application is structured beyond a visual prototype. The work involved:

- Designing a normalized financial database
- Implementing secure authentication and user-specific data isolation
- Handling money with decimal-safe arithmetic
- Building responsive dashboards and interactive charts
- Connecting a Next.js frontend to a versioned FastAPI API
- Managing PostgreSQL migrations
- Testing financial edge cases
- Deploying a monorepo across Vercel, Render, and Neon
- Adding a privacy-conscious, read-only AI explanation assistant
- Debugging real deployment, cold-start, CORS, dependency, and model-response issues

This project is an important starting point in my software-development journey and will continue to improve as I learn more about cloud engineering, AI integration, security, analytics, and scalable application design.

## Author

**Leo Varghese**  
**Registration Number:** 2602050956  
**B.Tech Computer Science and Engineering**  
**Manipal University Jaipur**

Built as my first full-stack project and portfolio milestone.

## Acknowledgement

PennyPilot was developed as a learning and portfolio project using modern open-source technologies and free cloud-service tiers. AI-assisted development tools were used during planning, implementation, debugging, documentation, and refinement, while the project architecture, deployment, testing, and iterative decisions were carried out as part of the learning process.

## License

This repository currently has no explicit open-source licence. Unless a licence is added, all rights are reserved by the project author. Third-party libraries remain subject to their respective licences.
