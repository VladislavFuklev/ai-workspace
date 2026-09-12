---
name: testing
description: Test strategy for this repository — what to test at which level, backend pytest and integration patterns, frontend Vitest/RTL/MSW patterns, Playwright journeys, tenant-isolation and AI testing, and the rules on fixtures, flakiness and coverage. Use when writing tests, when adding a feature that needs them, or when a test fails.
---

# Testing

Tooling lands progressively: pytest and Vitest in 0.4/phase 12, MSW at 12.3,
Playwright at 12.8. The strategy below applies from the first test written.

## What a test is for

A test exists to catch a regression in behavior a user depends on. It is not there
to raise a coverage number, and it is not documentation of the implementation.

Two rules from the master prompt, restated because they are the ones most often
broken under pressure:

1. **Never weaken or delete a test to make it pass.** A failing test is either a
   real defect or a wrong expectation. Decide which, in the open, and say so.
2. **Never write code that detects the test environment.** No branch on a test
   flag, no special-case for a fixture id. If production and test paths differ,
   the test proves nothing.

## Level selection

Pick the cheapest level that would actually catch the bug.

| Level | Use for | Do not use for |
| --- | --- | --- |
| Unit | pure logic: chunking, cost math, permission rules, validators, formatters | anything needing a DB or HTTP |
| Integration (API + real Postgres) | routes, repositories, migrations, transactions, **authorization and tenant isolation** | UI behavior |
| Component (Vitest + RTL) | what the user sees and does in one component or feature | routing across pages |
| MSW | frontend against a realistic API without a backend | asserting backend behavior |
| E2E (Playwright) | a handful of critical journeys end to end | edge cases, error permutations |

Most value sits in the middle two rows. A suite that is all unit tests passes while
the product is broken; a suite that is all E2E is slow and flaky.

## Backend

- pytest with `httpx.AsyncClient` against the FastAPI app.
- **Integration tests run against real PostgreSQL with pgvector**, from the compose
  stack. SQLite is a different database; a test that passes on it proves nothing
  about a query using pgvector, JSONB, or a Postgres-specific constraint.
- Each test gets a clean database state — a transaction rolled back per test, or a
  truncate between tests. Order dependence is a defect in the suite.
- Factories over fixtures-with-everything. A test should state only the data its
  assertion depends on; anything else hides what is being tested.
- Override dependencies through FastAPI's DI to inject fakes. Do not monkeypatch
  module internals — that couples the test to the implementation.
- Migrations are tested: the suite runs them from empty, so a broken migration
  fails in CI rather than in deployment.

### Authorization tests are mandatory, not optional

For every endpoint that touches tenant data, there is a test that a member of
organization A **cannot** reach organization B's resource — and it asserts the
specific status code. Phase 4.7 and 11.4 formalize this; write them as the
endpoints appear, not retroactively.

The same applies to roles: for each permission, a test that a user without it is
refused. A permission system with no negative tests is decoration.

## Frontend

- Vitest, React Testing Library, `user-event`.
- **Query by role and accessible name.** `getByRole('button', { name: /upload/i })`
  is both a behavior assertion and an accessibility assertion. Reach for
  `data-testid` only when nothing semantic exists — and consider that a finding.
- Drive interaction with `user-event`, not `fireEvent`. Real users tab and type.
- Assert what the user perceives, not internal state. Never assert on a hook's
  internals or a component's props.
- MSW at the network boundary so the app under test uses its real API client.
  Handlers must match the real API's shapes, including its error shapes.
- Test the four states for any data-driven surface: loading, empty, error, success.
  Empty and error are the ones that ship broken.
- No arbitrary waits. Use `findBy*` and RTL's async utilities; a `setTimeout` in a
  test is a future flake.

## E2E

Keep the set small and about journeys that would be released-blocking:
sign up → create organization → upload a document → wait for processing → ask a
question → see a cited answer.

- Seed state through the API or a fixture script, not by clicking through setup.
- Deterministic AI: point E2E at the fake provider. An E2E suite whose result
  depends on a live model is a coin flip.
- Accessibility assertions belong here too (12.9) — run an axe check on key pages.

## AI-specific testing

- The default provider in tests is the fake one. No network, no API key, ever, in
  the required suite.
- Retrieval quality is measured against fixed fixtures (6.8) — a question set with
  expected chunks — so a chunking change produces a number, not an opinion.
- Test the failure modes explicitly: malformed JSON, truncated output, refusal,
  timeout, empty retrieval, tool error, and a document containing an injection
  attempt. These paths are where AI features actually break.
- Snapshot testing a model response is meaningless. Assert on structure, schema
  validity, citation integrity and error handling.

## Flakiness

A flaky test is worse than no test: it trains everyone to ignore red. When one
appears, fix the cause — a real race, a shared fixture, a time or ordering
assumption — or delete it and say why. Never add a retry to hide it.

## Coverage

Coverage (12.11) is a diagnostic, not a target. Use it to find untested branches
that matter — authorization decisions, error paths, retry logic. Do not write tests
to move the number, and never let a coverage threshold justify a meaningless test.

## Definition of done for a feature

- [ ] Happy path tested at the cheapest sufficient level
- [ ] Error and empty paths tested
- [ ] For tenant data: a cross-tenant denial test
- [ ] For permissions: a negative test per permission
- [ ] For AI: fake provider, plus at least one malformed-output case
- [ ] Suite passes offline, from a clean database, in any order
