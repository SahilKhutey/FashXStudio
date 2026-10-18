import { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import { components } from "../../api/schema";
import { useAuthStore } from "../auth/authStore";

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

export function useJob(jobId: string | null) {
  const [pollCount, setPollCount] = useState(0);
  const startTimeRef = useRef<number>(Date.now());
  const [isTakingLongerThanUsual, setIsTakingLongerThanUsual] = useState(false);

  useEffect(() => {
    startTimeRef.current = Date.now();
    setPollCount(0);
    setIsTakingLongerThanUsual(false);
  }, [jobId]);

  const query = useQuery<TryOnJobStatusResponse, Error>({
    queryKey: ["tryon", "job", jobId],
    queryFn: async () => {
      const res = await api<TryOnJobStatusResponse>(`/tryon/jobs/${jobId}`);
      setPollCount((prev) => prev + 1);

      // Check if elapsed time exceeds 120 seconds (2 minutes)
      const elapsed = (Date.now() - startTimeRef.current) / 1000;
      if (elapsed >= 120 && res.status !== "completed" && res.status !== "failed" && res.status !== "cancelled") {
        setIsTakingLongerThanUsual(true);
      }

      return res;
    },
    enabled: !!jobId,
    refetchInterval: (q) => {
      const status = q.state.data?.status;
      if (status === "completed" || status === "failed" || status === "cancelled") {
        return false;
      }
      // Exponential backoff: 1s -> 2s -> 4s -> 5s (capped at 5s)
      const backoffMs = Math.min(1000 * Math.pow(2, pollCount), 5000);
      return backoffMs;
    },
    refetchIntervalInBackground: true,
  });

  return {
    ...query,
    isTakingLongerThanUsual,
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
