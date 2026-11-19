# ADR-003: Keep the AI Coach Read-Only

## Context

Generative AI can produce useful explanations but can also hallucinate or misinterpret financial intent.

## Options Considered

1. AI with direct transaction mutation tools
2. AI-generated suggestions requiring confirmation
3. Read-only AI over deterministic aggregates

## Decision

Use a read-only AI Coach that receives limited backend aggregates and has no mutation capability.

## Rationale

Authoritative calculations remain deterministic while the model focuses on explanation and communication.

## Consequences

The assistant cannot automate data entry or corrections. Users must verify answers against dashboard figures, and provider quotas can temporarily disable AI responses.
