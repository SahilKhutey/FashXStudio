import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchUserWardrobe,
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
      if (!me?.user_id) {
        throw new Error("User session required to save to wardrobe");
      }
      return saveGarmentToWardrobe({
        userId: me.user_id,
        garmentId,
        offerId,
        tryonArtifactId,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wardrobe"] });
    },
  });
}

export function useUserWardrobe() {
  const me = useAuthStore((s) => s.me);

  return useQuery<UserWardrobeItem[], Error>({
    queryKey: ["wardrobe", me?.user_id],
    queryFn: async () => {
      if (!me?.user_id) return [];
      return fetchUserWardrobe(me.user_id);
    },
    enabled: !!me?.user_id,
    staleTime: 30 * 1000,
  });
}
