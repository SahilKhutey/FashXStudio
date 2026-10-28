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
  return api<TryOnJobStatusResponse>(`/tryon/jobs/${jobId}`);
}

/**
 * Lists the user's historical virtual try-on jobs.
 */
export async function listTryOnJobs(limit = 50): Promise<TryOnJobListItem[]> {
  return api<TryOnJobListItem[]>(`/tryon/jobs?limit=${limit}`);
}

/**
 * Fetches an artifact by its deterministic composite key.
 * Enforces ownership and active consent on the backend (403 forbidden if not owner).
 */
export async function getTryOnArtifact(artifactKey: string): Promise<Response> {
  return fetch(`/tryon/artifacts/${artifactKey}`, {
    method: "GET",
  });
}

/**
 * Submits post-try-on visual accuracy and purchase confidence feedback.
 */
export async function submitTryOnFeedback(
  params: TryOnFeedbackParams
): Promise<{ status: string }> {
  return api<{ status: string }>("/feedback/tryon", {
    method: "POST",
    body: JSON.stringify({
      user_id: params.userId,
      tryon_job_id: params.jobId,
      visual_accuracy: params.visualAccuracy,
      purchase_confidence: params.purchaseConfidence ?? null,
    }),
  });
}
