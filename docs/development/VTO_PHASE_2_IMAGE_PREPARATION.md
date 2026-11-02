# VTO Phase 2 — Image Acquisition and Garment Preparation

**Project:** FashXStudio
**Phase:** VTO-2
**Status:** Implementation specification
**Objective:** Produce secure, validated, normalized garment images for virtual try-on inference.

## 1. Scope
Phase 2 processes authorized retailer images and converts them into standardized private assets.

Included:
- Source and item-level image permission checks
- HTTPS-only image acquisition
- Approved-host allowlisting
- Download size and content-type limits
- Image byte validation
- EXIF orientation correction
- RGB conversion and JPEG normalization
- SHA-256 content hashing
- Private local/S3-compatible storage
- Prepared image metadata

Excluded:
- User/person image processing
- Garment segmentation and background removal
- AI try-on generation
- Exact garment fit estimation
- Custom model training

## 2. Processing rules
- The source must be cleared.
- Image display/storage rights must be present.
- Try-on eligibility additionally requires source-level try-on permission, item-level try-on permission and mirror storage policy.
- Only approved HTTPS hosts are accepted.
- Redirects are rejected.
- Downloads are limited to 8 MB.
- JPEG, PNG and WEBP are accepted.
- The image must pass Pillow byte validation.
- Normalized output is JPEG, maximum 1024 pixels on either dimension.
- Storage keys are based on source, product ID and normalized image hash.
- The original external URL is not a storage key.
- Images are private and must be accessed through authorized backend operations or short-lived signed URLs.

## 3. Storage layout
`garments/{source_slug}/{source_product_id}/{sha256}.jpg`

The database `GarmentImage` record stores:
- `garment_id`
- `storage_key`
- `content_hash`
- `image_type`
- `version`

## 4. Security requirements
- Never accept arbitrary image URLs from mobile clients.
- Never infer permission from successful download.
- Never follow redirects without validating the destination host.
- Restrict worker outbound network traffic in production.
- Keep S3/R2 buckets private.
- Do not expose storage credentials or permanent object URLs.
- Record image provenance and source permission decisions.
- Provide a takedown process that can delete stored assets.
- Avoid logging signed URLs or sensitive credentials.

## 5. Quality requirements
A prepared image must:
- Decode successfully.
- Have a supported format.
- Remain within configured byte and pixel limits.
- Have a valid normalized JPEG representation.
- Have a reproducible SHA-256 hash for identical normalized bytes.
- Be stored successfully before being marked prepared.

## 6. Completion criteria
- Unit tests cover invalid formats, dimensions, permissions and storage.
- At least one authorized partner image is successfully acquired.
- The prepared image is retrievable from private storage.
- The database points to the actual stored image.
- The VTO eligibility decision is independently verified.
- No image is considered prepared solely because its URL exists.

## 7. Known limitations
This phase does not isolate the garment from a model or lifestyle photograph. Segmentation and garment preprocessing quality require a later model-assisted stage and evaluation dataset.
A successful Phase 2 run does not prove that a garment will produce a high-quality try-on result. That must be evaluated during VTO model integration and quality evaluation.
