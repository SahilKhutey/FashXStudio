# Phase 07 Known Limitations & Product Boundaries

## 1. Supported vs. Unsupported Categories

Virtual try-on capabilities are strictly bounded by category-level quality evaluation:

### 1.1 Supported Categories (Approved for Production)
- **Casual Shirts & Polos**: Clean collar, button, and sleeve rendering.
- **T-Shirts**: High fidelity on standard graphic, crewneck, and v-neck cuts.
- **Formal Shirts**: High fidelity on structured dress shirts.
- **Kurtas (Straight-cut Men's and Women's)**: Preserves hemline and neckline contours.
- **Trousers & Chinos**: Accurate waistband and standard straight/slim leg hang.
- **Denim Jeans**: Preserves denim texture and standard wash gradients.
- **Western Single-Piece Dresses**: Approved for simple A-line and sheath dresses without intricate draping.

### 1.2 Unsupported Categories (Blocked at Validation Gate)
- **Sarees (Draped Ethnic Wear)**: Unpredictable pallu pleating, inconsistent tucking, and high artifact rates (78% defect rate).
- **Lehengas (Multi-Layered Ethnic Ensembles)**: Multi-piece dupatta and flair construction cannot be synthesized accurately from a single 2D image.
- **Footwear & Shoes**: High occlusion, perspective distortion, and ground-plane alignment failures.
- **Jewelry, Watches & Small Accessories**: Resolution degradation and severe warping.
- **Structured Outerwear (Heavy Coats, Blazers)**: Internal shoulder padding and heavy tailoring structure are difficult to synthesize over loose civilian clothing.

---

## 2. Product and Technology Limitations

### 2.1 Visual Simulation vs. Physical Fit
- **Core Limitation**: The virtual try-on subsystem produces a **2D visual simulation**, not a physical fit prediction.
- It does **not** verify whether the shopper selected the correct numerical size.
- It does **not** simulate true fabric stretch, tensile pull, breathability, or garment comfort.
- FashXStudio strictly requires shoppers to consult merchant size charts for sizing decisions.

### 2.2 Input Photo Constraints
- **Pose Requirements**: Shoppers must be standing upright facing the camera with arms slightly away from the body. Seated poses, lying down, or extreme athletic postures are rejected or cause severe warping.
- **Occlusion**: Crossed arms, heavy coats, scarves, or bags covering the torso result in synthetic hallucination or partial garment omission.
- **Lighting & Contrast**: Extreme backlighting or severe shadows degrade skin boundary segmentation.

### 2.3 Single-Garment Try-On Constraint
- Inference processes one target garment per job. Layering multiple items simultaneously (e.g. attempting to try on a t-shirt, blazer, and jeans in a single generation step) is not currently supported.
