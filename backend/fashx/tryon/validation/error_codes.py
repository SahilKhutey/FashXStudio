"""Standard error codes and shopper remediation messages for VTO input validation."""

from __future__ import annotations

# Error Code Constants
VTO_CONSENT_REQUIRED = "VTO_CONSENT_REQUIRED"
VTO_CONSENT_WITHDRAWN = "VTO_CONSENT_WITHDRAWN"
IMAGE_NOT_OWNED_OR_NOT_FOUND = "IMAGE_NOT_OWNED_OR_NOT_FOUND"
IMAGE_NOT_ACTIVE = "IMAGE_NOT_ACTIVE"
FORMAT_UNSUPPORTED = "FORMAT_UNSUPPORTED"
IMAGE_TOO_LARGE = "IMAGE_TOO_LARGE"
IMAGE_TOO_SMALL = "IMAGE_TOO_SMALL"
IMAGE_CORRUPTED = "IMAGE_CORRUPTED"
PERSON_NOT_DETECTED = "PERSON_NOT_DETECTED"
MULTIPLE_PEOPLE_DETECTED = "MULTIPLE_PEOPLE_DETECTED"
BODY_REGION_NOT_VISIBLE = "BODY_REGION_NOT_VISIBLE"
POSE_UNSUPPORTED = "POSE_UNSUPPORTED"
BODY_REGION_OCCLUDED = "BODY_REGION_OCCLUDED"
PRODUCT_NOT_ACTIVE = "PRODUCT_NOT_ACTIVE"
IMAGE_PRODUCT_MISMATCH = "IMAGE_PRODUCT_MISMATCH"
GARMENT_PROCESSING_NOT_AUTHORIZED = "GARMENT_PROCESSING_NOT_AUTHORIZED"
GARMENT_NOT_VISIBLE = "GARMENT_NOT_VISIBLE"
GARMENT_BACKGROUND_UNSUITABLE = "GARMENT_BACKGROUND_UNSUITABLE"
UNSUPPORTED_GARMENT_CATEGORY = "UNSUPPORTED_GARMENT_CATEGORY"
IMAGE_VERSION_CHANGED = "IMAGE_VERSION_CHANGED"
IMAGE_VALIDATION_UNAVAILABLE = "IMAGE_VALIDATION_UNAVAILABLE"

# User-facing guidance mapping
USER_REMEDIATION_MESSAGES: dict[str, str] = {
    VTO_CONSENT_REQUIRED: "Please grant virtual try-on permission to try on garments.",
    VTO_CONSENT_WITHDRAWN: "Virtual try-on consent was withdrawn. Please grant permission to continue.",
    IMAGE_NOT_OWNED_OR_NOT_FOUND: "Selected photo is unavailable. Please choose another photo.",
    IMAGE_NOT_ACTIVE: "Selected photo is inactive. Please choose an active photo.",
    FORMAT_UNSUPPORTED: "Upload a JPG, PNG, or WebP image.",
    IMAGE_TOO_LARGE: "The image exceeds maximum size limits (10 MB or 4096px). Select a smaller image.",
    IMAGE_TOO_SMALL: "Upload a clearer photograph with higher resolution (minimum 512×512 px).",
    IMAGE_CORRUPTED: "The image could not be opened. Please upload it again.",
    PERSON_NOT_DETECTED: "Make sure one person is clearly visible in the photograph.",
    MULTIPLE_PEOPLE_DETECTED: "Make sure only one person is visible in the photograph.",
    BODY_REGION_NOT_VISIBLE: "Move farther back so the required body area is visible.",
    POSE_UNSUPPORTED: "Stand upright and face the camera directly.",
    BODY_REGION_OCCLUDED: "Keep bags, hands, and accessories away from the garment area.",
    PRODUCT_NOT_ACTIVE: "This product is not currently active for virtual try-on.",
    IMAGE_PRODUCT_MISMATCH: "Garment image does not match the selected product.",
    GARMENT_PROCESSING_NOT_AUTHORIZED: "Virtual try-on processing is not currently authorized for this product.",
    GARMENT_NOT_VISIBLE: "Garment is not clearly visible in the product image.",
    GARMENT_BACKGROUND_UNSUITABLE: "Product image background is unsuitable for automatic try-on.",
    UNSUPPORTED_GARMENT_CATEGORY: "This garment category is not currently supported for virtual try-on.",
    IMAGE_VERSION_CHANGED: "Product image was updated. Please refresh and try again.",
    IMAGE_VALIDATION_UNAVAILABLE: "Image validation service is temporarily busy. Please retry shortly.",
}


def get_user_remediation_message(error_code: str) -> str:
    """Retrieve shopper-friendly explanation and correction guidance."""
    return USER_REMEDIATION_MESSAGES.get(
        error_code,
        "We couldn't use this photo or garment. Please select another image.",
    )
