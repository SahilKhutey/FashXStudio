import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchUserWardrobe,
  removeGarmentFromWardrobe,
  saveGarmentToWardrobe,
  type SaveWardrobeResponse,
  type UserWardrobeItem,
} from "./api";
import { useAuthStore } from "../auth/authStore";

export type { SaveWardrobeResponse, UserWardrobeItem };

export function useSaveToWardrobe() {
  const queryClient = useQueryClient();
  const me = useAuthStore((s) => s.me);

  return useMutation({
    mutationFn: async ({
      garmentId,
      offerId,
      tryonArtifactId,
    }: {
      garmentId: string;
      offerId?: string | null;
      tryonArtifactId?: string | null;
    }) => {
      return saveGarmentToWardrobe({
        garmentId,
        offerId,
        tryonArtifactId,
        userId: me?.user_id,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wardrobe"] });
    },
  });
}

export function useRemoveFromWardrobe() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (itemId: string) => {
      return removeGarmentFromWardrobe(itemId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wardrobe"] });
    },
  });
}

export function useUserWardrobe(limit = 50, offset = 0) {
  const me = useAuthStore((s) => s.me);

  return useQuery<UserWardrobeItem[], Error>({
    queryKey: ["wardrobe", me?.user_id, limit, offset],
    queryFn: async () => {
      return fetchUserWardrobe(limit, offset);
    },
    enabled: Boolean(me?.user_id),
    staleTime: 30 * 1000,
  });
}
