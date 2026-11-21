# Image Permission Policy

**Workstream**: 5.1.6 — Standard Image Rights & Operations  
**Status**: Active  
**Enforcement Engine**: `backend/fashx/catalog/authorization/`

---

## 1. Principle
Product imagery embodies proprietary intellectual property, model publicity rights, and commercial copyrights. FashXStudio treats image acquisition, storage, and rendering as distinct legal permissions governed by strict license scopes.

---

## 2. Standard Image Permissions

```
+-----------------------------------------------------------------------------------+
|                            IMAGE LIFECYCLE RIGHTS                                 |
+-----------------------------------------------------------------------------------+
|  [IMAGE_FETCH]   --> Authority to download binary image from CDN / source URL     |
|         |                                                                         |
|         v                                                                         |
|  [IMAGE_STORE]   --> Authority to store mirrored image in private FashX S3 bucket |
|         |                                                                         |
|         v                                                                         |
|  [IMAGE_DISPLAY] --> Authority to serve image to shopper mobile client / web view  |
+-----------------------------------------------------------------------------------+
```

### 2.1 `IMAGE_FETCH`
- **Definition**: Authority to issue HTTP requests to merchant image CDNs and download image binaries into temporary validation pipelines.
- **Constraints**: Downloaded images must be validated for format (JPEG, PNG, WebP), dimension thresholds, and safe decoding.

### 2.2 `IMAGE_STORE`
- **Definition**: Authority to store mirrored, normalized copies of merchant product images in FashXStudio's private S3 bucket (`fashx-catalog-images-ap-south-1`).
- **Policy Alternatives**:
  - `mirror`: Allowed only when `IMAGE_STORE` is GRANTED.
  - `hotlink`: If `IMAGE_STORE` is not granted, images are hotlinked directly from merchant CDN (provided `IMAGE_DISPLAY` is granted).

### 2.3 `IMAGE_DISPLAY`
- **Definition**: Authority to present product photos to shoppers within search results, product detail pages, and curated feeds.
- **Watermark & Attribution**: Where required by contract, brand watermarks and copyright notices must remain unedited.

---

## 3. Strict Non-Inference Rule (Critical Invariant)
Having `IMAGE_FETCH`, `IMAGE_STORE`, and `IMAGE_DISPLAY` permissions **DOES NOT** grant permission to:
1. Pass the image to a neural network, segmentation model, or feature extractor (`IMAGE_AI_PROCESS`).
2. Synthesize virtual try-on renders (`VTO_PROCESS`).
3. Generate garment cutout masks or 3D meshes (`DERIVATIVE_CREATE`).

Any attempt to perform AI or derivative operations using an image authorized solely for standard display will immediately trip the `CatalogAuthorizationEvaluator` and result in `DENY_PERMISSION_NOT_FOUND`.
