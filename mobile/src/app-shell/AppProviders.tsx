import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppStatusBar } from "./AppStatusBar";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error: any) => {
        // Automatically retry up to 2 times for network or 5xx errors on idempotent GETs
        if (failureCount >= 2) return false;
        if (error?.status && error.status >= 400 && error.status < 500) {
          return false;
        }
        return true;
      },
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
