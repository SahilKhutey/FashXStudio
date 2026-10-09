import io

from PIL import Image

from fashx.core.errors import ValidationError

ALLOWED_FORMATS = frozenset({"JPEG", "JPG", "PNG", "WEBP"})
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_DIMENSION = 4096
MIN_DIMENSION = 100


def sanitize_photo(
    photo_bytes: bytes,
    max_bytes: int = MAX_UPLOAD_BYTES,
    max_dimension: int = MAX_DIMENSION,
    min_dimension: int = MIN_DIMENSION,
) -> bytes:
    """Sanitize and strip metadata/EXIF/GPS from user-uploaded photos.

    Enforces size caps, dimension bounds, and allowed image formats.
    """
    if len(photo_bytes) > max_bytes:
        max_mb = max_bytes // (1024 * 1024)
        raise ValidationError(
            f"Photo payload exceeds maximum permitted size of {max_mb}MB",
            field="photo_b64",
        )

    try:
        # Initial verify check
        with Image.open(io.BytesIO(photo_bytes)) as img:
            img.verify()
    except Exception:
        raise ValidationError(
            "Corrupted or invalid image payload",
            field="photo_b64",
        ) from None

    # Re-open after verify (PIL closes stream on verify)
    try:
        with Image.open(io.BytesIO(photo_bytes)) as img:
            fmt = (img.format or "").upper()
            if fmt not in ALLOWED_FORMATS:
                raise ValidationError(
                    f"Unsupported image format '{fmt}'. Permitted formats: JPEG, PNG, WEBP",
                    field="photo_b64",
                )

            width, height = img.size
            if width > max_dimension or height > max_dimension:
                raise ValidationError(
                    f"Image dimensions ({width}x{height}) exceed maximum allowed {max_dimension}x{max_dimension}",
                    field="photo_b64",
                )
            if width < min_dimension or height < min_dimension:
                raise ValidationError(
                    f"Image dimensions ({width}x{height}) below minimum required {min_dimension}x{min_dimension}",
                    field="photo_b64",
                )

            # Recreate clean image to strip EXIF, GPS, and custom chunks
            clean_mode = "RGB" if img.mode not in ("RGB", "RGBA") else img.mode
            if fmt in ("JPEG", "JPG") and clean_mode == "RGBA":
                clean_mode = "RGB"

            clean_img = Image.new(clean_mode, img.size)
            if clean_mode == "RGB" and img.mode == "RGBA":
                clean_img.paste(img, mask=img.split()[-1])
            else:
                clean_img.paste(img)

            out = io.BytesIO()
            save_format = "JPEG" if fmt in ("JPEG", "JPG") else fmt
            clean_img.save(out, format=save_format, quality=95)
            return out.getvalue()
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(
            f"Failed to process image payload: {e}",
            field="photo_b64",
        ) from e
