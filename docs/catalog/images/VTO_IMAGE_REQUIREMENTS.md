# Virtual Try-On (VTO) Image Requirements

## 1. High-Fidelity Garment Preservation

Virtual Try-On models rely on accurate garment boundary recognition and pattern alignment:

1. **Lossless Format**: VTO derivatives are generated in `PNG` format rather than lossy compression.
2. **Dimension Standard**: Scaled to max dimension 1024 × 1024 px, preserving aspect ratio.
3. **No Aggressive Auto-Cropping**: Sleeves, hemlines, lapels, collars, pockets, and lace trims must never be clipped or modified.
4. **Separation from Display Derivative**: A VTO input is a dedicated technical input for diffusion or segmentation pipelines, never a renamed web card.

---

## 2. Granular Permission Prerequisites

A VTO derivative is generated **strictly** when all four conditions are met:
1. `IMAGE_AI_PROCESS` is granted.
2. `VTO_PROCESS` is granted.
3. `DERIVATIVE_CREATE` is granted.
4. `DERIVATIVE_STORE` is granted.

If any of these rights are withheld, the product metadata and display derivatives may still be ingested, but `VTO_INPUT` is skipped.
