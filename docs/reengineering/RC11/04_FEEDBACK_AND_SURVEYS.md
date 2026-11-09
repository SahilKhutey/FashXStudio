# RC11: Feedback, Surveys and Defect Tagging

## 1. Realism Rating & Defect Taxonomy
Following try-on generation, users are prompted with an optional 1–5 visual realism rating:
- **Rating Scale**: 1 (Unusable) to 5 (Extremely Realistic).
- **Core Realism Questions**:
  1. Did the garment match the selected product?
  2. Did it drape naturally over your body silhouette?
  3. Were facial identity and body proportions preserved?
  4. Were fabric texture and color tones believable?
  5. Would this result assist your purchase decision?

### Defect Tags (Multi-select)
- `face_changed`: Facial identity or features altered.
- `body_shape_distorted`: Body silhouette or proportions rendered inaccurately.
- `garment_identity_altered`: Sleeve length, neckline, or style changed.
- `color_texture_inaccurate`: Fabric gloss, drape, or color tones off.
- `unnatural_occlusion`: Hands or hair overlapping garments incorrectly.
- `garment_misaligned`: Clothed item positioned off-center or floating.
- `offensive_or_inappropriate`: Distorted, offensive, or NSFW artifact (trips hard stop rule).

## 2. Privacy & Trust Survey
Administered following initial photo upload and at Day 7:
- *"I felt comfortable uploading my photo."* (1 = Strongly Disagree to 5 = Strongly Agree)
- *"I clearly understood how my photo would be processed."* (1–5)
- *"I know how to permanently delete my photo."* (1–5)

## 3. Standardized Satisfaction Metrics
- **System Usability Scale (SUS)**: Standard 10-item questionnaire yielding a 0–100 usability score.
- **Sean Ellis PMF Question**: *"How would you feel if you could no longer use FashXStudio?"*
  - Very Disappointed / Somewhat Disappointed / Not Disappointed.
- **Net Promoter Score (NPS)**: *"How likely are you to recommend FashX to a friend?"* (0–10 scale).
