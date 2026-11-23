<div align="center">
  <img src="frontend/public/icons/pennypilot-192.png" alt="PennyPilot green wallet logo" width="96" />

# PennyPilot

### Personal finance clarity, powered by a cloud-native full-stack platform

[Live Website](https://pennypilot-swart.vercel.app/) · [Install App](https://pennypilot-swart.vercel.app/install) · [Solution Documentation](docs/SOLUTION-OVERVIEW.md) · [Report an Issue](https://github.com/Leo-Varghese/PennyPilot/issues)

</div>

## Overview

PennyPilot is a personal finance platform for recording transactions, managing accounts and budgets, building savings goals, planning future purchases, monitoring recurring commitments, importing bank statements, and understanding financial activity through analytics and a read-only AI Coach.

PennyPilot is my first complete full-stack project. It demonstrates frontend development, backend APIs, relational data modelling, authentication, cloud deployment, database migrations, automated tests, responsible AI integration, privacy-conscious administration, and technical documentation.

## Author

**Leo Varghese**  
**Registration Number:** 2602050956  
**Programme:** B.Tech Computer Science and Engineering  
**Institution:** Manipal University Jaipur  
**Class:** 2030

- [GitHub Profile](https://github.com/Leo-Varghese)
- [LinkedIn Profile](https://www.linkedin.com/in/leo-varghese-in/)

## Live Architecture

```text
User Browser or Installed PennyPilot App
                 |
                 v
Next.js Frontend on Vercel
                 |
                 | HTTPS REST API
                 v
FastAPI Backend on Render
        |                    |
        |                    | Limited aggregated financial context
        v                    v
Neon PostgreSQL          GroqCloud AI
        |
        v
Brevo Transactional Email
```

- **Frontend:** Next.js App Router, React, TypeScript, Tailwind CSS, Recharts, Lucide icons, React Hook Form, and Zod
- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic, and Pytest
- **Database:** Persistent PostgreSQL hosted on Neon
- **AI assistant:** GroqCloud through a protected FastAPI route
- **Transactional email:** Brevo for password-reset messages
- **Frontend deployment:** Vercel
- **Backend deployment:** Render
- **Source control:** GitHub monorepo
- **App delivery:** Installable Progressive Web App for mobile and desktop

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
- Opening balance and current-balance tracking
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
- Savings goals with target values, dates, priorities, contributions, progress, and estimated monthly contribution
- Goal contributions treated as allocations rather than duplicate expenses

### Recurring payments

- Recurring income, bills, subscriptions, and expected expenses
- Projected future cash flow
- Explicit separation between scheduled and paid transactions
- Idempotent paid-record creation to reduce duplicates

### Financial workspace

- Income, expenses, refunds, transfers, and balance adjustments
- Multiple financial accounts and current balances
- Budgets with category allocations and remaining amounts
- Savings goals, progress tracking, and contribution history
- Recurring income, bills, subscriptions, and projected commitments
- Net worth using accounts, assets, and liabilities
- Monthly, weekly, quarterly, yearly, and custom-date analysis

### Planned Purchases

Planned Purchases acts as a wishlist for purchases a user may make later.

- Item name, expected price, category, merchant, priority, target date, and notes
- Merchant and item suggestions based on the signed-in user’s history
- Planned items remain separate from actual expenses
- **Mark purchased** creates one real expense transaction
- **Undo purchase** removes the linked expense and returns the item to Planned
- Purchase and undo notifications explain that free cloud services may require 30–40 seconds to refresh connected views

### Smart transaction entry

- Suggestions based on previous merchant activity
- Case-insensitive merchant grouping
- Merchant normalisation for casing, spaces, underscores, and hyphens
- Categories, payment methods, purposes, tags, dates, and notes
- Search, filtering, pagination, editing, duplication, and deletion

### Bank-statement import

- CSV statement upload
- Universal column mapping
- Debit and credit recognition
- Preview before import
- Category and merchant review
- File-level and row-level duplicate protection
- Import batches and stored original narration
- No collection of internet-banking passwords, OTPs, CVVs, or UPI PINs

### Analytics and reports

- Income versus expenses
- Spending by category and merchant
- Savings and savings-rate trends
- Budgeted versus actual spending
- Income-source analysis
- Lifetime category and total spending
- Comparison with the preceding equivalent period
- CSV and JSON exports
- Browser Print or Save as PDF

## PennyPilot AI Coach

PennyPilot includes a read-only AI Coach through GroqCloud and the FastAPI backend.

The AI Coach can:

- Summarise the current financial period
- Answer lifetime questions such as “How much have I spent on Food & groceries till date?”
- Preserve short follow-up context such as “without refunds”
- Explain category and budget changes
- Produce Markdown tables
- Distinguish recorded facts from general suggestions

### AI safeguards

- The API key is stored only in the Render backend environment
- The browser never contacts GroqCloud directly
- Only limited aggregated financial context is sent
- Passwords, tokens, receipts, notes, and raw transaction rows are excluded
- The AI cannot create, edit, or delete financial records
- Usage is rate-limited and has no automatic paid fallback

## Authentication and Password Recovery

- Argon2 password hashing
- Revocable opaque sessions
- Show and Hide password controls
- Normal-user Forgot Password flow
- Brevo transactional reset emails
- Neutral reset response that does not reveal whether an email is registered
- 30-minute, single-use reset links
- Existing sessions revoked after a successful password reset

Brevo’s free plan currently provides 300 email sends per day. The allowance resets daily and unused sends do not roll over.

## Private Administrator Portal

The administrator console is separate from the normal user workspace:

```text
https://pennypilot-swart.vercel.app/admin
```

It uses a separate administrator username, Argon2 password hash, session-signing secret, and short-lived administrator session.

The private console provides:

- Aggregate user, account, and transaction counts
- Masked user directory
- Registration activity
- Private Site Doctor diagnostics

The administrator console does **not** expose users’ financial records, balances, receipts, notes, passwords, or API secrets.

## Private Site Doctor

Site Doctor is visible only after successful private administrator login.

It checks:

- Public website availability
- Response time and free-tier cold starts
- Database readiness
- Alembic migration-chain health
- Groq AI configuration
- Private administrator configuration

Site Doctor provides health statuses, caveats, and recommendations. It never changes production automatically or reads user financial data.

## Installable App

PennyPilot is an installable Progressive Web App for:

- iPhone and iPad
- Android
- Windows
- macOS

Visit the [PennyPilot installation page](https://pennypilot-swart.vercel.app/install) for platform-specific instructions.

The installed app uses the same PennyPilot account, Render backend, and Neon database as the website. Updates follow the existing workflow:

```text
VS Code
→ Git commit
→ GitHub main branch
→ Vercel deployment
→ Installed app refresh
```

Financial and authentication API responses are not cached for offline use. Internet access is required for live account data.

## Architecture

```text
User browser or installed PWA
            |
            v
Next.js and TypeScript on Vercel
            |
            | HTTPS REST API
            v
FastAPI on Render
       |              |
       v              v
PostgreSQL         GroqCloud
on Neon            read-only AI
```

### Technology stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind CSS, Recharts |
| Backend | FastAPI, Python, Pydantic, SQLAlchemy |
| Database | PostgreSQL on Neon |
| Migrations | Alembic |
| AI | GroqCloud through FastAPI |
| Transactional email | Brevo |
| Frontend deployment | Vercel |
| Backend deployment | Render |
| CI and maintenance | GitHub Actions and Dependabot |
| App delivery | Progressive Web App |

## Financial Calculation Rules

PennyPilot uses PostgreSQL `NUMERIC(20,2)` and Python `Decimal` for authoritative money calculations.

```text
Net expenses = recorded expenses - recorded refunds
Actual savings = recorded income - net expenses
Savings rate = actual savings / recorded income × 100
```

The savings rate is unavailable when recorded income is zero.

Transfers, balance adjustments, planned purchases, savings-goal allocations, and projected recurring items are excluded from income and expense totals until they create actual financial activity.

## Security Highlights

- Argon2 password hashing
- Expiring and revocable sessions
- Server-side ownership checks
- Exact-origin CORS configuration
- Pydantic validation
- Parameterised SQLAlchemy queries
- Private receipt access
- Rate limiting for authentication, password reset, and AI usage
- Server-side secrets on Render
- Database migrations through Alembic
- Password-confirmed account deletion
- Separate private administrator credentials
- No bank credential collection

PennyPilot is an educational portfolio project and has not undergone an independent security audit. It is not a bank, regulated financial institution, investment adviser, tax adviser, or audited accounting product.

## Repository Structure

```text
PennyPilot/
├── frontend/                  Next.js website and installable app
├── backend/                   FastAPI API, models, migrations, and tests
├── docs/                      Architecture, risk, requirements, and FinOps
├── .github/workflows/         Automated verification
├── compose.yaml               Optional local PostgreSQL setup
├── render.yaml                Render service configuration
└── README.md
```

## Local Development

### Requirements

- Node.js 22 LTS
- Python 3.12
- npm
- Git
- PostgreSQL 16, or Docker for an optional local database

### Backend

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

Backend endpoints:

```text
API documentation: http://localhost:8000/docs
Liveness:         http://localhost:8000/health
Readiness:        http://localhost:8000/ready
```

### Frontend

Open a second terminal:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

The local frontend environment should contain:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Never place database, Groq, Brevo, password-reset, session, or administrator secrets in frontend code or `NEXT_PUBLIC_*` variables.

## Verification

### Frontend

```powershell
cd frontend
npm run typecheck
npm run build
```

### Backend

Use a disposable test database:

```powershell
cd backend
python -m pytest -q
python -m alembic check
python -m alembic heads
```

There must be exactly one Alembic head before deployment.

## Deployment

### Vercel

- Repository: `Leo-Varghese/PennyPilot`
- Root Directory: `frontend`
- Production branch: `main`
- Required environment variable:

```text
NEXT_PUBLIC_API_BASE_URL=https://YOUR-RENDER-SERVICE.onrender.com
```

Do not append `/api/v1`; the frontend API client adds it.

### Render

- Root Directory: `backend`
- Build command:

```text
pip install -r requirements.txt
```

- Start command:

```text
python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- Health-check path:

```text
/ready
```

Important backend environment variables include:

```text
DATABASE_URL
SESSION_SECRET
SESSION_HOURS
FRONTEND_ORIGINS
APP_ENV
GROQ_API_KEY
GROQ_MODEL
BREVO_API_KEY
EMAIL_FROM
PASSWORD_RESET_SECRET
FRONTEND_ORIGIN
ADMIN_USERNAME
ADMIN_PASSWORD_HASH
ADMIN_SESSION_SECRET
```

All secret values must remain in Render. Never commit them to GitHub or place them in screenshots.

## Free-Tier Notice

PennyPilot currently operates within provider free-tier allowances.

- Render and Neon may require 30–60 seconds to wake after inactivity
- Brevo provides 300 email sends per day on the free plan
- GroqCloud availability depends on model-specific free quotas
- Vercel, Render, Neon, Brevo, and GroqCloud limits can change

Production or commercial use requires renewed cost, availability, security, privacy, backup, and support planning.

## Consulting Documentation

PennyPilot includes client-style solution documentation:

- [Executive Summary](docs/EXECUTIVE-SUMMARY.md)
- [Solution Overview](docs/SOLUTION-OVERVIEW.md)
- [Requirements Traceability](docs/REQUIREMENTS.md)
- [Risk Register](docs/RISK-REGISTER.md)
- [Cloud Economics and FinOps](docs/FINOPS.md)
- [Roadmap](docs/ROADMAP.md)
- [Architecture Decision Records](docs/architecture/)

## Roadmap

### Current

- Full personal-finance workflow
- AI Coach and lifetime financial intelligence
- Planned Purchases
- CSV bank-statement import
- Password recovery
- Private administrator portal and Site Doctor
- Installable mobile and desktop PWA

### Next hardening priorities

- Email verification
- Multi-factor authentication
- Tested backup restoration
- Structured audit events
- Distributed rate limiting
- Private object storage for receipts
- Accessibility and security audits
- Performance monitoring
- Google Play packaging and closed testing
- iOS TestFlight and App Store packaging

## Project Journey

PennyPilot began as my first complete full-stack project and became a practical learning environment for:

- Translating requirements into working software
- Designing financial data models and calculation rules
- Building secure frontend and backend authentication
- Managing relational database migrations
- Connecting multiple cloud providers
- Applying privacy boundaries to AI and administration
- Debugging deployment, encoding, migration, cache, and free-tier issues
- Documenting architecture, cost, risk, and implementation trade-offs

The project will continue to improve as I develop deeper skills in cloud architecture, responsible AI, security, DevOps, analytics, and technology consulting.

## Updating the Application

```powershell
git add .
git commit -m "Describe the update"
git push origin main
```

Pushes to `main` trigger the configured Vercel and Render deployments. PostgreSQL records remain in Neon and are not rebuilt during normal code deployments.

## Acknowledgement

PennyPilot was developed as a learning and portfolio project using modern open-source technologies and free cloud-service tiers. AI-assisted development tools supported planning, implementation, debugging, documentation, and refinement, while architecture, deployment, testing, and iterative decisions formed part of the project learning process.

## Licence

This repository currently has no explicit open-source licence. Unless a licence is added, all rights are reserved by the project author. Third-party dependencies remain subject to their respective licences.
