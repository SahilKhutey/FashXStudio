import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import { components } from "../../api/schema";
import { useAuthStore } from "../auth/authStore";

export type SaveWardrobeResponse = components["schemas"]["SaveWardrobeResponse"];
export type UserWardrobeItem = components["schemas"]["WardrobeItemView"];
export type FitVerdict = "too_tight" | "true_to_size" | "too_loose";

export interface ClosetItem {
  id: string;
  item_id?: string;
  user_id: string;
  garment_id: string;
  title_at_save: string;
  price_at_save: number;
  currency: string;
  saved_at: string;
  purchased_at?: string | null;
  fit_feedback_given?: boolean;
  current_price?: number | null;
  render?: { url: string; expires_at: number } | null;
  snapshot_title?: string;
  snapshot_price_minor?: number;
  snapshot_currency?: string;
  snapshot_image_key?: string;
  tryon_artifact_id?: string | null;
}

export const useCloset = (userId?: string) =>
  useQuery({
    queryKey: ["closet", userId],
    enabled: !!userId,
    queryFn: () => api<ClosetItem[]>(`/wardrobe/users/${userId}`),
  });

export const useRemoveItem = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api(`/wardrobe/items/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["closet"] });
      qc.invalidateQueries({ queryKey: ["wardrobe"] });
    },
  });
};

export const useMarkPurchased = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api(`/wardrobe/items/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ purchased: true }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["closet"] });
      qc.invalidateQueries({ queryKey: ["wardrobe"] });
    },
  });
};

export const useFitFeedback = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (b: { item_id: string; verdict: FitVerdict }) =>
      api("/feedback/fit", { method: "POST", body: JSON.stringify(b) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["closet"] });
      qc.invalidateQueries({ queryKey: ["wardrobe"] });
    },
  });
};

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
      queryClient.invalidateQueries({ queryKey: ["closet"] });
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
  });
}
