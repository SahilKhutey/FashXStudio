# Image Ingestion Policy

## 1. Scope & Isolation Principle

Product images are treated with strict copyright and pipeline isolation. Missing, invalid, or unpermitted images must **never** prevent valid apparel metadata from being ingested into the catalog.

```mermaid
flowchart TD
    A[Product Image URL] --> B{URL Valid & HTTPS?}
    B -- No / Empty --> C[Metadata Valid: Ingest Product with display_eligible=False]
    B -- Yes --> D{Source Rights Display?}
    D -- Denied --> C
    D -- Granted --> E{Source Rights Try-On?}
    E -- Granted --> F[Set display_eligible=True, tryon_supported=True]
    E -- Denied --> G[Set display_eligible=True, tryon_supported=False]
    F --> H[Persist to garment_images]
    G --> H
```

---

## 2. Granular Permissions Enforcement

1. **`IMAGE_FETCH` & `IMAGE_STORE`**: Evaluated during image acquisition. If storage permission is denied, raw image URLs are not archived to S3.
2. **`IMAGE_DISPLAY`**: If display rights are withheld by contract, the product is persisted without public imagery (`display_eligible = False`).
3. **`VTO_PROCESS` / `IMAGE_AI_PROCESS`**: Explicit permission is mandatory for virtual try-on pipelines. Lack of try-on consent sets `tryon_supported = False` while allowing consumer browsing.
