# RC-02 — UI/UX Design System & Reusable Components

## Design Principles
1. **Editorial Fashion Aesthetic**: Warm ivory surfaces (`#F9FAFB` / `#FFFFFF`), deep charcoal typography (`#111827`), subtle borders (`#E5E7EB`), and restrained brand accents (`#4F46E5`).
2. **Product-First Visual Hierarchy**: High-contrast, unclipped photography with consistent aspect ratios (`0.78` portrait).
3. **Consistent Touch Targets**: All interactive elements adhere to accessibility standards (`minHeight: 48px`).
4. **Resilient Feedback States**: Every action provides immediate loading indicators, disabled states, and error recovery.

## Component Inventory

### 1. `Button`
- **File**: [`mobile/src/design-system/components/Button.tsx`](file:///c:/Users/ASUS/Documents/FashXStudio/mobile/src/design-system/components/Button.tsx)
- **Variants**: `primary`, `secondary`, `outline`, `danger`.
- **States**: `loading` (shows `ActivityIndicator`), `disabled` (50% opacity), pressed feedback.
- **Accessibility**: Explicit `accessibilityRole="button"`, `accessibilityLabel`, and `accessibilityState={{ disabled, busy }}`.
- **Unit Tests**: [`mobile/src/design-system/components/__tests__/Button.test.tsx`](file:///c:/Users/ASUS/Documents/FashXStudio/mobile/src/design-system/components/__tests__/Button.test.tsx) (4 unit tests passing).

### 2. `ProductCard`
- **File**: [`mobile/src/design-system/components/ProductCard.tsx`](file:///c:/Users/ASUS/Documents/FashXStudio/mobile/src/design-system/components/ProductCard.tsx)
- **Features**:
  - Expo Image with fade transitions and caching.
  - Price formatting in INR via `Intl.NumberFormat`.
  - Try-on badge indicator when supported.
  - Secondary Save action with busy and saved states.
  - Primary Try-On action trigger.

### 3. `SearchBar`
- **File**: [`mobile/src/design-system/components/SearchBar.tsx`](file:///c:/Users/ASUS/Documents/FashXStudio/mobile/src/design-system/components/SearchBar.tsx)
- **Features**: Debounced text input, search icon, clear button (`✕`), pill border radius (`radius.pill`).

### 4. `CategoryChip`
- **File**: [`mobile/src/design-system/components/CategoryChip.tsx`](file:///c:/Users/ASUS/Documents/FashXStudio/mobile/src/design-system/components/CategoryChip.tsx)
- **Features**: Pill chip with selected vs unselected token styling, high-contrast text on selection.

### 5. `SectionHeader`
- **File**: [`mobile/src/design-system/components/SectionHeader.tsx`](file:///c:/Users/ASUS/Documents/FashXStudio/mobile/src/design-system/components/SectionHeader.tsx)
- **Features**: Title, subtitle, and optional text action button.

### 6. `ProductSkeleton`
- **File**: [`mobile/src/design-system/components/ProductSkeleton.tsx`](file:///c:/Users/ASUS/Documents/FashXStudio/mobile/src/design-system/components/ProductSkeleton.tsx)
- **Features**: Animated loading placeholder with image box and text lines.

### 7. `Badge`
- **File**: [`mobile/src/design-system/components/Badge.tsx`](file:///c:/Users/ASUS/Documents/FashXStudio/mobile/src/design-system/components/Badge.tsx)
- **Variants**: `brand`, `neutral`, `success`, `warning`, `danger`.
