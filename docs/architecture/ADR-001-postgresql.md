# ADR-001: Use PostgreSQL for Financial Records

## Context

Financial records must survive browser resets and application redeployments while supporting constraints, transactions, indexes, and schema evolution.

## Options Considered

1. Browser localStorage
2. Temporary JSON files
3. PostgreSQL

## Decision

Use PostgreSQL hosted on Neon.

## Rationale

PostgreSQL provides persistent storage, ACID transactions, foreign keys, NUMERIC money columns, indexes, and Alembic migration support.

## Consequences

PennyPilot gains stronger integrity and portability but depends on database availability, connection management, backups, and safe migrations.
