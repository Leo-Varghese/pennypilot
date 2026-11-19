# PennyPilot Executive Summary

## Situation

Personal financial information is commonly fragmented across bank statements, payment methods, spreadsheets, and budgeting tools. This makes it difficult to maintain a consistent view of cash flow, budgets, recurring commitments, savings, and net worth.

## Complication

Financial applications must interpret transactions correctly. Transfers, refunds, credit-card repayments, recurring projections, savings-goal allocations, and duplicate statement imports can create misleading totals when the underlying ledger rules are unclear.

The solution must also protect user data, remain operable on a cost-conscious cloud architecture, and prevent generative AI from changing authoritative financial records.

## Response

PennyPilot is a cloud-native personal finance platform built with:

- Next.js and TypeScript on Vercel
- FastAPI on Render
- PostgreSQL on Neon
- GroqCloud through a protected backend AI route
- GitHub Actions and Dependabot for controlled maintenance

PennyPilot provides transaction tracking, accounts, budgets, savings goals, recurring payments, analytics, statement imports, and a read-only AI financial coach.

## Value Demonstrated

- One consolidated view of personal finances
- Decimal-safe financial calculations
- Transfers excluded from income and spending
- Credit-card payments protected from double-counting
- Persistent, user-isolated cloud data
- Database-backed analytics and lifetime aggregates
- Controlled AI explanations using a limited financial summary
- Reviewed dependency updates and automated verification
- A cost-conscious MVP designed around free-tier allowances

## Current Limitations

- Educational portfolio application, not an independently audited financial service
- No regulatory approval or live Account Aggregator production integration
- Free-tier cold starts and provider quotas can affect availability
- AI output requires verification against deterministic dashboard figures
- Production scaling requires stronger backups, monitoring, rate limiting, and operational controls

## Live Product

[PennyPilot Live Website](https://pennypilot-swart.vercel.app/)
