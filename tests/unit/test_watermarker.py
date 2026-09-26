import io

from PIL import Image

from api.app.tryon.watermarker import SyntheticWatermarker


def test_watermarker_embeds_metadata_and_provenance() -> None:
    # 1. Create a dummy test image (512x512 RGB)
    img = Image.new("RGB", (512, 512), (120, 140, 180))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    original_bytes = buf.getvalue()

    # 2. Apply watermark
    job_id = "test-job-9988"
    model_version = "vto-v1-mock"
    watermarked_bytes = SyntheticWatermarker.apply_watermark(
        image_bytes=original_bytes,
        job_id=job_id,
        model_version=model_version,
        add_visible_mark=True,
    )

    # 3. Verify Decoded Image
    with Image.open(io.BytesIO(watermarked_bytes)) as decoded:
        assert decoded.format == "PNG"
        assert decoded.size == (512, 512)

        # Verify C2PA / Synthetic provenance metadata tags
        info = decoded.info
        assert info.get("Origin") == "FashXStudio"
        assert info.get("IsSynthetic") == "True"
        assert info.get("Provenance") == "C2PA-Compatible-Synthetic"
        assert info.get("JobId") == job_id
        assert info.get("ModelVersion") == model_version
        assert "GeneratedAt" in info
