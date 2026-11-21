# Fashion Image Preprocessing Specification

## 1. Overview
The preprocessing pipeline transforms raw merchant imagery into standardized, color-accurate, aspect-ratio preserved tensors suitable for input to fashion vision models.

---

## 2. Preprocessing Steps

### 2.1 File Format & Dimension Bounds
- **Supported Encodings**: JPEG, PNG, WebP.
- **Minimum Dimensions**: $100 \times 100$ pixels.
- **Maximum Dimensions**: $4096 \times 4096$ pixels.
- **Aspect Ratio Limit**: Max $4:1$ (extreme panos rejected).
- Images outside these bounds fail with `PreprocessingError`.

### 2.2 EXIF Orientation Normalization
Many catalog images contain EXIF orientation metadata specifying rotations (e.g. 90-degree camera rotation).
- The preprocessor evaluates EXIF orientation tag `0x0112`.
- `ImageOps.exif_transpose` is applied to un-rotate the image raster.
- EXIF metadata is stripped from downstream buffers to protect privacy.

### 2.3 Color Space Normalization
- CMYK, Grayscale, and RGBA images are converted to 3-channel 8-bit sRGB.
- Transparent RGBA channels are blended over a neutral white background (`#FFFFFF`) to prevent black artifact fringing around garments.

### 2.4 Aspect-Ratio Preserving Resize with Padding
- Fashion garments (especially sarees, kurtas, maxis, and boots) have high aspect ratios (e.g. $1:2$ or $3:4$). Direct non-square stretching distorts silhouettes and necklines.
- The preprocessor computes the uniform scaling factor:
  $$s = \min\left(\frac{T_{\text{width}}}{W}, \frac{T_{\text{height}}}{H}\right)$$
- The image is scaled using high-quality Bicubic interpolation (`Image.Resampling.BICUBIC`).
- The scaled image is centered on a square canvas of target dimension ($224 \times 224$ px by default) with uniform neutral padding (`#FFFFFF`).

### 2.5 Tensor Normalization
For models consuming normalized tensors:
- Pixel values are cast to float32 in $[0.0, 1.0]$.
- Standard ImageNet / CLIP mean and standard deviation normalization is applied:
  - $\mu = [0.48145466, 0.4578275, 0.40821073]$
  - $\sigma = [0.26862954, 0.26130258, 0.27577711]$
