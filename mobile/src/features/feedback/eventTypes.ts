export type FeedbackEventType =
  | "PRODUCT_IMPRESSION"
  | "PRODUCT_CLICKED"
  | "PRODUCT_DETAIL_VIEWED"
  | "PRODUCT_LIKED"
  | "PRODUCT_DISLIKED"
  | "PRODUCT_LIKE_REMOVED"
  | "PRODUCT_DISLIKE_REMOVED"
  | "PRODUCT_SAVED"
  | "PRODUCT_UNSAVED"
  | "VTO_QUALITY_FEEDBACK_SUBMITTED"
  | "FIT_FEEDBACK_SUBMITTED"
  | "MERCHANT_OUTBOUND_CLICKED";

export type ReactionState = "NONE" | "LIKE" | "DISLIKE";

export interface FeedbackEventPayload {
  event_id: string;
  event_type: FeedbackEventType;
  subject_type: string;
  subject_id: string;
  occurred_at: string;
  schema_version: number;
  source?: string;
  session_id?: string | null;
  context?: Record<string, unknown>;
}
