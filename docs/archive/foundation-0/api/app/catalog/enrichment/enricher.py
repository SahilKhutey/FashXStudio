import io
import re

from PIL import Image

from .ports import EnrichmentResult, GarmentAttributes

COLOR_MAP = {
    "navy": "navy",
    "blue": "blue",
    "black": "black",
    "white": "white",
    "olive": "olive",
    "green": "green",
    "yellow": "yellow",
    "mustard": "yellow",
    "orange": "orange",
    "red": "red",
    "burgundy": "burgundy",
    "maroon": "maroon",
    "pink": "pink",
    "purple": "purple",
    "beige": "beige",
    "cream": "beige",
    "khaki": "beige",
    "brown": "brown",
    "tan": "brown",
    "grey": "grey",
    "gray": "grey",
    "charcoal": "charcoal",
    "teal": "teal",
}

COLLAR_RULES = [
    (r"\bbutton[- ]down\b", "button_down"),
    (r"\bmandarin\b|\bband\s*collar\b", "mandarin"),
    (r"\bspread\s*collar\b", "spread"),
    (r"\bcrew\s*neck\b", "crew_neck"),
    (r"\bv[- ]neck\b", "v_neck"),
    (r"\bpolo\b", "polo_collar"),
    (r"\bnotch\s*lapel\b", "notch_lapel"),
]

SLEEVE_RULES = [
    (r"\blong\s*sleeve[s]?\b|\bfull\s*sleeve[s]?\b", "long"),
    (r"\bshort\s*sleeve[s]?\b|\bhalf\s*sleeve[s]?\b", "short"),
    (r"\bsleeveless\b", "sleeveless"),
    (r"\bthree[- ]quarter\b|\b3/4\s*sleeve\b", "three_quarter"),
]

PATTERN_RULES = [
    (r"\bstrip(?:ed|es)?\b", "striped"),
    (r"\bcheck(?:ed|s)?\b|\bplaid\b|\bgingham\b", "checkered"),
    (r"\bfloral\b", "floral"),
    (r"\bprint(?:ed)?\b", "printed"),
    (r"\bsolid\b|\bplain\b", "solid"),
]

MATERIAL_RULES = [
    (r"\b100%\s*cotton\b|\bcotton\b", "100% cotton"),
    (r"\blinen\b", "linen"),
    (r"\bdenim\b", "denim"),
    (r"\bwool\b", "wool"),
    (r"\bsilk\b", "silk"),
    (r"\bpolyester\b", "polyester"),
]


class HeuristicGarmentEnricher:
    """Deterministic extractor parsing listing text and image data for garment attributes."""

    async def enrich(
        self,
        title: str,
        description: str | None = None,
        image_bytes: bytes | None = None,
    ) -> EnrichmentResult:
        full_text = f"{title} {description or ''}".lower()

        # 1. Collar
        collar: str | None = None
        collar_conf = 0.0
        for pat, val in COLLAR_RULES:
            if re.search(pat, full_text):
                collar = val
                collar_conf = 0.92
                break

        # 2. Sleeve Length
        sleeve: str | None = None
        sleeve_conf = 0.0
        for pat, val in SLEEVE_RULES:
            if re.search(pat, full_text):
                sleeve = val
                sleeve_conf = 0.94
                break

        # 3. Pattern
        pattern: str | None = None
        pattern_conf = 0.0
        for pat, val in PATTERN_RULES:
            if re.search(pat, full_text):
                pattern = val
                pattern_conf = 0.90
                break
        if pattern is None and ("solid" in full_text or "plain" in full_text):
            pattern = "solid"
            pattern_conf = 0.85

        # 4. Color from Text or Image
        color: str | None = None
        color_conf = 0.0
        for name, standard in COLOR_MAP.items():
            if re.search(rf"\b{name}\b", full_text):
                color = standard
                color_conf = 0.95
                break

        if color is None and image_bytes:
            extracted_color = self._extract_dominant_color_from_image(image_bytes)
            if extracted_color:
                color = extracted_color
                color_conf = 0.88

        # 5. Material
        material: str | None = None
        material_conf = 0.0
        for pat, val in MATERIAL_RULES:
            if re.search(pat, full_text):
                material = val
                material_conf = 0.91
                break

        # 6. Formality & Silhouette
        formality = "formal" if ("formal" in full_text or "suit" in full_text) else "casual"
        formality_conf = 0.88

        silhouette = "slim" if "slim" in full_text else "regular"
        silhouette_conf = 0.89

        attributes = GarmentAttributes(
            silhouette=silhouette,
            collar=collar,
            sleeve_length=sleeve,
            pattern=pattern or "solid",
            dominant_color=color or "navy",
            formality=formality,
            material=material,
        )

        confidences = {
            "silhouette": silhouette_conf,
            "formality": formality_conf,
            "pattern": pattern_conf or 0.85,
            "dominant_color": color_conf or 0.85,
        }
        if collar:
            confidences["collar"] = collar_conf
        if sleeve:
            confidences["sleeve_length"] = sleeve_conf
        if material:
            confidences["material"] = material_conf

        return EnrichmentResult(
            attributes=attributes,
            confidence_summary=confidences,
            model_version="heuristic-enricher-v1",
            embedding=[0.05] * 512,  # 512-dim mock vector matching Vector512 schema
        )

    def _extract_dominant_color_from_image(self, image_bytes: bytes) -> str | None:
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            # Sample center crop
            w, h = img.size
            center_crop = img.crop((w // 4, h // 4, 3 * w // 4, 3 * h // 4))
            resized = center_crop.resize((1, 1), Image.Resampling.BOX)
            r, g, b = resized.getpixel((0, 0))

            if r < 40 and g < 40 and b < 40:
                return "black"
            if r > 215 and g > 215 and b > 215:
                return "white"
            if b > r + 30 and b > g + 30:
                return "navy" if b < 120 else "blue"
            if g > r + 20 and g > b + 20:
                return "green"
            if r > g + 30 and r > b + 30:
                return "red"
            return "grey"
        except Exception:
            return None
