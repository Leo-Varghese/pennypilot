# API reference

Base path: `/api/v1`. All financial endpoints require `Authorization: Bearer <token>`. Money is a decimal string. See [generated OpenAPI](openapi.json) or the running service `/docs` for exact request schemas.

| Method | Path | Operation |
|---|---|---|
| GET | `/health` | Health |
| GET | `/ready` | Ready |
| POST | `/api/v1/auth/register` | Register |
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/logout` | Logout |
| GET | `/api/v1/auth/me` | Me |
| DELETE | `/api/v1/auth/me` | Delete Me |
| GET | `/api/v1/preferences` | Preferences |
| PUT | `/api/v1/preferences` | Update Preferences |
| GET | `/api/v1/transactions` | List Transactions |
| POST | `/api/v1/transactions` | Create |
| POST | `/api/v1/transfers` | Create |
| POST | `/api/v1/transactions/bulk-category` | Bulk |
| GET | `/api/v1/transactions/{id}` | Detail |
| PUT | `/api/v1/transactions/{id}` | Edit |
| DELETE | `/api/v1/transactions/{id}` | Remove |
| POST | `/api/v1/transactions/{id}/duplicate` | Duplicate |
| PUT | `/api/v1/transactions/{id}/receipt` | Upload |
| GET | `/api/v1/transactions/{id}/receipt` | Receipt |
| DELETE | `/api/v1/transactions/{id}/receipt` | Delete Receipt |
| GET | `/api/v1/exports/transactions.csv` | Export Csv |
| POST | `/api/v1/imports/csv` | Import Csv |
| GET | `/api/v1/accounts` | Accounts |
| POST | `/api/v1/accounts` | Add Account |
| PUT | `/api/v1/accounts/{id}` | Edit Account |
| DELETE | `/api/v1/accounts/{id}` | Delete Account |
| GET | `/api/v1/categories` | Categories |
| POST | `/api/v1/categories` | Add Category |
| PUT | `/api/v1/categories/{id}` | Edit Category |
| DELETE | `/api/v1/categories/{id}` | Delete Category |
| GET | `/api/v1/tags` | Tags |
| GET | `/api/v1/budgets` | Budgets |
| POST | `/api/v1/budgets` | Add Budget |
| PUT | `/api/v1/budgets/{id}` | Edit Budget |
| DELETE | `/api/v1/budgets/{id}` | Delete Budget |
| GET | `/api/v1/goals` | Goals |
| POST | `/api/v1/goals` | Add Goal |
| PUT | `/api/v1/goals/{id}` | Edit Goal |
| DELETE | `/api/v1/goals/{id}` | Delete Goal |
| POST | `/api/v1/goals/{id}/contributions` | Contribute |
| DELETE | `/api/v1/contributions/{id}` | Delete Contribution |
| GET | `/api/v1/recurring` | Recurring |
| POST | `/api/v1/recurring` | Add Recurring |
| PUT | `/api/v1/recurring/{id}` | Edit Recurring |
| DELETE | `/api/v1/recurring/{id}` | Delete Recurring |
| POST | `/api/v1/recurring/{id}/pay` | Pay |
| GET | `/api/v1/holdings` | Holdings |
| POST | `/api/v1/holdings` | Add Holding |
| PUT | `/api/v1/holdings/{id}` | Edit Holding |
| DELETE | `/api/v1/holdings/{id}` | Delete Holding |
| POST | `/api/v1/snapshots` | Snapshot |
| GET | `/api/v1/analytics` | Dashboard |
| GET | `/api/v1/dashboard` | Dashboard |
| GET | `/api/v1/exports/data.json` | Data Export |

Standard errors: 401 missing/expired session; 404 unknown or non-owned record; 409 duplicate/reference conflict; 422 validation; 429 auth rate limit; 503 database unavailable. No cross-user existence details are disclosed.

Transaction list: page (1-based), page_size (1–100), start/end, currency, q, kind, category_id, account_id, merchant, tag, payment_method, sort. Sort values: date_desc, date_asc, amount_desc, amount_asc. PUT replaces the validated input fields; it is not a partial PATCH.

Recurring pay requires the exact due_date. Repeating a paid due date returns the existing transaction. Full JSON export contains sensitive receipt bytes encoded as base64.
