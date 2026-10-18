import { useQuery } from "@tanstack/react-query";
import { api } from "./client";
import { UserMe, useAuthStore } from "../features/auth/authStore";

export interface RemoteConfigResponse {
  min_app_version: string;
  maintenance: boolean;
  tryon_supported_categories: string[];
  consent_version: string;
  legal?: {
    privacy_url: string | null;
    terms_url: string | null;
  };
  flags?: {
    tryon: boolean;
  };
}

export function useConfig() {
  return useQuery({
    queryKey: ["config"],
    queryFn: () => api<RemoteConfigResponse>("/config"),
    staleTime: 5 * 60 * 1000,
  });
}

export function useMe(enabled = true) {
  const hasSession = useAuthStore((s) => s.hasSession);
  return useQuery({
    queryKey: ["me"],
    queryFn: () => api<UserMe>("/me"),
    enabled: enabled && hasSession,
    staleTime: 30 * 1000,
  });
}
