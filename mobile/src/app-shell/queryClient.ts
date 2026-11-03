import { QueryClient } from "@tanstack/react-query";
import { ApiError } from "../api/errors";

export const queryRetry = (
  failureCount: number,
  error: unknown
): boolean => {
  if (failureCount >= 2) return false;
  if (error instanceof ApiError) {
    return error.isRetryable;
  }
  return false;
};

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: queryRetry,
      staleTime: 60_000,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: false,
    },
  },
});
