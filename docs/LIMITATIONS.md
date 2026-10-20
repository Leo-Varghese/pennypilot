# Remaining limitations and release gates

This is a substantial repository-ready implementation, **not a fully verified production release or complete parity with every requested feature**.

1. Frontend dependency installation was blocked by the workspace package proxy (503, missing cache entries, timeouts). TypeScript syntax transpilation passed, but a complete dependency-aware typecheck and Next.js production build have not been verified here. Run the included CI before deployment and fix any reported issues. No browser end-to-end or visual QA was completed.
2. No authorized GitHub, Vercel or Render integration was available. No repository was pushed and no live service URLs exist from this delivery.
3. SQLite integration tests pass. PostgreSQL migration application and schema drift check succeeded; the first full PostgreSQL test attempt timed out. Consult VERIFICATION.md for the final recorded status rather than assuming a pass.
4. Optional zero-based mode is an income-allocation guide, not full available-cash envelope budgeting. Goals earmark money without checking aggregate available cash. Overlapping budgets can double-count the same spending in combined remaining totals; avoid overlaps.
5. Chart totals are database-backed. Income/expense aggregates use SQL; several chart groupings and comparisons iterate bounded transaction results in Python. Analytics/export cap at 50,000 records; transaction pagination is server-side. Category budget queries and transaction tag/receipt lookups can produce N+1 queries. Optimize before large-scale use.
6. Chart drilldown is implemented for dates, categories, merchants, sources and budget allocations. Weekday and net-worth charts do not have transaction drilldown. Category trend is a daily category bar series rather than a multi-line pivot. Empty dates are not filled into time series. Net worth uses explicit snapshots only, not reconstructed historical asset valuations.
7. Reports support Excel-compatible CSV and browser print/save PDF. No native XLSX or server-generated PDF report is included.
8. Receipts accept PNG/JPEG only, 2 MiB each, stored in PostgreSQL. No PDF receipts, malware scanning, OCR or object-storage offloading.
9. No bank sync, investment-price feed, FX conversion, split transactions, debt-interest amortization, notification delivery, email verification, password recovery or MFA.
10. No background scheduler automatically posts transactions. Recurring payment posting is explicit and idempotent per due date. Projection expansion is bounded and very old overdue daily rules may require cleanup. Paid schedule transactions are protected from edit/delete; reverse them explicitly.
11. CSV duplicate detection is exact-file only. Formula-neutralized exports are not a lossless roundtrip. Full JSON export includes receipts but there is no automated restore endpoint.
12. Frontend sessions are memory-only, so page refresh requires login. API sessions expire and can be revoked; there is no refresh-token flow. Only auth routes have built-in rate limits. Use platform abuse controls and review security before public access.
13. Preferences accept three-letter uppercase currency codes, not a curated currency catalogue. Monetary precision is fixed at two decimals, suitable for INR but not every world currency. Display/chart coordinates use JavaScript numbers; backend Decimal is authoritative.
14. Goal estimates use a simple calendar-month calculation. Current net worth and balances are explicitly current, even when a past transaction date filter is selected.
15. Dependency versions are pinned directly; a verified frontend lockfile could not be produced in this workspace. Generate and commit one on a normal network, then use npm ci. Review dependency security updates before release.
