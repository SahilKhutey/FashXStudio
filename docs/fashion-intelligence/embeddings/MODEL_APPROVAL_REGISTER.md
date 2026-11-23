# Fashion Image Embedding Model Approval Register

## 1. Purpose and Governance
This register records all machine learning models formally evaluated and approved for generating image embeddings within FashXStudio's catalog and visual intelligence pipeline.

In compliance with **Rule I06 (Biometric and personal media storage privacy)** and FashXStudio Catalog Integrity standards:
- Only models registered here with `Status: APPROVED` may be executed in production catalog embedding pipelines.
- Models must operate locally/self-hosted; no product images or media assets may be dispatched to unauthorized third-party inference endpoints.
- Each approved model must specify deterministic weights, input preprocessing specifications, and dimension guarantees.

---

## 2. Model Status Lifecycle
- `EVALUATION`: Candidate under active testing for accuracy, retrieval performance, and latency.
- `APPROVED`: Validated for production deployment; meets licensing and architectural requirements.
- `DEPRECATED`: In transition phase; supported for read/query during active blue/green migration.
- `RETIRED`: No longer used; all associated vectors migrated or archived.
- `REJECTED`: Disqualified due to licensing, performance, or privacy violations.

---

## 3. Approved Models Register

### Primary Baseline Model: OpenCLIP ViT-B/32
- **Model Identifier**: `openclip_vit_b32`
- **Model Version**: `v1`
- **Upstream Checkpoint**: `ViT-B-32-laion2b_s34b_b79k`
- **Architecture**: Vision Transformer Base / 32 patch size
- **Vector Dimension**: 512 dimensions
- **Vector Normalization**: L2 unit sphere ($\|v\|_2 = 1.0 \pm 10^{-5}$)
- **Distance Metric**: Cosine similarity (`pgvector` `<=>` operator)
- **Licensing**: MIT License (unrestricted commercial use permitted)
- **Deployment Mode**: Self-hosted local inference container / CPU & GPU worker pool
- **Status**: `APPROVED`
- **Effective Date**: 2026-11-21
- **Governing ADR**: `docs/adr/0006-image-embedding-model.md`
- **Intended Use**: Catalog visual product search, deduplication, style similarity, multimodal retrieval.

---

### Secondary Candidate: DINOv2 ViT-B/14
- **Model Identifier**: `dinov2_vit_b14`
- **Model Version**: `v1`
- **Upstream Checkpoint**: `dinov2_vitb14_pretrain`
- **Architecture**: Self-supervised Vision Transformer Base / 14 patch size
- **Vector Dimension**: 768 dimensions
- **Vector Normalization**: L2 unit sphere
- **Distance Metric**: Cosine similarity
- **Licensing**: Apache 2.0 (standard base checkpoint)
- **Deployment Mode**: Self-hosted local inference
- **Status**: `EVALUATION`
- **Intended Use**: Fine-grained silhouette and garment shape discrimination benchmark.

---

### Test / Development Model: Deterministic Mock Adapter
- **Model Identifier**: `mock_vit_b32`
- **Model Version**: `v1`
- **Architecture**: Deterministic cryptographic hash-seeded pseudo-vector generator
- **Vector Dimension**: 512 dimensions
- **Vector Normalization**: L2 unit sphere
- **Status**: `APPROVED` (Restricted to Unit/Integration Testing & CI)
- **Intended Use**: Fast, deterministic test runs without GPU or heavy PyTorch weight downloads.

---

## 4. Architectural Boundaries
1. **Visual Similarity Only**: An embedding represents visual appearance, silhouette, color distribution, and pattern structure. It does **not** assert sizing, fabric percentages, interchangeability, or brand authenticity.
2. **Dynamic Permission Check**: Prior to invoking any embedding model on a catalog image, the system dynamically verifies `IMAGE_AI_PROCESS` permission for the parent merchant/source.
3. **Immutability of Checkpoints**: Model weights and preprocessing transforms are versioned and immutable. Any change in architecture or weights requires a new model identifier and Alembic migration.
