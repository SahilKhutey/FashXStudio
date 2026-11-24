# Automated Objective Image Metrics

## 1. Automated Metrics Role & Limits

Automated computer vision metrics accelerate regression detection between continuous model checkpoints. 

**Important Principle**:
**Automated metrics cannot substitute for human visual judgment.** A pure pixel difference comparison between the shopper photo and the try-on output is meaningless because the clothing region is intentionally changed.

---

## 2. Implemented Measurements

### 2.1 Structural Similarity Index (SSIM)
- Computed specifically on aligned garment patches:
  $$\text{SSIM}(x, y) = \frac{(2\mu_x\mu_y + c_1)(2\sigma_{xy} + c_2)}{(\mu_x^2 + \mu_y^2 + c_1)(\sigma_x^2 + \sigma_y^2 + c_2)}$$
- Evaluates texture, edge structure, and pattern continuity.

### 2.2 CIEDE2000 Color Difference ($\Delta E_{00}$)
- Evaluates color shifts in standardized $L^*a^*b^*$ color space.
- Detects whether lighting adjustments during inference inadvertently shifted the garment's dyed color (e.g. navy blue shifting to black).
- In standard NumPy execution environments, Euclidean RGB color delta is computed as a robust fallback.
