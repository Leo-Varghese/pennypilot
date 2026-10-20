# Executed verification

## Passed

- Backend imports and generated OpenAPI: actual FastAPI application loaded; generated schema included as openapi.json.
- `python -m pytest -q --color=no`: **14 passed**, one dependency deprecation warning, using disposable SQLite with foreign keys enabled. See backend-tests.txt.
- Coverage includes registration/login/logout, Argon2 hashing, authentication limits, transaction CRUD/duplicate/tags/search, income/expense/refund arithmetic, transfers, credit-card purchase/payment treatment, Decimal precision, budget remaining/rollover, goal contribution non-double-counting, date/timezone/DST boundaries, CSV atomicity/duplicates/export, cross-user isolation, CORS, private receipts, preferences and account deletion.
- Actual PostgreSQL 16.2: `alembic upgrade head` exited 0; `alembic check` exited 0 with no new upgrade operations. See postgres-verification.txt. This was a real local PostgreSQL server, not Render.
- Actual Uvicorn startup and HTTP health/readiness smoke check: see startup-smoke.txt.
- Frontend TypeScript files parsed/transpiled without syntax errors. This is not a dependency-aware typecheck. See frontend-syntax-check.txt.

## Not passed / not completed

- Full PostgreSQL pytest run timed out in this workspace. A later attempt emitted three passing test markers before timeout; that is not a completed suite or a final test count. See postgres-tests.txt. The GitHub workflow runs the full suite against PostgreSQL, but it has not been executed on GitHub here.
- Frontend package installation repeatedly failed or timed out through the workspace package proxy, including 503 Service Unavailable and unavailable offline cache entries. Consequently `npm run typecheck` and `npm run build` could not complete successfully with installed dependencies. See frontend-build-checks.txt. Do not interpret syntax transpilation as a successful production build.
- No browser automation, responsive screenshot review, real Vercel-to-Render request, hosted migration, backup restore, penetration test or load test was completed.
- No GitHub repository was created/pushed. No Render/Vercel service was deployed. No live URLs are claimed.

## Reproducibility

Backend requirements.lock.txt pins the dependency closure installed for these tests on Python 3.12. Frontend direct versions are pinned, but no verified npm lockfile is included because installation did not finish. On a normal network, run npm install, review the generated lockfile, run typecheck/build, then commit the lockfile and switch CI/deploy installs to npm ci.

## Required release gates

1. Green dependency-aware frontend typecheck and production build.
2. Green full PostgreSQL integration suite.
3. Browser smoke test against the actual deployed services, including CORS, ownership and persistence after redeploy.
4. Security review, dependency advisory review and tested backup/restore configuration before sensitive use.
