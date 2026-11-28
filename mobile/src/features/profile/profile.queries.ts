import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { profileApi } from "./services/profileApi";
import type { ShopperProfile, ShopperProfileUpdate } from "./types/profile.types";

export const profileKeys = {
  all: ["profile"] as const,
  me: () => ["profile", "me"] as const,
};

export function useMyProfile(enabled = true) {
  return useQuery<ShopperProfile>({
    queryKey: profileKeys.me(),
    queryFn: () => profileApi.getProfile(),
    staleTime: 60_000,
    enabled,
  });
}

export function useSaveMyProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ShopperProfileUpdate) => profileApi.updateProfile(payload),
    onSuccess: (savedProfile) => {
      queryClient.setQueryData(profileKeys.me(), savedProfile);
      void queryClient.invalidateQueries({ queryKey: ["fit"] });
      void queryClient.invalidateQueries({ queryKey: ["ranking"] });
    },
  });
}
