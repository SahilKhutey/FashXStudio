"""Image preparation for external ML and try-on providers."""

from io import BytesIO

from PIL import Image


def prepare_for_provider(jpeg: bytes, *, max_side: int = 1536) -> bytes:
    """Resize image to reasonable maximum dimensions and re-encode to RGB JPEG."""
    with Image.open(BytesIO(jpeg)) as im:
        im = im.convert("RGB")
        max_dim = max(im.size)
        scale = max_side / max_dim if max_dim > 0 else 1.0
        if scale < 1.0:
            im = im.resize(
                (round(im.width * scale), round(im.height * scale)),
                Image.Resampling.LANCZOS,
            )
        out = BytesIO()
        im.save(out, "JPEG", quality=92)
        return out.getvalue()
