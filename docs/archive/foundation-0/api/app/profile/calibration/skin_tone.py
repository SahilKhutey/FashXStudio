import io
import math
from dataclasses import dataclass

from PIL import Image

# Google Monk Skin Tone (MST) reference palette RGB centroids (Scale 1-10)
MONK_PALETTE: list[tuple[int, str, tuple[int, int, int]]] = [
    (1, "#f6ede4", (246, 237, 228)),
    (2, "#f3e7db", (243, 231, 219)),
    (3, "#f7dad0", (247, 218, 208)),
    (4, "#eadaba", (234, 218, 186)),
    (5, "#d7bd96", (215, 189, 150)),
    (6, "#a07e56", (160, 126, 86)),
    (7, "#825c43", (130, 92, 67)),
    (8, "#604134", (96, 65, 52)),
    (9, "#3a312a", (58, 49, 42)),
    (10, "#292420", (41, 36, 32)),
]


@dataclass
class SkinToneCalibrationResult:
    monk_scale_index: int
    hex_code: str
    undertone: str
    rgb: tuple[int, int, int]


class SkinToneCalibrator:
    """Calibrates skin tone and undertone from user portrait photographs (Roadmap 2.3.1)."""

    @classmethod
    def calibrate_from_rgb(cls, r: int, g: int, b: int) -> SkinToneCalibrationResult:
        """Find closest Monk Skin Tone centroid and classify undertone."""
        # Find closest Monk centroid by Euclidean distance in RGB space
        best_index = 5
        best_hex = "#d7bd96"
        min_dist = float("inf")

        for idx, hex_code, (cr, cg, cb) in MONK_PALETTE:
            dist = math.sqrt((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2)
            if dist < min_dist:
                min_dist = dist
                best_index = idx
                best_hex = hex_code

        # Undertone classification
        gb_diff = g - b
        if gb_diff > 14:
            undertone = "warm"
        elif gb_diff < 5:
            undertone = "cool"
        else:
            undertone = "neutral"

        return SkinToneCalibrationResult(
            monk_scale_index=best_index,
            hex_code=best_hex,
            undertone=undertone,
            rgb=(r, g, b),
        )

    @classmethod
    def calibrate_from_image_bytes(cls, image_bytes: bytes) -> SkinToneCalibrationResult:
        """Sample central face region from portrait image bytes and calibrate."""
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            w, h = img.size
            # Sample central 20% area where face typically rests in portrait framing
            box = (int(w * 0.4), int(h * 0.25), int(w * 0.6), int(h * 0.45))
            face_crop = img.crop(box)
            small = face_crop.resize((1, 1), Image.Resampling.BOX)
            r, g, b = small.getpixel((0, 0))
            return cls.calibrate_from_rgb(r, g, b)
        except Exception:
            # Fallback neutral Monk-5
            return SkinToneCalibrationResult(
                monk_scale_index=5,
                hex_code="#d7bd96",
                undertone="neutral",
                rgb=(215, 189, 150),
            )
