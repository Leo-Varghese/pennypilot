# PennyPilot Cloud Economics and FinOps

## Current MVP Architecture

| Service | Purpose | Current Approach | Primary Constraint |
|---|---|---|---|
| Vercel | Next.js frontend | Free-tier deployment | Personal/non-commercial terms and platform limits |
| Render | FastAPI backend | Free-tier web service | Cold starts and availability limitations |
| Neon | PostgreSQL | Free-tier database | Compute, storage, connections, and transfer limits |
| GroqCloud | AI inference | Free quota | Model-specific requests and token quotas |
| GitHub Actions | CI | Standard public-repository runners | Workflow and runner policies |

PennyPilot currently operates within available free-tier allowances. Free availability is not guaranteed indefinitely. Pricing and limits must be reassessed before commercial or production use.

## Primary Cost Drivers

- Monthly active users
- API requests per user
- Transactions and imported statement rows
- PostgreSQL compute and storage
- Database connections
- Receipt count and file size
- AI questions and response-token volume
- Backup retention and recovery objectives
- Monitoring and log retention
- Required uptime and response time

## Scaling Triggers

| Trigger | Recommended Response |
|---|---|
| Cold starts materially affect login | Move backend to an always-on plan |
| Database storage or compute approaches limits | Upgrade Neon and review indexes/query plans |
| Receipt volume becomes material | Use private object storage with signed access |
| AI demand exceeds free quota | Add stricter quotas, caching, or a budget-approved plan |
| Multiple backend workers are introduced | Add persistent distributed rate limiting |
| Consequential real-user data is stored | Enable tested backups, monitoring, and incident procedures |
| Commercial use begins | Reassess Vercel, Render, Neon, Groq, privacy, and support terms |

## Suggested FinOps KPIs

- Cost per monthly active user
- API requests per active user
- Database storage per user
- Average AI tokens per question
- AI questions per user per month
- Cold-start rate
- Statement-import success rate
- Duplicate-import prevention rate
- Average API latency
- Error rate by service
