# Dependency Register: Virtual Try-On (VTO) Models & Checkpoints

| Attribute | Specification |
| :--- | :--- |
| **Subsystem** | Virtual Try-On Engine (VTO) |
| **Component** | Diffusion Inpainting & Garment Warping Model Adapters |
| **Owner** | ML / Platform Team |
| **Status** | Phase-0 Gate: Under Evaluation / Research Only |

---

## 1. Candidate Checkpoints & Licensing Audit

> [!WARNING]
> **Commercial Licensing Gate (Rule R11 / Rule I19)**:
> Public checkpoints for research models (such as IDM-VTON and CatVTON) carry **CC BY-NC-SA 4.0** or strict non-commercial restrictions.
> **Research-model evaluation != production commercial authorization.**
> No model may be set as the production default unless full commercial deployment rights are cleared or an enterprise commercial API is integrated.

### 1.1 Model Registry

| Model Checkpoint | Origin / Author | Published License | Commercial Permission | Latency Target | Primary Use Case |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **IDM-VTON** | KAIST & OminiLabs | CC BY-NC-SA 4.0 | **NON-COMMERCIAL (Evaluation Only)** | ~3.5s (A100) | Benchmark Baseline / Research Evaluation |
| **CatVTON** | CatVTON Authors | Non-Commercial | **NON-COMMERCIAL (Evaluation Only)** | ~2.8s (A100) | Lightweight Inpainting Benchmark |
| **OOTDiffusion** | Levihsu / OOTD | Apache 2.0 (Code) / Model Weights restricted | **Restricted / Review Required** | ~4.0s (A100) | Upper / Lower Body Category Inpainting |
| **Commercial VTO Partner API** | Enterprise Vendor (e.g., Fashn.ai / Revery / Custom Trained) | Commercial SaaS SLA | **COMMERCIAL APPROVED** | ~2.5s (API) | **Production Target (V1 Release)** |

---

## 2. Model Adapter Decoupling & Invalidation Contract

The API and worker pipelines must never couple to a specific vendor checkpoint. All models implement the `TryOnModelAdapter` port:

$$\text{TryOnArtifactKey} = \text{SHA256}(\text{photo\_hash} + \text{garment\_version} + \text{model\_version} + \text{pipeline\_version} + \text{render\_config\_hash})$$

If weights are updated or an enterprise commercial model replaces an evaluation checkpoint, the artifact key automatically invalidates stale renders.

---

## 3. Production Fallback Strategy

1. If GPU worker queue latency exceeds 10 seconds: fail gracefully to high-res flat-lay garment lookbook presentation with fit estimation card.
2. If VTO worker encounters terminal parsing failure (e.g. occluded limbs): emit `TryOnJobFailedEventV1` with user-correctable guidance and refund any user generation credits.
