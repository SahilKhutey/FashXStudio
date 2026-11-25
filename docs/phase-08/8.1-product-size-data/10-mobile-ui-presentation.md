# 10 — Mobile UI Presentation

## 1. UI Component Architecture

Mobile components are located in `mobile/src/features/product-size/`:
- `ProductSizeChart.tsx`: Full-width sizing table, unit switcher, system badges, provenance footer, and mandatory fit disclaimers.
- `AvailableSizes.tsx`: Variant size selection pill grid showing stock availability states.

## 2. Key UI Invariants

### 2.1 Explicit Unit Toggling
- Shoppers can toggle between Centimeters (`CM`) and Inches (`IN`).
- Measurements re-render instantly without network latency using the pre-computed `normalized_cm` values.

### 2.2 Sizing System Visibility & Unmapped Warnings
- The merchant's native sizing system is clearly displayed (e.g., "US Women's Numeric").
- If the shopper selects a different system but no verified mapping exists, an info banner clarifies:
  *"Showing merchant's native US sizes. Direct conversion to your preferred system is not verified by this merchant."*

### 2.3 Prominent Physical Fit Disclaimer
The UI renders a mandatory disclaimer:
> **Disclaimer**: *Size charts describe physical garment dimensions provided directly by the merchant. Visual try-on simulates visual drape only and does not establish verified physical fit.*

### 2.4 Availability Status Styling
| Status | Badge Color | Interaction |
|---|---|---|
| `IN_STOCK` | Green (`#DCFCE7`) | Selectable |
| `LOW_STOCK` | Amber (`#FEF3C7`) | Selectable ("Few Left") |
| `OUT_OF_STOCK` | Red (`#FEE2E2`) | Disabled, Strikethrough |
| `UNKNOWN` | Grey (`#F3F4F6`) | Selectable ("Availability Unknown") |
