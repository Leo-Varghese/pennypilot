# ADR-002: Use Decimal-Safe Money Calculations

## Context

Binary floating-point arithmetic can produce unacceptable rounding behaviour for financial calculations.

## Options Considered

1. JavaScript and Python floating-point values
2. Integer minor units
3. Python Decimal with PostgreSQL NUMERIC

## Decision

Use Python Decimal and PostgreSQL NUMERIC(20,2) as the authoritative representation.

## Rationale

The approach supports explicit two-decimal currency values and avoids common binary floating-point errors.

## Consequences

API money values are serialised as strings. Frontend numeric conversion is limited to presentation and chart coordinates rather than authoritative calculation.
