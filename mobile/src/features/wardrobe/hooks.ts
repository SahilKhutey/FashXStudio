import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import { components } from "../../api/schema";
import { useAuthStore } from "../auth/authStore";

export type SaveWardrobeResponse = components["schemas"]["SaveWardrobeResponse"];
export type UserWardrobeItem = components["schemas"]["WardrobeItemView"];

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
      return api<SaveWardrobeResponse>("/wardrobe/items", {
        method: "POST",
        body: JSON.stringify({
          user_id: me.user_id,
          garment_id: garmentId,
          offer_id: offerId ?? null,
          tryon_artifact_id: tryonArtifactId ?? null,
        }),
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
      return api<UserWardrobeItem[]>(`/wardrobe/users/${me.user_id}`);
    },
    enabled: !!me?.user_id,
    staleTime: 30 * 1000,
  });
}
