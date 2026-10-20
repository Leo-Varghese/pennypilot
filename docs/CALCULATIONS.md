# Financial semantics

All stored amounts use SQL NUMERIC(20,2); backend arithmetic uses Decimal. API monetary values are strings. JavaScript converts them only for display/chart coordinates, never for authoritative calculations.

## Ledger

- Income adds to an account and income totals.
- Expense subtracts from an account and increases expense totals.
- Refund adds to an account and reduces expenses in the refund's recorded period/category. It is not income. Refunds are not linked to original purchases in this version.
- Transfer is one atomic record with a source and destination: subtract from source, add to destination. Neither side is income/expense. Both accounts must have the same currency.
- Adjustment changes an account balance using direction +1 or -1. It is excluded from income, expenses and savings.
- Opening balances are not income. Transactions before an account's opening date are rejected.
- Credit-card balances use the same signed ledger. A purchase makes a card balance more negative. A bank-to-card transfer pays it down without a second expense.

## Dashboard

Income = sum(recorded income). Net expenses = expenses − refunds. Net cash flow and actual savings = income − net expenses. Savings rate = actual savings / income × 100, rounded to 2 decimals, or null when income is zero. This is a recorded cash-flow definition, not a bank-balance-change or investment-return measure. It can be negative or exceed 100% when refunds exceed expenses.

Current account balances and net worth are current values, not historical values at the filter's end. Historical net worth is shown only from explicitly saved dated snapshots. Snapshot date uses the user's timezone. Holdings are separately configured assets/liabilities; never duplicate an account in holdings.

Comparison period is the immediately preceding equal number of local calendar days. Its exact start/end are returned and displayed. It is not automatically the previous calendar month. Category increases are arithmetic differences, never inferred reasons for spending.

## Budgets

Each allocation covers its category and direct subcategories. Allocating both a parent and its subcategory in the same budget is rejected. Remaining = allocation + signed rollover − net expenses during the budget's full dates. Rollover references an earlier non-overlapping period in the same currency. Positive and negative remaining amounts carry forward. Alerts trigger at 80% or more used. Budget history is retained; a budget with rollover successors is immutable through the edit endpoint.

Dashboard budget remaining sums full budgets that overlap the selected dates, not prorated amounts. Avoid overlapping budgets for the same spending. The optional zero-based mode is a **period income allocation guide**, not a full cash-available envelope engine. Unassigned income = period income − overlapping budget allocations; it does not authorize spending or reserve money.

## Goals and recurring schedules

Goal current amount = recorded contributions. Contributions earmark existing money; they do not create ledger transactions or change savings totals. Progress = current / target × 100. Monthly needed = remaining target divided by at least one remaining calendar-month interval; this is a simple planning estimate, not an interest forecast. Goal allocations are not validated against available bank cash in this version.

Recurring schedules are projections only. Recording paid locks the schedule, creates the actual transaction and a unique (schedule, due date) payment record in one database transaction, then advances the schedule. Repeating the same due-date request returns the existing transaction. Monthly rules retain their original day across short months. Paid schedule transactions are immutable; use an explicit refund/adjustment for corrections.

## Dates and currencies

API timestamps must include a timezone offset. Local inclusive date ranges become UTC half-open intervals [start-of-start-day, start-of-day-after-end), handling daylight-saving changes. Default timezone is Asia/Kolkata. All analytics and account queries are scoped to one currency. Cross-currency transfers are rejected; no exchange rates are invented.
