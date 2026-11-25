# Phase 07 Evaluation Dataset Acceptance

## 1. Dataset Governance & Consent Principles

The Phase 07 VTO Quality Evaluation Dataset (`vto-eval-v1.0.0`) provides a permissioned, controlled test collection to evaluate provider generation quality across diverse garment categories and body profiles.

### Governance Rules
1. **Explicit Model Consent**: Every human photograph in the dataset is covered by a signed model release explicitly granting permission for AI image processing and quality benchmarking.
2. **Authorized Garment Assets**: All garment product images are licensed from cooperating merchants or created from internal studio photography with full intellectual property clearance.
3. **Restricted Storage**: Evaluation assets reside in a dedicated, access-restricted AWS S3 bucket (`s3://fashx-eval-dataset/`) segregated from customer production buckets.
4. **No Customer Photos in Evaluation Datasets**: Real shopper photos submitted to the consumer app are NEVER added to evaluation or benchmarking datasets.

---

## 2. Dataset Composition & Demographic Balance

The `vto-eval-v1.0.0` manifest specifies balanced coverage:

| Category Dimension | Subcategory / Group | Target Count | Purpose |
| :--- | :--- | :---: | :--- |
| **Garment: Tops** | T-shirts, Casual Shirts, Formal Shirts, Kurtas | 40 | Fit, collar preservation, sleeve drape |
| **Garment: Bottoms** | Trousers, Jeans | 30 | Waistband alignment, inseam drape |
| **Garment: One-Piece** | Western Dresses, Jumpsuits | 30 | Full-body integration, pattern scaling |
| **Garment: Excluded** | Sarees, Lehengas, Shoes, Accessories | 10 | Negative control (Must fail closed) |
| **Demographics: Gender** | Female (50%), Male (50%) | 100 | Balanced representation |
| **Demographics: Skin Tones**| Fitzpatrick Types I–VI | 100 | Contrast and boundary preservation |
| **Body Profiles** | Standard, Plus, Athletic, Petite | 100 | Drape accuracy across diverse builds |

---

## 3. Dataset Manifest Schema

The manifest file `manifest.json` is cryptographically signed and version-controlled (`backend/fashx/tryon/evaluation/dataset.py`):
```json
{
  "dataset_id": "vto-eval-v1.0.0",
  "version": "1.0.0",
  "created_at": "2026-11-20T00:00:00Z",
  "manifest_sha256": "4a71b...8e1",
  "pairs_count": 100,
  "negative_controls_count": 10,
  "pairs": [
    {
      "pair_id": "pair_001_top_casual_male",
      "model_id": "model_m_042",
      "model_photo_uri": "s3://fashx-eval-dataset/models/m_042.jpg",
      "model_gender": "male",
      "model_skin_tone": "IV",
      "garment_id": "garment_shirt_088",
      "garment_photo_uri": "s3://fashx-eval-dataset/garments/shirt_088.png",
      "category": "casual_shirts",
      "expected_outcome": "SUPPORTED"
    }
  ]
}
```

---

## 4. Verification and Acceptance Status

- **Automated Validation**: `tests/unit/tryon/evaluation/test_dataset_and_permissions.py` verifies manifest parsing, cryptographic checksum validation, and permission checks.
- **Acceptance Decision**: Accepted for local and staging benchmark execution.
