# Human Visual Quality Rubric & Scoring Criteria

## 1. Six Evaluation Dimensions

Every generated try-on render is assessed by independent reviewers across six dimensions using a 5-point Likert scale (1 = Poor, 5 = Excellent):

### 1. Garment Preservation (Weight: 25%)
- **Criteria**: Faithfulness of primary colors, secondary tones, printed logos, graphics, embroidery, collar cut, and sleeve styling compared to the reference product photo.
- **Score 1**: Major garment identity changed (wrong color, omitted pattern, altered cut).
- **Score 3**: Partially preserved; noticeable pattern or color shifts.
- **Score 5**: Highly faithful; imperceptible variance from reference item.

### 2. Body Alignment (Weight: 20%)
- **Criteria**: Anatomical alignment with shoulders, neck, waist, hips, and limbs. Symmetric draping along the shopper's true posture.
- **Score 1**: Severe misalignment (collar detached from neck, garment floating).
- **Score 3**: Acceptable alignment with visible boundary artifacts.
- **Score 5**: Perfectly aligned and naturally contoured to the body pose.

### 3. Artifact Quality (Weight: 15%)
- **Criteria**: Absence of blurriness, pixelation, floating buttons, severed sleeves, or distorted fingers/hands.
- **Score 1**: Unusable; severe visual hallucinations.
- **Score 3**: Noticeable but minor artifacts outside focal regions.
- **Score 5**: Crisp, clean image without discernible generation flaws.

### 4. Identity Preservation (Weight: 15%)
- **Criteria**: Maintenance of the shopper's authentic facial identity, hairstyle, skin complexion, and physical build.
- **Score 1**: Shopper identity replaced or unrecognizable.
- **Score 3**: Recognizable, but with slight facial or skin tone alterations.
- **Score 5**: Shopper identity and facial features flawlessly preserved.

### 5. Visual Plausibility (Weight: 15%)
- **Criteria**: Consistency of ambient lighting, shadows, fabric texture, and realistic interaction with the environment.
- **Score 1**: Cartoonish or synthetic appearance.
- **Score 3**: Plausible at first glance; minor lighting mismatches.
- **Score 5**: Indistinguishable from an authentic studio or real-life photograph.

### 6. Non-Misleading Representation (Weight: 10%)
- **Criteria**: Does the render avoid giving a deceptive impression of garment size, stretch, length, or fit?
- **Score 1**: Extremely misleading (e.g. ankle-length dress rendered above knees).
- **Score 3**: Minor ambiguity in fit.
- **Score 5**: Honest, non-deceptive representation of the apparel item.
