from enum import StrEnum


class BuildType(StrEnum):
    SLIM = "slim"
    ATHLETIC = "athletic"
    REGULAR = "regular"
    BROAD = "broad"


class DataType(StrEnum):
    BODY_PHOTO = "body_photo"
    MEASUREMENTS = "measurements"
    CAMERA_FEED = "camera_feed"
    PERSONALIZATION = "personalization"
    MODEL_TRAINING = "model_training"


class PhotoType(StrEnum):
    SKIN_TONE = "skin_tone"
    TRYON_REFERENCE = "tryon_reference"


class PhotoStatus(StrEnum):
    PROCESSING = "processing"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class PhotoRejectReason(StrEnum):
    FACE_NOT_VISIBLE = "face_not_visible"
    INVALID_FORMAT = "invalid_format"
    LANDSCAPE_ORIENTATION = "landscape_orientation"
    LOW_CONTRAST = "low_contrast"
    MULTIPLE_PEOPLE = "multiple_people"
    PERSON_NOT_DETECTED = "person_not_detected"
    POSE_NOT_UPRIGHT = "pose_not_upright"
    RESOLUTION_TOO_LOW = "resolution_too_low"
    TOO_BRIGHT = "too_bright"
    TOO_DARK = "too_dark"


class MeasurementSource(StrEnum):
    USER_ENTERED = "user_entered"
    CV_ESTIMATED = "cv_estimated"
    MANUAL = "manual"


class GarmentImageType(StrEnum):
    FRONT = "front"
    BACK = "back"
    MODEL = "model"
    DETAIL = "detail"
    SIZE_CHART = "size_chart"


class EnrichmentStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEW_REQUIRED = "review_required"


class TryOnStatus(StrEnum):
    QUEUED = "queued"
    VALIDATING = "validating"
    PREPROCESSING = "preprocessing"
    INFERENCE = "inference"
    POSTPROCESSING = "postprocessing"
    QUALITY_CHECK = "quality_check"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TryOnFailureReason(StrEnum):
    BAD_INPUT_PHOTO = "bad_input_photo"
    UNSUPPORTED_GARMENT = "unsupported_garment"
    MODEL_ERROR = "model_error"
    GPU_UNAVAILABLE = "gpu_unavailable"
    TIMEOUT = "timeout"
    STORAGE_ERROR = "storage_error"
    QUALITY_REJECTED = "quality_rejected"
    INTERNAL_ERROR = "internal_error"


class FitVerdict(StrEnum):
    TOO_TIGHT = "too_tight"
    TRUE_TO_SIZE = "true_to_size"
    TOO_LOOSE = "too_loose"


class VisualAccuracy(StrEnum):
    VERY_INACCURATE = "very_inaccurate"
    INACCURATE = "inaccurate"
    NEUTRAL = "neutral"
    ACCURATE = "accurate"
    VERY_ACCURATE = "very_accurate"
