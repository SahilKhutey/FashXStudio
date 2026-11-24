"""VTO Error Classification and Error Taxonomy (Phase 07.5)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ErrorCategory(StrEnum):
    """Broad category governing automated retryability and operational triage."""

    TRANSIENT = "TRANSIENT"
    PERMANENT = "PERMANENT"
    CONFIGURATION = "CONFIGURATION"
    AMBIGUOUS = "AMBIGUOUS"
    CANCELLED = "CANCELLED"


class ErrorCode(StrEnum):
    """Normalized internal error codes across API, worker, provider, and storage."""

    # Transient failures (retryable)
    DATABASE_TEMPORARY = "DATABASE_TEMPORARY"
    QUEUE_UNAVAILABLE = "QUEUE_UNAVAILABLE"
    WORKER_INTERRUPTED = "WORKER_INTERRUPTED"
    PROVIDER_RATE_LIMITED = "PROVIDER_RATE_LIMITED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_STATUS_TIMEOUT = "PROVIDER_STATUS_TIMEOUT"
    PROVIDER_DOWNLOAD_FAILED = "PROVIDER_DOWNLOAD_FAILED"
    STORAGE_TEMPORARY_FAILURE = "STORAGE_TEMPORARY_FAILURE"

    # Ambiguous failures (NOT automatically retryable; requires reconciliation)
    PROVIDER_SUBMISSION_UNKNOWN = "PROVIDER_SUBMISSION_UNKNOWN"

    # Permanent failures (non-retryable)
    INVALID_INPUT_IMAGE = "INVALID_INPUT_IMAGE"
    UNSUPPORTED_CATEGORY = "UNSUPPORTED_CATEGORY"
    CONSENT_REQUIRED = "CONSENT_REQUIRED"
    CONSENT_WITHDRAWN = "CONSENT_WITHDRAWN"
    MERCHANT_PERMISSION_DENIED = "MERCHANT_PERMISSION_DENIED"
    PRODUCT_TAKEN_DOWN = "PRODUCT_TAKEN_DOWN"
    PROVIDER_CONTENT_REJECTED = "PROVIDER_CONTENT_REJECTED"
    OUTPUT_IMAGE_INVALID = "OUTPUT_IMAGE_INVALID"

    # Configuration failures (non-retryable; operator required)
    PROVIDER_AUTH_FAILED = "PROVIDER_AUTH_FAILED"
    PROVIDER_OUT_OF_CREDITS = "PROVIDER_OUT_OF_CREDITS"

    # Terminal lifecycle states
    MAX_RETRIES_EXCEEDED = "MAX_RETRIES_EXCEEDED"
    JOB_CANCELLED = "JOB_CANCELLED"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass(frozen=True)
class ErrorDefinition:
    """Metadata describing operational and customer impact of an error."""

    code: ErrorCode
    category: ErrorCategory
    retryable: bool
    safe_to_repeat: bool
    user_message: str
    suggested_action: str
    description: str


ERROR_REGISTRY: dict[ErrorCode, ErrorDefinition] = {
    ErrorCode.DATABASE_TEMPORARY: ErrorDefinition(
        code=ErrorCode.DATABASE_TEMPORARY,
        category=ErrorCategory.TRANSIENT,
        retryable=True,
        safe_to_repeat=True,
        user_message="Virtual try-on is temporarily experiencing technical delays. Retrying shortly.",
        suggested_action="Wait while we retry",
        description="Transient database connection loss or deadlock.",
    ),
    ErrorCode.QUEUE_UNAVAILABLE: ErrorDefinition(
        code=ErrorCode.QUEUE_UNAVAILABLE,
        category=ErrorCategory.TRANSIENT,
        retryable=True,
        safe_to_repeat=True,
        user_message="Virtual try-on queue is temporarily busy. Your job is safely saved.",
        suggested_action="Wait while we retry",
        description="Message broker connection error.",
    ),
    ErrorCode.WORKER_INTERRUPTED: ErrorDefinition(
        code=ErrorCode.WORKER_INTERRUPTED,
        category=ErrorCategory.TRANSIENT,
        retryable=True,
        safe_to_repeat=True,
        user_message="Processing worker was restarted. Resuming your try-on.",
        suggested_action="Check again shortly",
        description="Worker container restart or lease expiration.",
    ),
    ErrorCode.PROVIDER_RATE_LIMITED: ErrorDefinition(
        code=ErrorCode.PROVIDER_RATE_LIMITED,
        category=ErrorCategory.TRANSIENT,
        retryable=True,
        safe_to_repeat=True,
        user_message="Virtual try-on is busy right now. We are pacing requests.",
        suggested_action="Wait while we retry",
        description="External provider returned HTTP 429 Too Many Requests.",
    ),
    ErrorCode.PROVIDER_UNAVAILABLE: ErrorDefinition(
        code=ErrorCode.PROVIDER_UNAVAILABLE,
        category=ErrorCategory.TRANSIENT,
        retryable=True,
        safe_to_repeat=True,
        user_message="We are having trouble processing your try-on. Retrying automatically.",
        suggested_action="Check again shortly",
        description="External provider returned 5xx server error.",
    ),
    ErrorCode.PROVIDER_STATUS_TIMEOUT: ErrorDefinition(
        code=ErrorCode.PROVIDER_STATUS_TIMEOUT,
        category=ErrorCategory.TRANSIENT,
        retryable=True,
        safe_to_repeat=True,
        user_message="Your try-on is taking longer than expected. Continuing to monitor.",
        suggested_action="Keep this screen open or check later",
        description="Polling request timed out; polling can safely resume.",
    ),
    ErrorCode.PROVIDER_DOWNLOAD_FAILED: ErrorDefinition(
        code=ErrorCode.PROVIDER_DOWNLOAD_FAILED,
        category=ErrorCategory.TRANSIENT,
        retryable=True,
        safe_to_repeat=True,
        user_message="Your result is almost ready. We are retrieving it.",
        suggested_action="Check again shortly",
        description="Network interruption while fetching completed result bytes.",
    ),
    ErrorCode.STORAGE_TEMPORARY_FAILURE: ErrorDefinition(
        code=ErrorCode.STORAGE_TEMPORARY_FAILURE,
        category=ErrorCategory.TRANSIENT,
        retryable=True,
        safe_to_repeat=True,
        user_message="Finalizing your try-on result.",
        suggested_action="Check again shortly",
        description="S3 storage PUT failed transiently.",
    ),
    ErrorCode.PROVIDER_SUBMISSION_UNKNOWN: ErrorDefinition(
        code=ErrorCode.PROVIDER_SUBMISSION_UNKNOWN,
        category=ErrorCategory.AMBIGUOUS,
        retryable=False,
        safe_to_repeat=False,
        user_message="We are checking the status of your try-on with the inference provider.",
        suggested_action="Do not submit the same request again yet",
        description="Provider submission timed out; outcome unknown. Must reconcile before any retry.",
    ),
    ErrorCode.INVALID_INPUT_IMAGE: ErrorDefinition(
        code=ErrorCode.INVALID_INPUT_IMAGE,
        category=ErrorCategory.PERMANENT,
        retryable=False,
        safe_to_repeat=False,
        user_message="This photo cannot be used for virtual try-on.",
        suggested_action="Upload a clear, full-body photo",
        description="Input image failed validation (occlusion, resolution, format).",
    ),
    ErrorCode.UNSUPPORTED_CATEGORY: ErrorDefinition(
        code=ErrorCode.UNSUPPORTED_CATEGORY,
        category=ErrorCategory.PERMANENT,
        retryable=False,
        safe_to_repeat=False,
        user_message="Virtual try-on is not yet supported for this clothing category.",
        suggested_action="Try another product",
        description="Product belongs to unsupported category (e.g. footwear, accessories).",
    ),
    ErrorCode.CONSENT_REQUIRED: ErrorDefinition(
        code=ErrorCode.CONSENT_REQUIRED,
        category=ErrorCategory.PERMANENT,
        retryable=False,
        safe_to_repeat=False,
        user_message="Please provide permission to process your photo for virtual try-on.",
        suggested_action="Review consent in account settings",
        description="Missing DPDP third-party VTO processing consent.",
    ),
    ErrorCode.CONSENT_WITHDRAWN: ErrorDefinition(
        code=ErrorCode.CONSENT_WITHDRAWN,
        category=ErrorCategory.PERMANENT,
        retryable=False,
        safe_to_repeat=False,
        user_message="Try-on stopped because photo processing consent was withdrawn.",
        suggested_action="Grant consent if you wish to use virtual try-on",
        description="Shopper revoked consent prior to or during execution.",
    ),
    ErrorCode.MERCHANT_PERMISSION_DENIED: ErrorDefinition(
        code=ErrorCode.MERCHANT_PERMISSION_DENIED,
        category=ErrorCategory.PERMANENT,
        retryable=False,
        safe_to_repeat=False,
        user_message="The merchant has not authorized virtual try-on for this product.",
        suggested_action="Select another product",
        description="Merchant image rights do not include AI processing / VTO.",
    ),
    ErrorCode.PRODUCT_TAKEN_DOWN: ErrorDefinition(
        code=ErrorCode.PRODUCT_TAKEN_DOWN,
        category=ErrorCategory.PERMANENT,
        retryable=False,
        safe_to_repeat=False,
        user_message="This product is no longer available for virtual try-on.",
        suggested_action="Choose another product",
        description="Product or merchant offer suspended or delisted.",
    ),
    ErrorCode.PROVIDER_CONTENT_REJECTED: ErrorDefinition(
        code=ErrorCode.PROVIDER_CONTENT_REJECTED,
        category=ErrorCategory.PERMANENT,
        retryable=False,
        safe_to_repeat=False,
        user_message="The input image could not be processed by the try-on engine.",
        suggested_action="Try a different photograph",
        description="External provider rejected image content as unsuitable.",
    ),
    ErrorCode.OUTPUT_IMAGE_INVALID: ErrorDefinition(
        code=ErrorCode.OUTPUT_IMAGE_INVALID,
        category=ErrorCategory.PERMANENT,
        retryable=False,
        safe_to_repeat=False,
        user_message="We could not create a usable try-on result from these images.",
        suggested_action="Try different images",
        description="Generated image failed post-inference visual assessment or contrast check.",
    ),
    ErrorCode.PROVIDER_AUTH_FAILED: ErrorDefinition(
        code=ErrorCode.PROVIDER_AUTH_FAILED,
        category=ErrorCategory.CONFIGURATION,
        retryable=False,
        safe_to_repeat=False,
        user_message="Virtual try-on is temporarily unavailable. Engineering is notified.",
        suggested_action="Try again later",
        description="Provider API credentials rejected (401/403).",
    ),
    ErrorCode.PROVIDER_OUT_OF_CREDITS: ErrorDefinition(
        code=ErrorCode.PROVIDER_OUT_OF_CREDITS,
        category=ErrorCategory.CONFIGURATION,
        retryable=False,
        safe_to_repeat=False,
        user_message="Virtual try-on service is temporarily unavailable.",
        suggested_action="Check back later",
        description="Provider account quota or credit exhausted.",
    ),
    ErrorCode.MAX_RETRIES_EXCEEDED: ErrorDefinition(
        code=ErrorCode.MAX_RETRIES_EXCEEDED,
        category=ErrorCategory.PERMANENT,
        retryable=False,
        safe_to_repeat=False,
        user_message="We could not complete your try-on this time. Please try again later.",
        suggested_action="Try again later",
        description="All retry attempts exhausted for this job.",
    ),
    ErrorCode.JOB_CANCELLED: ErrorDefinition(
        code=ErrorCode.JOB_CANCELLED,
        category=ErrorCategory.CANCELLED,
        retryable=False,
        safe_to_repeat=False,
        user_message="Your try-on has been cancelled.",
        suggested_action="Submit a new request if needed",
        description="Job cancelled by shopper or administrative action.",
    ),
}

DEFAULT_UNKNOWN_DEFINITION = ErrorDefinition(
    code=ErrorCode.UNKNOWN_ERROR,
    category=ErrorCategory.PERMANENT,
    retryable=False,
    safe_to_repeat=False,
    user_message="An unexpected error occurred during virtual try-on.",
    suggested_action="Try again later",
    description="Unclassified internal error. Defaulted to non-retryable for safety.",
)


def classify_error(code: ErrorCode | str) -> ErrorDefinition:
    """Classify an error code into its operational ErrorDefinition.

    Unknown codes are safely treated as non-retryable to prevent uncontrolled retry loops.
    """
    if isinstance(code, ErrorCode):
        return ERROR_REGISTRY.get(code, DEFAULT_UNKNOWN_DEFINITION)
    try:
        enum_code = ErrorCode(code.upper().strip())
        return ERROR_REGISTRY.get(enum_code, DEFAULT_UNKNOWN_DEFINITION)
    except (ValueError, AttributeError):
        return DEFAULT_UNKNOWN_DEFINITION
