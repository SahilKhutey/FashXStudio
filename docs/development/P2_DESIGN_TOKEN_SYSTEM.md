# P2 — Design Token System

**Project:** FashXStudio  
**Status:** Implementation specification  
**Scope:** Mobile design-system foundation  

## Objective
Establish a single source of truth for visual values and shared UI primitives across the React Native application.

## Design-system layers
1. **Primitives:** Raw colors, spacing, typography scale, radii, elevation, opacity and stacking order.
2. **Semantic tokens:** Meaning-based colors for backgrounds, surfaces, text, borders, status and actions.
3. **Themes:** Light and dark themes with system-mode resolution.
4. **Typography:** Reusable text styles for headings, body text, labels, captions and buttons.
5. **Layout:** Standard gutters, control sizes, icon sizes, product imagery and content width.
6. **Responsive behavior:** Screen classifications, gutters and product-grid utilities.
7. **Motion:** Shared transition durations and press feedback.
8. **Accessibility:** Minimum touch targets, focus styling and scalable text.
9. **Components:** Token-backed text and button primitives.
10. **Validation:** Typecheck, unit tests, visual checks and regression testing.

## Rules
- UI components must not introduce arbitrary color, spacing, radius or typography values when an appropriate token exists.
- Semantic tokens must be used for screen-level colors.
- Platform and layout exceptions must be documented.
- Text must remain scalable.
- Interactive controls must have meaningful accessible labels and state.
- Theme changes must not break contrast or component states.

## Acceptance criteria
- All token modules compile under strict TypeScript.
- Theme resolution supports light, dark and system modes.
- Responsive utilities have unit tests.
- Shared text and button components use tokens.
- Feed and tab layouts have a documented migration plan.
- Authentication, feed, wardrobe and try-on flows pass regression checks.
- No new unnecessary hard-coded visual values are introduced.
- Device-level appearance and accessibility checks are recorded.

## Out of scope
This milestone does not complete a full screen redesign, custom font licensing, animation-library integration, or a user-facing theme preference setting. Those require separate implementation and verification.

## Completion rule
P2 is complete only after the code is merged, automated checks pass, representative screens are verified on a device, and the acceptance checklist is updated with actual evidence.
