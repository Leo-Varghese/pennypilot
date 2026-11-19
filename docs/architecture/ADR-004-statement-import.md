# ADR-004: Implement Statement Import Before Live Bank Sync

## Context

Users need faster historical transaction entry, but live Account Aggregator integration requires eligibility, onboarding, consent controls, security, reconciliation, and likely commercial arrangements.

## Options Considered

1. Collect bank credentials and scrape bank websites
2. Live Account Aggregator production integration
3. User-reviewed CSV statement import

## Decision

Implement CSV statement import with mapping, preview, duplicate detection, and batch tracking.

## Rationale

Statement import provides real value without collecting passwords, OTPs, PINs, or claiming regulated production access.

## Consequences

Users must download and upload statements manually. Bank formats vary, and reconciliation still requires user review.
