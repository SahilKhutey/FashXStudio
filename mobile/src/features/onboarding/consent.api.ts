import { api } from "../../api/client";

export type OnboardingConsentPurpose =
  | "PERSONALIZED_RANKING"
  | "PRODUCT_ANALYTICS"
  | "THIRD_PARTY_VTO_PROCESSING"
  | "VTO_QUALITY_REVIEW"
  | "FIT_FEEDBACK_PROCESSING"
  | "MODEL_TRAINING"
  | "PURCHASE_ATTRIBUTION";

export type ConsentSubmission = {
  purpose: OnboardingConsentPurpose;
  granted: boolean;
  noticeVersion: string;
};

export async function savePurposeConsent(
  submission: ConsentSubmission,
): Promise<Record<string, unknown>> {
  return api<Record<string, unknown>>(
    `/profile/fit/consents/${encodeURIComponent(submission.purpose)}`,
    {
      method: "PUT",
      body: JSON.stringify({
        granted: submission.granted,
        notice_version: submission.noticeVersion,
      }),
    },
  );
}
