"""Central event registry defining classification, subject types, and consent rules."""

from __future__ import annotations

from dataclasses import dataclass

from fashx.feedback.enums import ConsentPurpose, FeedbackClass, FeedbackEventType


@dataclass(frozen=True)
class EventSpec:
    """Authoritative metadata for a registered feedback event type."""

    event_type: FeedbackEventType
    feedback_class: FeedbackClass
    subject_type: str
    consent_purpose: ConsentPurpose
    server_only: bool = False


EVENT_REGISTRY: dict[str, EventSpec] = {
    FeedbackEventType.PRODUCT_IMPRESSION.value: EventSpec(
        event_type=FeedbackEventType.PRODUCT_IMPRESSION,
        feedback_class=FeedbackClass.IMPLICIT,
        subject_type="PRODUCT",
        consent_purpose=ConsentPurpose.PRODUCT_ANALYTICS,
    ),
    FeedbackEventType.PRODUCT_CLICKED.value: EventSpec(
        event_type=FeedbackEventType.PRODUCT_CLICKED,
        feedback_class=FeedbackClass.IMPLICIT,
        subject_type="PRODUCT",
        consent_purpose=ConsentPurpose.PERSONALIZED_RANKING,
    ),
    FeedbackEventType.PRODUCT_DETAIL_VIEWED.value: EventSpec(
        event_type=FeedbackEventType.PRODUCT_DETAIL_VIEWED,
        feedback_class=FeedbackClass.IMPLICIT,
        subject_type="PRODUCT",
        consent_purpose=ConsentPurpose.PERSONALIZED_RANKING,
    ),
    FeedbackEventType.PRODUCT_LIKED.value: EventSpec(
        event_type=FeedbackEventType.PRODUCT_LIKED,
        feedback_class=FeedbackClass.EXPLICIT,
        subject_type="PRODUCT",
        consent_purpose=ConsentPurpose.PERSONALIZED_RANKING,
    ),
    FeedbackEventType.PRODUCT_DISLIKED.value: EventSpec(
        event_type=FeedbackEventType.PRODUCT_DISLIKED,
        feedback_class=FeedbackClass.EXPLICIT,
        subject_type="PRODUCT",
        consent_purpose=ConsentPurpose.PERSONALIZED_RANKING,
    ),
    FeedbackEventType.PRODUCT_LIKE_REMOVED.value: EventSpec(
        event_type=FeedbackEventType.PRODUCT_LIKE_REMOVED,
        feedback_class=FeedbackClass.EXPLICIT,
        subject_type="PRODUCT",
        consent_purpose=ConsentPurpose.PERSONALIZED_RANKING,
    ),
    FeedbackEventType.PRODUCT_DISLIKE_REMOVED.value: EventSpec(
        event_type=FeedbackEventType.PRODUCT_DISLIKE_REMOVED,
        feedback_class=FeedbackClass.EXPLICIT,
        subject_type="PRODUCT",
        consent_purpose=ConsentPurpose.PERSONALIZED_RANKING,
    ),
    FeedbackEventType.PRODUCT_SAVED.value: EventSpec(
        event_type=FeedbackEventType.PRODUCT_SAVED,
        feedback_class=FeedbackClass.EXPLICIT,
        subject_type="PRODUCT",
        consent_purpose=ConsentPurpose.PERSONALIZED_RANKING,
    ),
    FeedbackEventType.PRODUCT_UNSAVED.value: EventSpec(
        event_type=FeedbackEventType.PRODUCT_UNSAVED,
        feedback_class=FeedbackClass.EXPLICIT,
        subject_type="PRODUCT",
        consent_purpose=ConsentPurpose.PERSONALIZED_RANKING,
    ),
    FeedbackEventType.VTO_REQUESTED.value: EventSpec(
        event_type=FeedbackEventType.VTO_REQUESTED,
        feedback_class=FeedbackClass.SYSTEM_OUTCOME,
        subject_type="VTO_JOB",
        consent_purpose=ConsentPurpose.ESSENTIAL_SERVICE,
        server_only=True,
    ),
    FeedbackEventType.VTO_COMPLETED.value: EventSpec(
        event_type=FeedbackEventType.VTO_COMPLETED,
        feedback_class=FeedbackClass.SYSTEM_OUTCOME,
        subject_type="VTO_JOB",
        consent_purpose=ConsentPurpose.ESSENTIAL_SERVICE,
        server_only=True,
    ),
    FeedbackEventType.VTO_FAILED.value: EventSpec(
        event_type=FeedbackEventType.VTO_FAILED,
        feedback_class=FeedbackClass.SYSTEM_OUTCOME,
        subject_type="VTO_JOB",
        consent_purpose=ConsentPurpose.ESSENTIAL_SERVICE,
        server_only=True,
    ),
    FeedbackEventType.VTO_CANCELLED.value: EventSpec(
        event_type=FeedbackEventType.VTO_CANCELLED,
        feedback_class=FeedbackClass.SYSTEM_OUTCOME,
        subject_type="VTO_JOB",
        consent_purpose=ConsentPurpose.ESSENTIAL_SERVICE,
        server_only=True,
    ),
    FeedbackEventType.VTO_QUALITY_FEEDBACK_SUBMITTED.value: EventSpec(
        event_type=FeedbackEventType.VTO_QUALITY_FEEDBACK_SUBMITTED,
        feedback_class=FeedbackClass.EXPLICIT,
        subject_type="VTO_JOB",
        consent_purpose=ConsentPurpose.FEEDBACK_EVALUATION,
    ),
    FeedbackEventType.FIT_FEEDBACK_SUBMITTED.value: EventSpec(
        event_type=FeedbackEventType.FIT_FEEDBACK_SUBMITTED,
        feedback_class=FeedbackClass.EXPLICIT,
        subject_type="FIT_RECOMMENDATION",
        consent_purpose=ConsentPurpose.FEEDBACK_EVALUATION,
    ),
    FeedbackEventType.MERCHANT_OUTBOUND_CLICKED.value: EventSpec(
        event_type=FeedbackEventType.MERCHANT_OUTBOUND_CLICKED,
        feedback_class=FeedbackClass.IMPLICIT,
        subject_type="MERCHANT_OFFER",
        consent_purpose=ConsentPurpose.PRODUCT_ANALYTICS,
    ),
    FeedbackEventType.PURCHASE_INTENT_RECORDED.value: EventSpec(
        event_type=FeedbackEventType.PURCHASE_INTENT_RECORDED,
        feedback_class=FeedbackClass.IMPLICIT,
        subject_type="MERCHANT_OFFER",
        consent_purpose=ConsentPurpose.PRODUCT_ANALYTICS,
    ),
    FeedbackEventType.PURCHASE_CONFIRMED.value: EventSpec(
        event_type=FeedbackEventType.PURCHASE_CONFIRMED,
        feedback_class=FeedbackClass.VERIFIED_COMMERCIAL,
        subject_type="MERCHANT_OFFER",
        consent_purpose=ConsentPurpose.ESSENTIAL_SERVICE,
        server_only=True,
    ),
    FeedbackEventType.PURCHASE_CANCELLED.value: EventSpec(
        event_type=FeedbackEventType.PURCHASE_CANCELLED,
        feedback_class=FeedbackClass.VERIFIED_COMMERCIAL,
        subject_type="MERCHANT_OFFER",
        consent_purpose=ConsentPurpose.ESSENTIAL_SERVICE,
        server_only=True,
    ),
    FeedbackEventType.ITEM_RETURNED.value: EventSpec(
        event_type=FeedbackEventType.ITEM_RETURNED,
        feedback_class=FeedbackClass.VERIFIED_COMMERCIAL,
        subject_type="MERCHANT_OFFER",
        consent_purpose=ConsentPurpose.ESSENTIAL_SERVICE,
        server_only=True,
    ),
}
