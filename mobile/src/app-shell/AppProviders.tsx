import React from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { AppStatusBar } from "./AppStatusBar";
import { queryClient } from "./queryClient";

export { queryClient } from "./queryClient";
export { queryRetry } from "./queryClient";

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
