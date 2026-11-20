from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ValueStatus(StrEnum):
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"
    NOT_PROVIDED = "NOT_PROVIDED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_DETECTED = "NOT_DETECTED"
    CONFLICTING = "CONFLICTING"
    PENDING_REVIEW = "PENDING_REVIEW"
    OTHER = "OTHER"


class AttributeSource(StrEnum):
    MERCHANT = "MERCHANT"
    SOURCE_FEED = "SOURCE_FEED"
    RULE_BASED = "RULE_BASED"
    AI_IMAGE = "AI_IMAGE"
    AI_TEXT = "AI_TEXT"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    USER_FEEDBACK = "USER_FEEDBACK"


class ReviewStatus(StrEnum):
    UNREVIEWED = "UNREVIEWED"
    APPROVED = "APPROVED"
    OVERRIDDEN = "OVERRIDDEN"


class StyleFamily(StrEnum):
    WESTERN = "western"
    INDIAN_ETHNIC = "indian_ethnic"
    FUSION = "fusion"
    SPORTSWEAR = "sportswear"
    UNIVERSAL = "universal"


class IntendedAudience(StrEnum):
    MEN = "men"
    WOMEN = "women"
    UNISEX = "unisex"
    BOYS = "boys"
    GIRLS = "girls"
    KIDS = "kids"
    INFANTS = "infants"
    ALL_AUDIENCES = "all_audiences"
    UNKNOWN = "unknown"


class Occasion(StrEnum):
    EVERYDAY = "everyday"
    CASUAL = "casual"
    WORKWEAR = "workwear"
    BUSINESS_FORMAL = "business_formal"
    PARTY = "party"
    WEDDING = "wedding"
    FESTIVE = "festive"
    TRADITIONAL_CEREMONY = "traditional_ceremony"
    DATE_NIGHT = "date_night"
    TRAVEL = "travel"
    VACATION = "vacation"
    SPORTS = "sports"
    GYM = "gym"
    OUTDOOR = "outdoor"
    LOUNGE = "lounge"
    EVENING = "evening"


class ColorFamily(StrEnum):
    BLACK = "black"
    WHITE = "white"
    GREY = "grey"
    BROWN = "brown"
    RED = "red"
    PINK = "pink"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    PURPLE = "purple"
    METALLIC = "metallic"
    MULTICOLOR = "multicolor"
    OTHER = "other"


class PatternType(StrEnum):
    SOLID = "solid"
    STRIPED = "striped"
    CHECKED = "checked"
    PLAID = "plaid"
    FLORAL = "floral"
    GEOMETRIC = "geometric"
    ABSTRACT = "abstract"
    GRAPHIC = "graphic"
    PRINTED = "printed"
    EMBROIDERED = "embroidered"
    POLKA_DOT = "polka_dot"
    ANIMAL_PRINT = "animal_print"
    CAMOUFLAGE = "camouflage"
    PAISLEY = "paisley"
    IKAT = "ikat"
    TIE_DYE = "tie_dye"
    COLOR_BLOCK = "color_block"
    TEXTURED = "textured"
    SELF_DESIGN = "self_design"
    OTHER = "other"
    # Indian extensions
    BLOCK_PRINT = "block_print"
    BANDHANI = "bandhani"
    AJRAK = "ajrak"
    KALAMKARI = "kalamkari"
    BATIK = "batik"
    LEHERIYA = "leheriya"
    CHIKANKARI = "chikankari"
    PHULKARI = "phulkari"
    KANTHA = "kantha"
    ZARI_WORK = "zari_work"


class MaterialType(StrEnum):
    COTTON = "cotton"
    ORGANIC_COTTON = "organic_cotton"
    LINEN = "linen"
    SILK = "silk"
    RAW_SILK = "raw_silk"
    WOOL = "wool"
    CASHMERE = "cashmere"
    POLYESTER = "polyester"
    NYLON = "nylon"
    VISCOSE = "viscose"
    RAYON = "rayon"
    MODAL = "modal"
    LYOCELL = "lyocell"
    ACRYLIC = "acrylic"
    DENIM = "denim"
    LEATHER = "leather"
    FAUX_LEATHER = "faux_leather"
    SATIN = "satin"
    CHIFFON = "chiffon"
    GEORGETTE = "georgette"
    CREPE = "crepe"
    VELVET = "velvet"
    NET = "net"
    OTHER = "other"


class SleeveType(StrEnum):
    SLEEVELESS = "sleeveless"
    CAP_SLEEVE = "cap_sleeve"
    SHORT_SLEEVE = "short_sleeve"
    HALF_SLEEVE = "half_sleeve"
    THREE_QUARTER_SLEEVE = "three_quarter_sleeve"
    FULL_SLEEVE = "full_sleeve"
    LONG_SLEEVE = "long_sleeve"
    ROLL_UP_SLEEVE = "roll_up_sleeve"
    BELL_SLEEVE = "bell_sleeve"
    PUFF_SLEEVE = "puff_sleeve"
    BISHOP_SLEEVE = "bishop_sleeve"
    RAGLAN_SLEEVE = "raglan_sleeve"
    OTHER = "other"


class NecklineType(StrEnum):
    CREW_NECK = "crew_neck"
    ROUND_NECK = "round_neck"
    V_NECK = "v_neck"
    SCOOP_NECK = "scoop_neck"
    BOAT_NECK = "boat_neck"
    SQUARE_NECK = "square_neck"
    SWEETHEART_NECK = "sweetheart_neck"
    HALTER_NECK = "halter_neck"
    HIGH_NECK = "high_neck"
    MOCK_NECK = "mock_neck"
    TURTLE_NECK = "turtle_neck"
    COLLARED = "collared"
    MANDARIN_COLLAR = "mandarin_collar"
    PETER_PAN_COLLAR = "peter_pan_collar"
    OFF_SHOULDER = "off_shoulder"
    ONE_SHOULDER = "one_shoulder"
    OTHER = "other"


class FitType(StrEnum):
    REGULAR = "regular"
    SLIM = "slim"
    RELAXED = "relaxed"
    OVERSIZED = "oversized"
    FITTED = "fitted"
    TIGHT = "tight"
    LOOSE = "loose"


class SilhouetteType(StrEnum):
    STRAIGHT = "straight"
    A_LINE = "a_line"
    FIT_AND_FLARE = "fit_and_flare"
    BODYCON = "bodycon"
    FLARED = "flared"
    WIDE_LEG = "wide_leg"
    TAPERED = "tapered"
    BOOTCUT = "bootcut"
    SKINNY = "skinny"
    CROPPED = "cropped"
    LAYERED = "layered"
    ASYMMETRIC = "asymmetric"
    OTHER = "other"


class MaterialBlendItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    material: str
    percentage: float = Field(ge=0.0, le=100.0)


class FabricSpecification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materials: list[MaterialBlendItem] = Field(default_factory=list)
    fabric_structure: str | None = None  # knit, woven, non_woven
    fabric_weight: str | None = None
    material_source: str | None = None

    @model_validator(mode="after")
    def validate_percentages_sum(self) -> FabricSpecification:
        if self.materials:
            total = sum(item.percentage for item in self.materials)
            # If all components specified with percentages, allow 1.0 tolerance for rounding
            if total > 0 and (total < 99.0 or total > 101.0):
                raise ValueError(f"Fabric composition percentages must sum to ~100% (got {total:.1f}%)")
        return self


class ColorSpecification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary_color: str
    secondary_colors: list[str] = Field(default_factory=list)
    color_family: str
    color_source: str | None = None
    color_confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class IndianWearAttributes(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ethnic_garment_type: str | None = None
    kurta_length: str | None = None
    kurta_style: str | None = None
    saree_drape_style: str | None = None
    saree_length_meters: float | None = None
    blouse_included: bool | None = None
    dupatta_included: bool | None = None
    closure_type: str | None = None
    embellishments: list[str] = Field(default_factory=list)
    craft_technique: list[str] = Field(default_factory=list)
    weave_type: str | None = None
    regional_style: str | None = None
    set_components: list[str] = Field(default_factory=list)


class WesternWearAttributes(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shirt_type: str | None = None
    t_shirt_type: str | None = None
    dress_type: str | None = None
    trouser_type: str | None = None
    jeans_fit: str | None = None
    rise_type: str | None = None
    waistband_type: str | None = None
    closure_type: str | None = None
    length_type: str | None = None
    layering_type: str | None = None
    hood_type: str | None = None
    pocket_configuration: str | None = None


class FootwearAttributes(BaseModel):
    model_config = ConfigDict(extra="forbid")

    footwear_type: str | None = None
    closure_type: str | None = None
    toe_shape: str | None = None
    heel_type: str | None = None
    heel_height_cm: float | None = None
    upper_material: str | None = None
    sole_material: str | None = None
    occasion: str | None = None
    shoe_width: str | None = None
    size_system: str | None = None


class AccessoryAttributes(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accessory_type: str | None = None
    material: str | None = None
    color: str | None = None
    dimensions: str | None = None
    closure: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class TaxonomyAttributeValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attribute_id: str
    value: Any | None = None
    status: ValueStatus = ValueStatus.UNKNOWN
    source: AttributeSource | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class ProductClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    taxonomy_version: str
    category_id: str
    garment_type_id: str | None = None
    style_family: str | None = None
    intended_audience: str | None = None
    occasions: list[str] = Field(default_factory=list)
    attributes: dict[str, TaxonomyAttributeValue] = Field(default_factory=dict)
    indian_wear: IndianWearAttributes | None = None
    western_wear: WesternWearAttributes | None = None
    footwear: FootwearAttributes | None = None
    accessories: AccessoryAttributes | None = None
    classification_status: str = "VERIFIED"
    classification_source: AttributeSource = AttributeSource.MERCHANT
    classification_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
