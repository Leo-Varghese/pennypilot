# Security and operational boundaries

## Implemented

- Argon2 password hashing through pwdlib; no plaintext passwords.
- Cryptographically random opaque bearer tokens, HMAC hashes stored server-side, expiry and logout revocation. Tokens are memory-only in the frontend. Refreshing the page requires login.
- All financial routes require authentication. Owned-record queries include user_id; related account/category/goal/schedule references are validated before writes. No client-provided user_id is trusted.
- Explicit CORS origins and Authorization headers. No authentication cookies are used, so cookie-based CSRF does not apply. CORS is not a substitute for authorization.
- Database-backed authentication attempt windows per email/IP. Limits survive API restarts. Multi-request updates use row locks where appropriate; concurrent initial attempt inserts may return a safe conflict.
- Parameterized SQLAlchemy queries, Pydantic input validation, forbidden unknown fields, amount/date/currency constraints, foreign keys, indexes and transaction rollback.
- Uploads: maximum 2 MiB, PNG/JPEG magic-byte validation, authenticated attachment download, no SVG/HTML, no public URLs. Bytes live in PostgreSQL. No malware scanning or full image decoding is implemented.
- CSV: 2 MiB / 5,000 rows, validated headers and ownership, atomic rollback, exact-file digest duplicate protection, spreadsheet formula-prefix neutralization on export.
- Safe generic database errors, no credentials in diagnostics, no-store headers, nosniff, frame denial and production HSTS.
- Full JSON data/receipt export and password-confirmed permanent user deletion.

## Before public or sensitive use

This is not an independently audited financial service. Enable HTTPS, use strong secrets, configure backups/restore tests, review dependency advisories, set platform-level request/body limits and abuse protection, and test deployed ownership/CORS. Add email verification, password reset, MFA and a complete audit trail before a broader launch. Only authentication routes have application-level rate limiting; other routes need platform-level abuse protection for public use.

PostgreSQL encryption-at-rest, backups, availability and recovery depend on your hosting configuration. There is no application-level end-to-end encryption. Do not log authorization headers or request bodies. A database administrator can access financial data and receipt bytes. Exported files are sensitive; store them privately.

Database ownership is enforced in application queries, not PostgreSQL row-level security. Schema changes and new endpoints must retain the ownership invariant. Tests must use disposable databases only: they drop and recreate the schema.

Session-secret rotation invalidates all existing sessions. Expired session/attempt rows are not automatically purged; add a controlled retention job if operating long term. Backups may retain deleted records according to your configured retention policy; deletion removes live records, not independently managed backups.

Report vulnerabilities privately to your repository owner. Never commit a credential to demonstrate a problem.
