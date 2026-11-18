# Image Quality Policy

## 1. Quality Profile Definitions

Image quality is evaluated across distinct consumer display and virtual try-on profiles:

### Display Quality Profile
- Minimum dimensions: 400 × 400 px
- Aspect ratio bounds: 0.25 to 3.5
- Background: Clean, uncorrupted
- Outcomes:
  - `PASS`: Suitable for browsing, cards, and detail views.
  - `REVIEW`: Non-standard aspect ratio or resolution; human curation review flagged.
  - `REJECT`: Corrupted, unreadable, or undersized.

### Virtual Try-On (VTO) Profile
- Minimum dimensions: 768 × 768 px recommended
- Aspect ratio bounds: 0.6 to 2.5 (portrait orientation preferred)
- Garment preservation: Neckline, collar, sleeves, hems, and patterns must remain intact without clipping.
- Outcomes:
  - `PASS`: Suitable for AI segmentation and virtual try-on inference.
  - `REVIEW`: Aspect ratio or resolution below recommended threshold.
  - `NOT_APPLICABLE`: VTO or AI processing permissions not granted by merchant.
  - `REJECT`: Unsuitable for try-on pipelines.
