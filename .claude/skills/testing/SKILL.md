# Testing Skill

Use for test planning and implementation.

Prefer the testing pyramid:
- unit tests for pure logic
- component tests for UI behavior
- integration tests for API/database boundaries
- MSW for frontend API isolation
- Playwright for critical user journeys

Tests verify behavior; never implement test-specific hacks.
