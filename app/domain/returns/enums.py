from enum import StrEnum


class CancellationStatus(StrEnum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class ReturnStatus(StrEnum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    PICKUP_PENDING = "pickup_pending"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    INSPECTION = "inspection"
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RefundStatus(StrEnum):
    REQUESTED = "requested"
    APPROVED = "approved"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReplacementStatus(StrEnum):
    REQUESTED = "requested"
    APPROVED = "approved"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ReturnReason(StrEnum):
    WRONG_ITEM = "wrong_item"
    DAMAGED = "damaged"
    DEFECTIVE = "defective"
    SIZE_ISSUE = "size_issue"
    COLOR_DIFFERENCE = "color_difference"
    NOT_AS_EXPECTED = "not_as_expected"
    CHANGED_MIND = "changed_mind"
    OTHER = "other"


class RefundReason(StrEnum):
    ORDER_CANCELLED = "order_cancelled"
    RETURN_ACCEPTED = "return_accepted"
    DAMAGED_ITEM = "damaged_item"
    DEFECTIVE_ITEM = "defective_item"
    DUPLICATE_CHARGE = "duplicate_charge"
    MANUAL_ADJUSTMENT = "manual_adjustment"
    OTHER = "other"
