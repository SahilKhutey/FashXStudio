# Phase 06.1 — Missing-Value Policy and Data Governance

## 1. Missing-Value States

To prevent misleading search results, empty strings and nulls must not be used interchangeably. FashXStudio defines strict missing-value states:

| State | Semantic Meaning | Example |
| :--- | :--- | :--- |
| `KNOWN` | Attribute is verified and present | Fabric is 100% cotton |
| `UNKNOWN` | Relevant attribute is unknown or undetermined | Sleeve length not specified in feed |
| `NOT_PROVIDED` | Merchant source feed omitted the attribute | No fabric field in CSV feed |
| `NOT_APPLICABLE` | Attribute does not apply to this category | Neckline on a handbag or sneakers |
| `NOT_DETECTED` | Vision/NLP model failed to extract a value | Visual model could not identify pattern |
| `CONFLICTING` | Multiple sources or pipelines disagree | Merchant says black; Vision model says navy |
| `PENDING_REVIEW` | Attribute requires human or manual verification | Uncertain textile technique |
| `OTHER` | Known value outside current taxonomy dictionary | Regional handloom technique |

## 2. Source Attribution & Provenance

Every attribute value tracks:
- `source`:
  - `MERCHANT`: Merchant-provided catalog metadata.
  - `SOURCE_FEED`: Standardized partner product feed.
  - `RULE_BASED`: Deterministic rule extraction (e.g. title parsing).
  - `AI_IMAGE`: Multimodal vision classification.
  - `AI_TEXT`: LLM text extraction from long description.
  - `HUMAN_REVIEW`: Founder/admin verified ground truth.
  - `USER_FEEDBACK`: Shopper correction or fit feedback.
- `source_reference`: Raw field name, SKU, or prompt ID.
- `confidence`: Confidence score (`0.0` to `1.0`).
- `review_status`: `UNREVIEWED`, `APPROVED`, or `OVERRIDDEN`.

## 3. Conflict Resolution Priority

When multiple pipelines provide conflicting attribute values:

1. **HUMAN_REVIEW** (Verified founder/specialist audit)
2. **MERCHANT** (Authorized merchant structured specification)
3. **SOURCE_FEED** (Partner connector structured field)
4. **RULE_BASED** (Deterministic regex/dictionary parsing)
5. **AI_IMAGE** (Multimodal computer vision prediction)
6. **AI_TEXT** (NLP inferred attribute)
7. **UNKNOWN** / **PENDING_REVIEW**
