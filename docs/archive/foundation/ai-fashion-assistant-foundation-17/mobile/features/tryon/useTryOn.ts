import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { cancelTryOn, createTryOn, getTryOnStatus, recordTryOnTelemetry, submitTryOnFeedback } from "../../api/tryon";

function newIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `tryon-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export function useCreateTryOn(productId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => createTryOn(productId, newIdempotencyKey()),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ["tryon", data.job_id] });
    },
  });
}

export function useTryOnJob(jobId: string | null) {
  return useQuery({
    queryKey: ["tryon", jobId],
    queryFn: () => getTryOnStatus(jobId as string),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "completed" || status === "failed" || status === "cancelled") return false;
      if (status === "inference" || status === "preprocessing" || status === "postprocessing") return 2000;
      return 1500;
    },
  });
}

export function useCancelTryOn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => cancelTryOn(jobId),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ["tryon", data.job_id] });
    },
  });
}


export function useTryOnFeedback() {
  return useMutation({
    mutationFn: submitTryOnFeedback,
  });
}

export function useTryOnTelemetry() {
  return useMutation({
    mutationFn: ({ jobId, event, elapsed_ms, screen_context }: {
      jobId: string;
      event: "viewed" | "retry_requested";
      elapsed_ms?: number;
      screen_context?: string;
    }) => recordTryOnTelemetry(jobId, event, { elapsed_ms, screen_context }),
  });
}
