# PennyPilot Free Maintenance Policy

PennyPilot uses a controlled, zero-cost maintenance workflow:

1. GitHub Dependabot checks frontend, backend, and GitHub Actions dependencies.
2. Dependabot creates pull requests instead of changing production directly.
3. GitHub Actions verifies the frontend build, backend tests, and migrations.
4. AI-assisted development may help explain or repair pull requests within free or student-plan limits.
5. The repository owner reviews and merges approved updates.
6. Vercel and Render deploy only after an approved change reaches `main`.

## Update policy

| Change type | Handling |
|---|---|
| Security patch | Review promptly and merge after CI passes |
| Patch or minor dependency update | Grouped weekly pull request |
| Major framework update | Separate pull request and manual review |
| Authentication or financial calculation | Dedicated tests and manual review |
| Database migration | Manual schema inspection and backup |
| AI provider or model change | Branch testing before production |

## Zero-cost and safety rules

- No paid maintenance agent or automatic paid AI fallback.
- No bot receives Neon, Render, Vercel, or Groq administrator credentials.
- No bot bypasses branch protection or merges directly to `main`.
- No paid GitHub Actions runners.
- Optional paid-usage budgets remain at zero.
- Failed builds, tests, migration checks, ownership tests, or financial tests block merging.

```text
Dependabot proposes
â†’ GitHub Actions verifies
â†’ AI assistance may help repair
â†’ Leo reviews
â†’ Leo merges
â†’ Vercel and Render deploy
```