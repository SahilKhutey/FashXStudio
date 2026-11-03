# RC-02 — Shopping Decision & Garment Detail Experience

## Architecture & Integration
The garment detail screen ([`mobile/app/garment/[id].tsx`](file:///c:/Users/ASUS/Documents/FashXStudio/mobile/app/garment/[id].tsx)) is the consumer's decision point between discovery, virtual try-on, wardrobe saving, and retailer purchasing.

## Features & Implementation
1. **Product Gallery & Details**:
   - High-resolution multi-image gallery with pagination dots and smooth scrolling.
   - Brand name, product title, category, and formatted price in INR.
   - Attribute chips detailing fabric, silhouette, care instructions, and style tags.
2. **Retailer Offers & Purchasing**:
   - Integrates [`RetailerOffers`](file:///c:/Users/ASUS/Documents/FashXStudio/mobile/src/features/wardrobe/RetailerOffers.tsx).
   - In-stock availability indicators.
   - Authorized retailer redirection using `useBuy()` hook, recording buy-clicks before external browser handoff.
3. **Action Triggers**:
   - **Save to Closet**: Persists garment snapshot into `wardrobe_items`.
   - **Virtual Try-On**: Submits try-on job via `useStartTryOn()` and transitions directly into the Try-On Studio (`/tryon/[jobId]`).
   - Disabled states for unavailable try-on garments or out-of-stock items.
