# Derivative Image Permission Policy

**Workstream**: 5.1.8 — Derivative Asset Creation, Storage & Distribution  
**Status**: Active  
**Enforcement Engine**: `backend/fashx/catalog/authorization/`

---

## 1. Definition of Derivative Works
A derivative work is any asset created by transforming, modifying, or synthesizing new visual representations from the original merchant product image. Examples include:
- Transparent PNG garment cutouts (background removed).
- 2D / 3D garment warp maps and UV textures.
- Color-normalized and lighting-standardized garment masks.
- Synthetic try-on preview composites (shopper body + warped garment).
- Downscaled multi-resolution asset pyramids and WebP/AVIF thumbnails.

---

## 2. Granular Derivative Permissions

### 2.1 `DERIVATIVE_CREATE`
- **Definition**: Authority to execute transformation algorithms that generate derivative images from original catalog media.
- **Enforcement**: Must be held concurrently with `IMAGE_FETCH` and `IMAGE_AI_PROCESS`.

### 2.2 `DERIVATIVE_STORE`
- **Definition**: Authority to retain generated derivative assets in object storage across user sessions.
- **Retention Limits**: Governed by `storage_limit_days`. If merchant agreement limits retention to 30 days post-generation, derivative assets are automatically purged upon expiry.

### 2.3 `DERIVATIVE_DISPLAY`
- **Definition**: Authority to display generated derivative assets (such as segmented garment flats or styled outfit collages) publicly to shoppers.

---

## 3. Copyright & Provenance Tracking
1. **Provenance Metadata**: Every derivative image stored in FashXStudio object storage includes S3 object tags recording:
   - `SourceID`: Originating `catalog_sources.id`.
   - `MerchantID`: Originating `merchants.id`.
   - `SourceProductID`: Originating merchant SKU.
   - `PermissionID`: ID of the `DERIVATIVE_CREATE` permission record.
2. **Takedown Cascade**: When a takedown is executed on a source, all derivative assets tagged with that `SourceID` are included in the purge cascade (`TakedownAsyncWorker`).
