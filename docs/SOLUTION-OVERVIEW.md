# PennyPilot Solution Overview

## Business Problem

Users need a consistent way to record, classify, analyse, and explain financial activity across accounts and payment methods.

## Stakeholders

| Stakeholder | Primary Need |
|---|---|
| Financial user | Accurate and understandable personal-finance records |
| Product owner | Reliable features and controlled product evolution |
| Cloud operator | Deployable, observable, and cost-conscious services |
| Database operator | Data integrity, migrations, backups, and recovery |
| AI provider | Limited, policy-constrained inference requests |
| Future financial-data partner | Consent, security, reconciliation, and compliance |

## Current Architecture

```text
User Browser
    |
    v
Next.js + TypeScript
Vercel
    |
    | HTTPS REST API
    v
FastAPI
Render
    |
    v
PostgreSQL
Neon

FastAPI
    |
    | Limited aggregated financial context
    v
GroqCloud AI
```

## Architecture Responsibilities

| Component | Responsibility | Business Relevance |
|---|---|---|
| Vercel | Frontend delivery and automatic deployments | Responsive user access and rapid releases |
| Render | API, authentication, calculations, imports, and AI orchestration | Central control over business rules |
| Neon | Persistent PostgreSQL storage | Integrity, transactions, constraints, and portability |
| GroqCloud | Read-only natural-language explanations | Faster understanding without granting mutation authority |
| GitHub | Source control, CI, and dependency proposals | Traceable and reviewed change management |

## Key Design Decisions

### Decimal over floating point

Financial amounts use Python Decimal and PostgreSQL NUMERIC to reduce binary floating-point errors.

### PostgreSQL over browser storage

Financial records survive browser resets and deployments while benefiting from constraints, transactions, indexes, and migrations.

### Read-only AI

The AI explains backend-generated aggregates and cannot create, modify, or delete financial records.

### Statement import before live bank synchronisation

CSV import provides real value without collecting bank credentials or claiming regulated Account Aggregator production access.

## Evidence

- Versioned REST API under `/api/v1`
- Alembic-controlled schema changes
- User ownership checks in backend queries
- Automated financial-calculation tests
- Frontend typecheck and production build workflow
- Health and readiness endpoints
- Server-side Groq secret management
- Duplicate protection for imported statements

## Production Readiness Gap

Before consequential financial use, PennyPilot requires an independent security review, tested backup restoration, stronger observability, persistent distributed rate limiting, password recovery, email verification, MFA, and operational incident procedures.
