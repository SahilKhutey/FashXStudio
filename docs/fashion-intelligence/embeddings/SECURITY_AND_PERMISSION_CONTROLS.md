# Fashion Image Embedding Security & Permission Controls

## 1. Compliance with Rule I06 (Biometric & Personal Media Privacy)
The fashion catalog embedding pipeline processes merchant product catalog images exclusively. Under **Rule I06**:
- **Personal Shopper Imagery Isolation**: Shopper photos (e.g., profile pictures, user fitting photos from Phase 04.5) are processed through segregated, private pipelines and are NEVER routed through catalog embedding tables.
- **Biometric Prohibition**: No facial recognition, body scanning, or biometric feature extraction is performed in catalog image embeddings.
- **Air-Gapped / Self-Hosted Inference**: Model inference is executed strictly on self-hosted infrastructure. Image rasters and feature vectors are never transmitted to unapproved external APIs or cloud vision services.

---

## 2. Dynamic Permission Checks (`IMAGE_AI_PROCESS`)
Prior to embedding an image:
1. The subsystem verifies that the image's source merchant has the `IMAGE_AI_PROCESS` permission enabled.
2. If `IMAGE_AI_PROCESS` is absent or revoked, the embedding job terminates with status `SKIPPED_UNAUTHORIZED`, and an audit event is logged.
3. If an image is revoked or subjected to a takedown request (`ImageTakedownStatus.PROCESSING` or `COMPLETED`), its associated embedding records are marked `is_active = FALSE` and quarantined or purged from nearest-neighbor search indexes.

---

## 3. Data Integrity & Content Hash Verification
- Each embedding record stores the `image_sha256` hash of the preprocessed image bytes.
- If the original asset file is modified, the hash mismatch is detected, preventing stale vectors from serving active catalog queries.
