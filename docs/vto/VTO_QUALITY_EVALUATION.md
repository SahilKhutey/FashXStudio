# FashXStudio — Virtual Try-On Visual Quality Rubric & Human Evaluation Protocol

**Document ID:** `FASHX-VTO-002`  
**Version:** `1.0 — Execution Baseline`  
**Date:** `10 November 2026`  
**Scope:** `Phase 01.4 — AI Quality Benchmarking & Human Review Protocol`  

---

## 1. Quality Evaluation Philosophy

Automated image metrics (e.g., PSNR, SSIM, or LPIPS) cannot determine whether a fashion try-on image appears convincing, flattering, and faithful to a paying shopper. Visual quality must be evaluated through **structured human review** across two independent axes:
1. **Visual Realism:** Does the image look like a genuine photograph rather than a warped AI hallucination?
2. **Garment Preservation:** Does the rendered garment accurately match the physical product the shopper intends to purchase?

---

## 2. Visual Realism Scoring Rubric (1.0 – 5.0)

Reviewers ask: *"How realistic does the generated try-on look compared with an actual photograph of this person?"*

| Score | Rating Level | Qualitative Criteria & Visual Defects |
| :--- | :--- | :--- |
| **5.0** | **Highly Realistic** | Flawless boundary blending; completely natural fabric folds and shadows; zero blur or warping around head, neck, hands, or waistline. |
| **4.0** | **Realistic (Minor Flaws)**| Photorealistic appearance at normal phone viewing distance; minor edge softening at collar or wrist that does not distract from overall impression. |
| **3.0** | **Acceptable (Noticeable)** | Recognizable photo, but with noticeable diffusion artifacts (e.g. slight skin tone boundary mismatch, faint halo around shoulders, or slightly stiff drape). |
| **2.0** | **Mostly Unrealistic** | Obvious visual errors; unnatural warping of torso or arms; skin tone distortion; blurred hands; garment appears pasted on. |
| **1.0** | **Very Unrealistic** | Fatal generation failure; mutilated limbs; detached head; major hallucinated patterns; severe blur across the entire frame. |

*Target Benchmark:* Average score $\ge 3.8 / 5.0$; at least $70\%$ of reviewed outputs rated $\ge 4.0$.

---

## 3. Garment Preservation Rubric (1.0 – 5.0)

Reviewers ask: *"How faithful is the synthesized garment to the merchant's authoritative product photography?"*

| Score | Rating Level | Fidelity Criteria Across 8 Product Dimensions |
| :--- | :--- | :--- |
| **5.0** | **Highly Faithful** | Exact color tone; complete preservation of prints, embroidery, and buttons; collar and sleeve cut identical to source; correct fabric drape. |
| **4.0** | **Mostly Faithful** | Primary color, cut, and print accurate; minor softening of small text/logos or micro-textures that does not alter product perception. |
| **3.0** | **Moderately Faithful**| Basic silhouette and color match, but noticeable alterations to collar shape, sleeve length, or print scale. |
| **2.0** | **Poor Fidelity** | Significant color shift (e.g. navy rendered as royal blue); major distortion of block print or graphic; altered garment length (shirt turned into tunic). |
| **1.0** | **Unacceptable** | Garment is fundamentally altered or replaced with a generic clothing item of different style, color, or silhouette. |

### Eight-Point Inspection Checklist (Per Garment)
Reviewers mark Pass / Fail on each element:
1. **Hue & Saturation:** Color matches merchant studio photo under daylight standard.
2. **Pattern Scale:** Block print, stripes, or florals maintain proportional scale across the torso.
3. **Collar & Neckline:** Mandarin, crewneck, polo, or V-neck structure preserved.
4. **Sleeve Fit & Length:** Full, half, or sleeveless cut accurately positioned at shoulders and cuffs.
5. **Silhouette & Fit:** Slim, regular, or relaxed drape aligns with brand description.
6. **Hemline & Length:** Garment terminates at correct waist or hip level.
7. **Distinctive Details:** Pockets, plackets, buttons, and brand emblems preserved.
8. **Fabric Texture:** Denim, linen weave, or knit cotton texture visually evident.

---

## 4. Human Evaluation Protocol for Pilot

### Reviewer Panel Composition
- Minimum of 2 independent reviewers evaluate each sample image.
- Reviewers are blinded to the specific model version or prompt parameters used.
- Where scores diverge by $\ge 2.0$ points, a senior reviewer conducts an adjudication review.

### Representative Indian Diversity Test Suite (Target: 50 Samples)
The evaluation set must include:
- **Skin Tones:** Varied across the Fitzpatrick / Monk Skin Tone scale (Fair, Wheatish, Dusky, Deep).
- **Body Proportions:** Diverse height and body mass profiles across men and women.
- **Garment Mix:** 20 Men's shirts/T-shirts, 15 Women's tops, 15 Men's & Women's kurtas.
- **Lighting Conditions:** 35 optimal studio/indoor lighting samples; 15 sub-optimal ambient mobile photo samples.
