import { apiRequest } from "./client";

export type TryOnStatus =
  | "queued"
  | "validating"
  | "preprocessing"
  | "inference"
  | "postprocessing"
  | "quality_check"
  | "completed"
  | "failed"
  | "cancelled";

export type TryOnFailureReason =
  | "bad_input_photo"
  | "unsupported_garment"
  | "model_error"
  | "gpu_unavailable"
  | "timeout"
  | "storage_error"
  | "quality_rejected"
  | "internal_error";

export type TryOnResult = {
  artifact_id?: string | null;
  quality_status: string;
  quality_score?: number | null;
  width?: number | null;
  height?: number | null;
  size_bytes?: number | null;
  content_type?: string | null;
  content_sha256?: string | null;
  quality_reasons: string[];
  result_url?: string | null;
};

export type TryOnJob = {
  job_id: string;
  status: TryOnStatus;
  result_url?: string | null;
  failure_reason?: TryOnFailureReason | null;
  model_version: string;
  pipeline_version: string;
  attempt_count: number;
  result?: TryOnResult | null;
};

export type TryOnCreateResponse = {
  job_id: string;
  status: TryOnStatus;
  cache_hit: boolean;
  result_url?: string | null;
};

export async function createTryOn(productId: string, idempotencyKey: string): Promise<TryOnCreateResponse> {
  return apiRequest<TryOnCreateResponse>("/tryon", {
    method: "POST",
    headers: { "Idempotency-Key": idempotencyKey },
    body: JSON.stringify({ product_id: productId }),
  });
}

export async function getTryOnStatus(jobId: string): Promise<TryOnJob> {
  return apiRequest<TryOnJob>(`/tryon/${encodeURIComponent(jobId)}`);
}

export async function cancelTryOn(jobId: string): Promise<{ job_id: string; status: TryOnStatus }> {
  return apiRequest(`/tryon/${encodeURIComponent(jobId)}/cancel`, { method: "POST" });
}
