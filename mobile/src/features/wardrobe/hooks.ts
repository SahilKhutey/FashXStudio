import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createSavedLook,
  deleteSavedLook,
  fetchUserWardrobe,
  getSavedLooks,
  removeGarmentFromWardrobe,
  saveGarmentToWardrobe,
  type SaveWardrobeResponse,
  type UserWardrobeItem,
} from "./api";
import type { CreateSavedLookRequest, SavedLook, SavedLooksResponse } from "./types";
import { useAuthStore } from "../auth/authStore";
import { queryKeys } from "../../app-shell/queryKeys";

export type { SaveWardrobeResponse, UserWardrobeItem };

export const wardrobeKeys = {
  items: (userId: string | null) => ["account", userId, "wardrobe", "items"] as const,
  looks: (userId: string | null) => ["account", userId, "wardrobe", "looks"] as const,
  look: (userId: string | null, lookId: string) =>
    ["account", userId, "wardrobe", "look", lookId] as const,
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
    queryKey: queryKeys.wardrobe(me?.user_id ?? null, limit, offset),
    queryFn: async () => {
      return fetchUserWardrobe(limit, offset);
    },
    enabled: Boolean(me?.user_id),
    staleTime: 30 * 1000,
  });
}

export function useSavedLooks() {
  const me = useAuthStore((s) => s.me);

  return useQuery<SavedLooksResponse, Error>({
    queryKey: wardrobeKeys.looks(me?.user_id ?? null),
    queryFn: getSavedLooks,
    enabled: Boolean(me?.user_id),
    staleTime: 30 * 1000,
  });
}

export function useCreateSavedLook() {
  const queryClient = useQueryClient();
  const me = useAuthStore((s) => s.me);

  return useMutation<SavedLook, Error, CreateSavedLookRequest>({
    mutationFn: (request) => createSavedLook(request),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: wardrobeKeys.looks(me?.user_id ?? null),
      });
    },
  });
}

export function useDeleteSavedLook() {
  const queryClient = useQueryClient();
  const me = useAuthStore((s) => s.me);

  return useMutation<void, Error, string>({
    mutationFn: (lookId) => deleteSavedLook(lookId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: wardrobeKeys.looks(me?.user_id ?? null),
      });
    },
  });
}
