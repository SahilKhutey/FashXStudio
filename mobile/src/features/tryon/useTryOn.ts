import { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import { components } from "../../api/schema";
import { useAuthStore } from "../auth/authStore";
import { getTryOnPollInterval } from "./polling";

export type TryOnJobStatusResponse = components["schemas"]["TryOnJobStatusResponse"];
export type TryOnJobSubmissionResponse = components["schemas"]["TryOnJobSubmissionResponse"];
export type TryOnJobListItem = components["schemas"]["TryOnJobListItem"];
export type VisualAccuracy = components["schemas"]["VisualAccuracy"];

export function ratingToVisualAccuracy(rating: number): VisualAccuracy {
  if (rating <= 1) return "very_inaccurate";
  if (rating === 2) return "inaccurate";
  if (rating === 3) return "neutral";
  if (rating === 4) return "accurate";
  return "very_accurate";
}

export function useStartTryOn() {
  const queryClient = useQueryClient();
  const idempotencyKeyRef = useRef<string>(
    `tryon-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
  );

  return useMutation({
    mutationFn: async ({ garmentId }: { garmentId: string }) => {
      return api<TryOnJobSubmissionResponse>("/tryon/jobs", {
        method: "POST",
        idempotencyKey: idempotencyKeyRef.current,
        body: JSON.stringify({
          garment_id: garmentId,
        }),
      });
    },
    onSuccess: () => {
      // Refresh the tryon jobs list
      queryClient.invalidateQueries({ queryKey: ["tryon", "jobs"] });
      // Reset idempotency key for next run
      idempotencyKeyRef.current = `tryon-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    },
  });
}

export function useRetryTryOn() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ garmentId }: { garmentId: string }) => {
      const idempotencyKey = `tryon-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

      return api<TryOnJobSubmissionResponse>("/tryon/jobs", {
        method: "POST",
        idempotencyKey,
        body: JSON.stringify({
          garment_id: garmentId,
        }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["tryon", "jobs"],
      });
    },
  });
}

export function useJob(jobId: string | null, isFocused = true) {
  const [startedAt, setStartedAt] = useState(Date.now());

  useEffect(() => {
    setStartedAt(Date.now());
  }, [jobId]);

  const query = useQuery<TryOnJobStatusResponse, Error>({
    queryKey: ["tryon", "job", jobId],
    queryFn: async () => {
      if (!jobId) throw new Error("Missing try-on job ID");
      return api<TryOnJobStatusResponse>(
        `/tryon/jobs/${encodeURIComponent(jobId)}`
      );
    },
    enabled: Boolean(jobId && isFocused),
    staleTime: 0,
    refetchOnMount: "always",
    refetchOnReconnect: true,
    refetchOnWindowFocus: true,
    refetchInterval: (q) =>
      getTryOnPollInterval(Date.now() - startedAt, q.state.data?.status),
    refetchIntervalInBackground: false,
    retry: 2,
  });

  const elapsedMs = Date.now() - startedAt;

  return {
    ...query,
    isTakingLongerThanUsual: elapsedMs >= 120_000,
    refreshJob: query.refetch,
  };
}

export function useTryOnJobs(limit = 50) {
  return useQuery<TryOnJobListItem[], Error>({
    queryKey: ["tryon", "jobs", limit],
    queryFn: async () => {
      return api<TryOnJobListItem[]>(`/tryon/jobs?limit=${limit}`);
    },
    staleTime: 15 * 1000,
  });
}

export function useTryOnFeedback() {
  const me = useAuthStore((s) => s.me);

  return useMutation({
    mutationFn: async ({
      jobId,
      rating,
      purchaseConfidence,
    }: {
      jobId: string;
      rating: number;
      purchaseConfidence?: number;
    }) => {
      const visualAccuracy = ratingToVisualAccuracy(rating);
      return api<{ status: string }>("/feedback/tryon", {
        method: "POST",
        body: JSON.stringify({
          user_id: me?.user_id,
          tryon_job_id: jobId,
          visual_accuracy: visualAccuracy,
          purchase_confidence: purchaseConfidence ?? null,
        }),
      });
    },
  });
}
