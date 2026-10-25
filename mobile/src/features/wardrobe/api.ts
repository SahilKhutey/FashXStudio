import { api } from "../../api/client";
import type { components } from "../../api/schema";

export type SaveWardrobeResponse = components["schemas"]["SaveWardrobeResponse"];
export type UserWardrobeItem = components["schemas"]["WardrobeItemView"];

export async function fetchUserWardrobe(userId: string): Promise<UserWardrobeItem[]> {
  if (!userId) return [];
  return api<UserWardrobeItem[]>(`/wardrobe/users/${userId}`);
}

export async function saveGarmentToWardrobe(params: {
  userId: string;
  garmentId: string;
  offerId?: string | null;
  tryonArtifactId?: string | null;
}): Promise<SaveWardrobeResponse> {
  return api<SaveWardrobeResponse>("/wardrobe/items", {
    method: "POST",
    body: JSON.stringify({
      user_id: params.userId,
      garment_id: params.garmentId,
      offer_id: params.offerId ?? null,
      tryon_artifact_id: params.tryonArtifactId ?? null,
    }),
  });
}

export async function removeGarmentFromWardrobe(params: {
  userId: string;
  itemId: string;
}): Promise<void> {
  return api<void>(`/wardrobe/users/${params.userId}/items/${params.itemId}`, {
    method: "DELETE",
  });
}
