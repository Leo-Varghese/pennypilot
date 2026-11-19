# PennyPilot Risk Register

| Risk | Likelihood | Impact | Current Control | Residual Limitation |
|---|---|---|---|---|
| Free backend cold start | High | Medium | Login notice, readiness endpoint, controlled retry | First request can remain delayed |
| AI hallucination | Medium | High | Aggregate-only context, read-only route, deterministic dashboard | Explanations still require verification |
| Duplicate statement import | Medium | High | File digest and transaction fingerprints | Modified statement copies require review |
| Cross-user data exposure | Low | Critical | Server-side ownership filters and isolation tests | Independent penetration test not completed |
| Incorrect category suggestion | Medium | Medium | User preview and confirmation | User judgement remains required |
| Groq quota exhaustion | Medium | Medium | Per-user application limit and no paid fallback | AI temporarily becomes unavailable |
| Database migration failure | Low | High | Alembic chain and pre-deploy migration | Backup and rollback procedures need formalisation |
| Credential exposure | Low | Critical | Platform secrets and no public AI key | Operational account security remains necessary |
| Free-tier capacity exhaustion | Medium | Medium | Cost-conscious MVP and usage monitoring | Upgrade path may introduce cost |
| Receipt storage growth | Medium | Medium | File size/type restrictions | PostgreSQL is not ideal for large-scale media storage |
| Incorrect bank-statement interpretation | Medium | High | Mapping, preview, and explicit import approval | Bank formats vary and can change |
| Unverified production security | Medium | High | Secure coding controls and tests | No independent audit or regulatory certification |
