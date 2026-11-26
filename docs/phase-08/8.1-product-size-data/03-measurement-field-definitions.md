# 03 — Measurement Field Definitions

## 1. Measurement Taxonomy

FashXStudio standardizes garment measurement field codes. Each field represents a single linear dimension with an explicit anatomical or garment definition, allowed garment categories, and strict physical plausibility bounds.

## 2. Controlled Field Registry

| Field Code | Display Name | Allowed Categories | Min (cm) | Max (cm) | Anatomical / Garment Definition |
|---|---|---|---|---|---|
| `CHEST` | Chest | TOPS, DRESSES, OUTERWEAR, GENERAL | 40.0 | 200.0 | Full circumference around the broadest part of chest/torso |
| `BUST` | Bust | TOPS, DRESSES, OUTERWEAR | 40.0 | 200.0 | Full circumference across apex of bust |
| `WAIST` | Waist | TOPS, BOTTOMS, DRESSES, GENERAL | 30.0 | 180.0 | Circumference at the natural waistline or waistband |
| `HIP` | Hip | BOTTOMS, DRESSES, SKIRTS, GENERAL | 40.0 | 220.0 | Circumference at the widest part of the hips / buttocks |
| `LENGTH` | Garment Length | ALL | 15.0 | 250.0 | Total vertical length from high point shoulder to hem |
| `SHOULDER` | Shoulder Width | TOPS, DRESSES, OUTERWEAR | 20.0 | 80.0 | Straight horizontal distance between shoulder seam points |
| `SLEEVE_LENGTH` | Sleeve Length | TOPS, DRESSES, OUTERWEAR | 10.0 | 110.0 | From shoulder seam down outer arm to sleeve cuff edge |
| `INSEAM` | Inseam | BOTTOMS | 20.0 | 120.0 | Distance along inner leg seam from crotch to bottom hem |
| `OUTSEAM` | Outseam | BOTTOMS | 30.0 | 160.0 | Distance along outer leg seam from waistband to hem |
| `THIGH` | Thigh | BOTTOMS | 20.0 | 120.0 | Circumference around the fullest part of the upper leg |
| `RISE` | Rise | BOTTOMS | 15.0 | 60.0 | Distance from crotch seam to top of waistband |
| `NECK` | Neck / Collar | SHIRTS, TOPS | 25.0 | 65.0 | Circumference around collar band or base of neck |

## 3. Category Eligibility Rules
- Measurements must match the product's taxonomy category.
- Submitting `INSEAM` for a Top, or `CHEST` for Trousers without waist/hip context, produces validation warnings or rejections during ingestion.
