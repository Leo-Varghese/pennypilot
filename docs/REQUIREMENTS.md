# PennyPilot Requirements Traceability

| Requirement | Business Reason | Implementation | Verification Evidence |
|---|---|---|---|
| Transfers excluded from expenses | Avoid misleading spending totals | Source and destination account transfer record | Transfer calculation test |
| Credit-card payments not double-counted | Avoid recording one purchase twice | Purchase is expense; payment is transfer | Credit-card flow test |
| Decimal-safe money | Prevent rounding errors | Python Decimal and PostgreSQL NUMERIC | Decimal arithmetic test |
| User data isolation | Protect financial privacy | Ownership filters in API queries and mutations | Cross-user isolation test |
| Persistent records | Preserve data across browser and code deployments | PostgreSQL on Neon | Deployment persistence check |
| Explainable aggregate definitions | Make reports auditable | Backend calculation rules and displayed definitions | Dashboard consistency test |
| AI cannot modify data | Reduce AI-related risk | Read-only AI route with no mutation tools | Mutation-prompt acceptance test |
| AI key stays private | Prevent provider credential exposure | Render environment variable; no public frontend key | Browser network inspection |
| Schema updates preserve data | Support safe releases | Alembic migrations | Migration and drift checks |
| Statement imports avoid duplicates | Prevent overstated balances | File digest and transaction fingerprint | Repeated-statement import test |
| Imported rows remain reviewable | Support correction and reconciliation | Preview before commit and editable transactions | Import workflow test |
| Provider failure does not break finance tracking | Maintain core availability | AI errors isolated from ledger routes | AI quota/failure test |
