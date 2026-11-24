# VTO Quality Limitations, Misleading Output & Fit Risks

## 1. Technical & Real-World Limitations

Virtual Try-On is an illustrative, synthetic rendering technology. FashXStudio explicitly acknowledges several structural limitations:

1. **No Physical Tailoring Guarantee**: A photograph alone does not contain 3D body measurements. The visual render must never be marketed as proof that a garment will fit the customer in real life.
2. **Fabric Drape & Stretch**: Stiff cottons, flowing silks, and elastane blends drape differently on actual bodies than 2D neural diffusion models simulate.
3. **Lighting & Texture Discontinuities**: Subtle textures (e.g. fine silk weaves or tonal embroidery) may be smoothed out during diffusion downsampling.
4. **Complex Ethnic Garments**: Sarees, lehengas, and layered dupattas have multiple independent components and loose fabric flows that single-garment VTO architectures struggle to resolve accurately.

---

## 2. Customer Risk Mitigation

To prevent misleading shopper impressions:
- Every VTO render displayed in the mobile client is watermarked with: **"Illustrative AI simulation — not a guarantee of physical fit or garment measurements."**
- Categories exhibiting higher distortion rates are blocked from production eligibility.
