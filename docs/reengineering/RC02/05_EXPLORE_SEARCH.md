# RC-02 — Explore & Search Experience

## Architecture & Integration
The Explore screen ([`mobile/app/(tabs)/explore.tsx`](file:///c:/Users/ASUS/Documents/FashXStudio/mobile/app/(tabs)/explore.tsx)) fulfills the product discovery and search requirements across the fashion catalog.

## Features & Implementation
1. **Interactive Search**:
   - Built with [`SearchBar`](file:///c:/Users/ASUS/Documents/FashXStudio/mobile/src/design-system/components/SearchBar.tsx).
   - Real-time search by garment title, brand name, and category keywords.
   - Clear button to quickly reset active search strings.
2. **Category Chips**:
   - Filter pills for *All Styles*, *Tops*, *Bottoms*, *Dresses & Sets*, *Shoes*, and *Accessories*.
   - Instant filtering with zero latency.
3. **Two-Column Product Grid**:
   - 2-column responsive layout rendering `ProductCard` instances.
   - Try-on badge indicator when try-on is supported for the garment.
   - Inline save-to-wardrobe and direct navigation to garment detail (`/garment/[id]`).
4. **Resilient Loading & Empty States**:
   - Loading skeleton grid using [`ProductSkeleton`](file:///c:/Users/ASUS/Documents/FashXStudio/mobile/src/design-system/components/ProductSkeleton.tsx).
   - Contextual empty state with *"Clear Filters"* action button when queries yield no results.
   - Pull-to-refresh control hooked to backend query invalidation.
