/**
 * Adaptive Try-On Polling Hook (TanStack Query v5)
 * Schedules polling: 0-10s -> 2s, 10-30s -> 3s, 30s+ -> 5s.
 */

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/api/client";

export interface TryOnJobStatusResponse {
  job_id: string;
  status: "queued" | "preprocessing" | "diffusion_inference" | "completed" | "failed" | "cancelled";
  result_image_url?: string;
  error_code?: string;
  error_message?: string;
  completed_at?: string;
}

export function useTryOnJob(jobId: string | null, startTimeMs: number = Date.now()) {
  return useQuery<TryOnJobStatusResponse>({
    queryKey: ["tryon_job", jobId],
    queryFn: () => apiClient<TryOnJobStatusResponse>(`/api/v1/try-on/${jobId}`),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 2000;

      // Stop polling on terminal states
      if (data.status === "completed" || data.status === "failed" || data.status === "cancelled") {
        return false;
      }

      const elapsedSec = (Date.now() - startTimeMs) / 1000;
      if (elapsedSec < 10) return 2000;
      if (elapsedSec < 30) return 3000;
      return 5000;
    },
    refetchIntervalInBackground: false,
  });
}
