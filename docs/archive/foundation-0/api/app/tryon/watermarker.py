import io
from datetime import UTC, datetime

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin


class SyntheticWatermarker:
    """Rule I09: Embeds imperceptible metadata and subtle visual provenance watermark."""

    WATERMARK_TEXT = "FashX AI Preview"

    @classmethod
    def apply_watermark(
        cls,
        image_bytes: bytes,
        job_id: str,
        model_version: str,
        add_visible_mark: bool = True,
    ) -> bytes:
        """Apply invisible provenance metadata and optional subtle visual watermark."""
        with Image.open(io.BytesIO(image_bytes)) as img:
            img = img.convert("RGBA")

            if add_visible_mark:
                # Create a semi-transparent overlay
                overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(overlay)

                # Bottom right watermark placement
                margin = 16
                # Default bitmap font fallback for portability across environments
                font = ImageFont.load_default()
                text = cls.WATERMARK_TEXT

                # Calculate text dimensions
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                x = img.width - text_width - margin - 12
                y = img.height - text_height - margin - 8

                # Background pill for readability
                draw.rounded_rectangle(
                    [x - 6, y - 4, x + text_width + 6, y + text_height + 4],
                    radius=4,
                    fill=(0, 0, 0, 110),
                )
                draw.text((x, y), text, font=font, fill=(255, 255, 255, 200))

                # Composite
                img = Image.alpha_composite(img, overlay)

            # Convert back to RGB
            rgb_img = img.convert("RGB")

            # Embed synthetic media metadata tags (PNG info)
            png_info = PngImagePlugin.PngInfo()
            png_info.add_text("Origin", "FashXStudio")
            png_info.add_text("IsSynthetic", "True")
            png_info.add_text("Provenance", "C2PA-Compatible-Synthetic")
            png_info.add_text("JobId", job_id)
            png_info.add_text("ModelVersion", model_version)
            png_info.add_text("GeneratedAt", datetime.now(UTC).isoformat())

            out_buf = io.BytesIO()
            rgb_img.save(out_buf, format="PNG", pnginfo=png_info)
            return out_buf.getvalue()
