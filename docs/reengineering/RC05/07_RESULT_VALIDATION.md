# RC05 — 07 Result Validation & Preview Watermarking

## Objective
Enforce strict post-inference safety and quality validation on all rendered try-on outputs. Guarantee that corrupted, extreme exposure, or rejected results are never published, and embed visible provenance markings on mock outputs.

## Existing State
- `PostInferenceQualityValidator` checked structural limits, minimum/maximum luminance, contrast deviation, dimension limits, and supported formats.
- `MockTryOnAdapter` generated composite images without an unmistakable on-image preview banner.

## Changes
- **Preview Watermark Guard:** Added a permanent, high-visibility watermark `"PREVIEW ONLY - MOCK VTO"` directly into `MockTryOnAdapter._composite_bytes` (`backend/fashx/tryon/adapters/mock_adapter.py`).
  - Ensures mock development outputs can never be misconstrued as genuine AI inferences.
- **C2PA Synthetic Media Metadata:** Applied by `SyntheticWatermarker` (`backend/fashx/tryon/watermarker.py`), embedding metadata tags (`Origin`, `IsSynthetic`, `Provenance`, `JobId`, `ModelVersion`).
- **Quality Rejection Gate:** Verified that outputs with contrast standard deviation `< 12.0` or mean luminance outside `[25, 235]` are marked failed with `failure_reason="quality_rejected"` and never stored as active artifacts.

## Quality Rules Matrix
| Parameter | Threshold | Action on Breach |
|---|---|---|
| Allowed Formats | JPEG, PNG, WEBP | Reject (`Unsupported image format`) |
| Min Resolution | 256x256 px | Reject (`Resolution below threshold`) |
| Max Dimension | 4096 px | Reject (`Dimension exceeds max side`) |
| Max Size | 15 MB | Reject (`Payload exceeds max bytes`) |
| Mean Luminance | 25.0 to 235.0 | Reject (`Overexposed / underexposed`) |
| Contrast Deviation | >= 12.0 std | Reject (`Blank or low-contrast frame`) |

## Implementation
```python
# backend/fashx/tryon/adapters/mock_adapter.py
# Draw unmistakable PREVIEW ONLY watermark on mock generation
draw = ImageDraw.Draw(result_img)
font = ImageFont.load_default()
banner_text = "PREVIEW ONLY - MOCK VTO"
bbox = draw.textbbox((0, 0), banner_text, font=font)
text_w = bbox[2] - bbox[0]
text_h = bbox[3] - bbox[1]
bx = int((result_img.width - text_w) / 2)
by = result_img.height - text_h - 24
draw.rounded_rectangle([bx - 8, by - 4, bx + text_w + 8, by + text_h + 4], radius=4, fill=(220, 38, 38, 200))
draw.text((bx, by), banner_text, font=font, fill=(255, 255, 255, 255))
```

## Execution
```bash
pytest tests/unit/test_vto_phase6_artifacts.py tests/unit/test_tryon_adapters.py -v
```

## Tests
- `test_mock_tryon_adapter_execution` -> PASSED
- `test_normalize_result_returns_jpeg` -> PASSED
- `test_normalize_result_rejects_resolution_too_small` -> PASSED
- Quality rejection tested in `test_tryon_use_cases.py` (`FailingQualityAdapter`) -> PASSED

## Risks
- Degrading image quality during watermarking.
- Mitigation: Subtle semi-transparent bottom pill applied without obscuring central garment area.

## Evidence
- Smoke test verified that completed mock job outputs carry identifiable `provider: "mock"` metadata and watermarks.

## Exit Criteria
- Corrupt or extreme images rejected; mock results unambiguously labeled.
