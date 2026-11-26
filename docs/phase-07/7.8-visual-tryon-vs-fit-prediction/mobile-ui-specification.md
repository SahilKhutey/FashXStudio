# Mobile UI Specification: Disclosures & Sizing

> **Component architecture, accessibility, and user interaction patterns.**

## 1. Components
1. **`VisualTryOnDisclosure.tsx`**:
   - Renders a prominent card directly below the virtual try-on render.
   - States: "AI-generated visual try-on. This image shows how the garment might look on you. It does not verify the garment's physical size or fit."
   - Accessibility: `accessibilityRole="summary"`, screen reader accessible.
2. **`ProductSizeChart.tsx`**:
   - Renders merchant-supplied size tables in product detail screens.
   - Shows merchant provenance, verification status, and basis (`Body measurements` vs `Garment measurements`).
   - Supports horizontal scrolling and empty/stale state warnings.
3. **`ReportTryOnModal.tsx`**:
   - Shopper reporting modal with 9 standardized reason codes.
   - Optional text details and explicit consent toggle for internal quality review.

## 2. Invariant: Independent Sections
In the mobile app, the Try-On result view and the Size Chart view are separate components. The try-on screen includes an explicit link to "View merchant size chart" rather than embedding sizing claims inside the try-on image.
