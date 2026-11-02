# VTO Benchmark Dataset Manifest

> **Notice:** This manifest references anonymized sample identifiers and canonical garment metadata for evaluation. In compliance with Rule 7, no real user body photos, face crops, external credentials, or private signed storage URLs are recorded in this manifest.

## 1. Overview

This benchmark dataset defines standardized test fixtures for assessing VTO model generation realism across garment categories, body orientations, and pattern complexities.

## 2. Sample Manifest Structure

| Sample ID | Garment Category | Pattern / Style | Pose / Orientation | Complexity Tier | Target Evaluation Focus |
|---|---|---|---|---|---|
| `BM-VTO-001` | Tops (T-Shirt) | Solid Crewneck | Frontal Standing | Standard | Torso silhouette alignment & edge sharpness |
| `BM-VTO-002` | Tops (Shirt) | Vertical Striped Button-down | Slight 3/4 Turn | Medium | Stripe continuity & placket alignment |
| `BM-VTO-003` | Tops (Hoodie) | Heavy Fleece Oversized | Frontal Arms Relaxed | High | Garment drape bulk & shoulder drop realism |
| `BM-VTO-004` | Bottoms (Jeans) | Straight Fit Denim | Frontal Standing | Standard | Waistband alignment & crotch drape |
| `BM-VTO-005` | Bottoms (Trousers)| Pleated Formal | Walking Pose | Medium | Crease preservation & leg flare |
| `BM-VTO-006` | Dresses (Midi) | Floral Print Wrap Dress | Frontal Standing | High | Pattern distortion & waist tie placement |
| `BM-VTO-007` | Outerwear (Jacket) | Leather Biker with Hardware | Frontal Asymmetrical | High | Metal zipper texture & collar folding |
| `BM-VTO-008` | Tops (Sleeveless) | Athletic Tank Top | Frontal Hands on Hips | High | Armhole occlusion & shoulder seam placement |
| `BM-VTO-009` | Knitwear (Sweater)| Cable Knit Texture | Frontal Standing | High | Knit relief texture & cuff elasticity |
| `BM-VTO-010` | Tops (Polo) | Piqué Knit with Collar | Frontal Standing | Medium | Collar structure preservation & neck boundary |

## 3. Evaluation Dimensions

Human raters evaluate generated results for each sample against five discrete fidelity criteria:
1. **Garment Preservation**: Does the garment in the try-on image retain its original design, sleeves, pattern, and color?
2. **Person Identity Preservation**: Does the person's face, neck, exposed limbs, and background remain unaltered?
3. **Boundary Alignment**: Are garment boundaries cleanly aligned without blur, halo artifacts, or pixel tearing?
4. **Occlusion Handling**: Do crossed arms, hands in pockets, or hanging hair correctly occlude the garment?
5. **Drape Realism**: Does the fabric fold naturally according to the user's posture and garment weight?
