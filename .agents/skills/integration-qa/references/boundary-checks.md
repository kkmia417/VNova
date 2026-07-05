# Boundary Checks

Use this reference when comparing both sides of a changed contract.

## API and Client

- endpoint path and method match
- request body fields match validators
- response fields match client types
- error shape is handled
- loading, empty, and failure states are represented

## Routes and Navigation

- generated links match actual routes
- dynamic parameter names match
- redirects and fallback states are intentional
- route guards match auth requirements

## Scripts and Docs

- command names match actual files
- required arguments are documented
- examples use valid paths
- platform-specific shell syntax is marked

## Skills and Harness Files

- `SKILL.md` references existing files
- frontmatter `name` matches folder
- `description` includes trigger conditions
- `agents/openai.yaml` has a default prompt with `$skill-name`
- validation commands exist

## Data and Persistence

- schema fields match model code
- migrations match query assumptions
- default values are handled
- nullable fields are checked before use

## Reporting

Prioritize contract mismatches over style. A mismatch is actionable when it can cause a runtime failure, stale docs, invalid generated skill, or user-visible behavior drift.
