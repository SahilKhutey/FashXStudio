# Dataset Labeling & Annotation Guide

## 1. Ethical & Objective Labeling Principles

1. **No Sensitive Inferences**: Never guess or record religion, caste, sexual orientation, precise weight, or medical conditions.
2. **Participant Self-Description**: Where demographic descriptors (such as skin tone or height band) are recorded, they must be participant-selected during consented intake.
3. **Objective Photographic Descriptions**: Focus on camera mechanics, geometry, and lighting rather than subjective impressions of attractiveness or body shape.

---

## 2. Standard Taxonomy & Permitted Values

### 2.1 Lighting Labels
- `NATURAL_BRIGHT`: Clear daylight, minimal shadow.
- `INDOOR`: Standard ambient residential or studio illumination.
- `LOW_LIGHT`: Under-illuminated, high ISO grain, or dark indoor conditions.
- `MIXED`: Multiple conflicting color temperatures or strong backlighting.

### 2.2 Camera Framing
- `FULL_BODY`: Entire figure visible from head to shoes.
- `THREE_QUARTER`: Head to mid-thigh.
- `WAIST_UP`: Head to waist. Valid only for tops, shirts, and short kurtas.

### 2.3 Pose Orientations
- `FRONT_RELAXED`: Standard standing facing camera, arms by side.
- `SLIGHT_ROTATION_LEFT`: Torso rotated 10°–20° left.
- `SLIGHT_ROTATION_RIGHT`: Torso rotated 10°–20° right.
- `ARMS_BENT`: Hands on hips or forearms raised.
- `ARMS_SEPARATED`: Arms held away from torso to expose side seams.
- `NO_PERSON_DETECTED`: Negative test image containing no human figure.
