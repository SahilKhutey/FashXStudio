/**
 * Virtual Try-On API Client
 * Wraps typed backend endpoints for try-on submission, polling, artifacts, and feedback.
 */

import { api } from "../../api/client";
import { components } from "../../api/schema";

export type TryOnJobStatusResponse = components["schemas"]["TryOnJobStatusResponse"];
export type TryOnJobSubmissionResponse = components["schemas"]["TryOnJobSubmissionResponse"];
export type TryOnJobListItem = components["schemas"]["TryOnJobListItem"];
export type VisualAccuracy = components["schemas"]["VisualAccuracy"];

export interface SubmitTryOnParams {
  garmentId: string;
  idempotencyKey?: string;
  renderConfig?: Record<string, unknown>;
}

export interface TryOnFeedbackParams {
  jobId: string;
  userId?: string;
  visualAccuracy: VisualAccuracy;
  purchaseConfidence?: number | null;
}

/**
 * Submits a new virtual try-on job for the current user and garment.
 */
export async function submitTryOnJob(
  params: SubmitTryOnParams
): Promise<TryOnJobSubmissionResponse> {
  const idempotencyKey =
    params.idempotencyKey ||
    `tryon-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

  return api<TryOnJobSubmissionResponse>("/tryon/jobs", {
    method: "POST",
    idempotencyKey,
    body: JSON.stringify({
      garment_id: params.garmentId,
      render_config: params.renderConfig,
    }),
  });
}

/**
 * Retrieves the status and output artifact URL for a try-on job.
 */
export async function getTryOnJob(jobId: string): Promise<TryOnJobStatusResponse> {
  return api<TryOnJobStatusResponse>(`/tryon/jobs/${encodeURIComponent(jobId)}`);
}

export async function cancelTryOnJob(jobId: string): Promise<TryOnJobStatusResponse> {
  return api<TryOnJobStatusResponse>(`/tryon/jobs/${encodeURIComponent(jobId)}/cancel`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

/**
 * Lists the user's historical virtual try-on jobs.
 */
export async function listTryOnJobs(limit = 50): Promise<TryOnJobListItem[]> {
  return api<TryOnJobListItem[]>(`/tryon/jobs?limit=${limit}`);
}

export interface TryOnArtifactResponse {
  artifact_key: string;
  result_key: string;
  model_version: string;
  pipeline_version: string;
  photo_version: number;
  garment_version: number;
  quality_reasons: string[];
}

/**
 * Fetches an artifact metadata by its deterministic composite key.
 * Enforces ownership and active consent on the backend (403 forbidden if not owner).
 */
export async function getTryOnArtifact(
  artifactKey: string
): Promise<TryOnArtifactResponse> {
  return api<TryOnArtifactResponse>(
    `/tryon/artifacts/${encodeURIComponent(artifactKey)}`
  );
}

/**
 * Submits post-try-on visual accuracy and purchase confidence feedback.
 */
export interface ReportMisleadingTryOnParams {
  jobId: string;
  reasonCode: string;
  details?: string;
  includeInQualityReview: boolean;
}

export interface ReportMisleadingTryOnResponse {
  feedback_id: string;
  job_id: string;
  user_id: string;
  reason_code: string;
  status: string;
  include_in_quality_review: boolean;
  message: string;
  created_at: string;
}

export interface TryOnPresentationPolicyResponse {
  presentation: {
    result_type: string;
    is_ai_generated: boolean;
    fit_verified: boolean;
    fit_prediction_id: string | null;
    disclaimer_code: string;
    fit_recommendation_available: boolean;
    fit_guaranteed: boolean;
    policy_version: string;
    copy: Record<string, string>;
  };
}

/**
 * Reports an inaccurate, distorted, or misleading Virtual Try-On result (Phase 07.8).
 */
export async function reportMisleadingTryOn(
  params: ReportMisleadingTryOnParams
): Promise<ReportMisleadingTryOnResponse> {
  return api<ReportMisleadingTryOnResponse>(`/tryon/jobs/${params.jobId}/feedback`, {
    method: "POST",
    body: JSON.stringify({
      reason_code: params.reasonCode,
      details: params.details,
      include_in_quality_review: params.includeInQualityReview,
    }),
  });
}

/**
 * Retrieves the server-authoritative presentation policy and disclosures (Phase 07.8).
 */
export async function getTryOnPresentationPolicy(
  fitRecommendationAvailable = false
): Promise<TryOnPresentationPolicyResponse> {
  return api<TryOnPresentationPolicyResponse>(
    `/tryon/presentation-policy?fit_recommendation_available=${fitRecommendationAvailable}`
  );
}

