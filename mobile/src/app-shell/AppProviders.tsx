import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppStatusBar } from "./AppStatusBar";
import { ApiError } from "../api/errors";

export const queryRetry = (
  failureCount: number,
  error: unknown,
): boolean => {
  if (failureCount >= 2) return false;
  if (error instanceof ApiError) {
    return error.isRetryable;
  }
  // Unknown errors are not automatically assumed to be transient.
  return false;
};

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: queryRetry,
      staleTime: 60_000,
    },
    mutations: {
      retry: false,
    },
  },
});

type AppProvidersProps = {
  children: React.ReactNode;
};

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <QueryClientProvider client={queryClient}>
      <AppStatusBar />
      {children}
    </QueryClientProvider>
  );
}
