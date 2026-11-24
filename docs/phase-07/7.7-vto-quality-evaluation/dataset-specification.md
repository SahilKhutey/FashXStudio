# Evaluation Dataset Specification & Diversity Coverage

## 1. Benchmark Composition & Sampling Plan

The evaluation dataset represents the demographic, environmental, and garment variations expected across the Indian apparel commerce market.

### Staged Collection Targets:
| Stage | Consenting Participants | Authorized Garments | Evaluated Pairs | Objective |
|---|---|---|---|---|
| **Pilot Benchmark** | 20–30 | 40–60 | 50–80 | Validate runner, scoring, and rubrics. |
| **Initial Benchmark** | 50–75 | 100–150 | 180–300 | Compare provider configs & baseline categories. |
| **Category Benchmark** | 100–150 | 200–300 | 300–500 | Formally gate individual garment categories. |

---

## 2. Diversity Dimensions

### 2.1 Demographic Diversity
- **Height Bands**: Broad, objective ranges:
  - `< 155 cm`
  - `155–165 cm`
  - `166–175 cm`
  - `> 175 cm`
- **Body Representation**: Multiple proportional builds (slender, average, broad, plus-size) without subjective or stigmatizing labeling.
- **Skin Tone Range**: Consented annotation across Fitzpatrick and Monk Skin Tone scales to ensure model fidelity across fair, medium, olive, and deep complexions.

### 2.2 Environmental & Photographic Diversity
- **Lighting Conditions**: `NATURAL_BRIGHT`, `INDOOR_WARM`, `LOW_LIGHT`, `BACKLIT`, `MIXED`.
- **Camera Distances**: `FULL_BODY` (head to toe), `THREE_QUARTER` (head to mid-thigh), `WAIST_UP` (head to hip).
- **Poses**: `FRONT_RELAXED`, `SLIGHT_ROTATION_LEFT`, `SLIGHT_ROTATION_RIGHT`, `ARMS_BENT`, `ARMS_SEPARATED`.

---

## 3. Dataset Partitioning

To avoid data leakage and over-optimistic evaluation metrics, the dataset is strictly split:
- **`DEVELOPMENT` (50%)**: Used for exploratory engineering, pipeline debugging, and threshold calibration.
- **`VALIDATION` (25%)**: Used for hyperparameter tuning and model configuration selection.
- **`HOLDOUT_TEST` (25%)**: Strictly reserved for final category release gate measurement. Never used for prompt tuning or threshold adjustments.
