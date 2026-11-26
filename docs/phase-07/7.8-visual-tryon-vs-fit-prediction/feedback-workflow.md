# Shopper Feedback & Issue Reporting Workflow

> **Reporting mechanisms, triage, root-cause categorization, and resolution.**

## 1. Reporting Flow
Shoppers can report try-on inaccuracies directly from completed results via `POST /api/v1/tryon/jobs/{job_id}/feedback`.

## 2. Standardized Reason Codes
- `GARMENT_LOOKS_DIFFERENT`: Generated garment does not resemble selected product.
- `COLOUR_OR_PATTERN_CHANGED`: Colour, print or pattern is incorrect.
- `GARMENT_LENGTH_OR_SHAPE`: Garment dimensions or silhouette appear distorted.
- `BODY_ALIGNMENT_ISSUE`: Garment is placed incorrectly on the body.
- `FACE_OR_BODY_CHANGED`: Identity or body appearance changed unexpectedly.
- `MISLEADING_FIT_IMPRESSION`: Output suggests an unsupported fit result.
- `LAYERING_ERROR`: Layered garment or component is incorrect.
- `IMAGE_ARTIFACT`: Visible generation artifact.
- `OTHER`: Other issue with text details.

## 3. Investigation & Resolution States
Reports progress through an audit trail:
`RECEIVED` $\rightarrow$ `TRIAGE` $\rightarrow$ `CONFIRMED` / `NOT_CONFIRMED` $\rightarrow$ `CLOSED` (or `ESCALATED`).

## 4. Root Cause Categories
- `INPUT_QUALITY`
- `GARMENT_ASSET_QUALITY`
- `GARMENT_PRESERVATION`
- `BODY_ALIGNMENT`
- `IDENTITY_PRESERVATION`
- `LAYERING`
- `CATEGORY_MISMATCH`
- `PROVIDER_FAILURE`
- `PRODUCT_DATA_ISSUE`
- `PRESENTATION_MISLEADING`
- `UNDETERMINED`
