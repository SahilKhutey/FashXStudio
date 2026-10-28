import { api } from "../../api/client";

export interface UserWardrobeItem {
  item_id: string;
  user_id: string;
  garment_id: string;
  snapshot_title: string;
  snapshot_price_minor: number;
  snapshot_currency: string;
  snapshot_image_key: string;
  image_url?: string | null;
  tryon_artifact_id?: string | null;
  saved_at: string;
}

export interface SaveWardrobeResponse {
  item_id: string;
  user_id: string;
  garment_id: string;
  snapshot_title: string;
  snapshot_price_minor: number;
  snapshot_currency: string;
  snapshot_image_key: string;
  image_url?: string | null;
  tryon_artifact_id?: string | null;
}

export async function fetchUserWardrobe(
  limit = 50,
  offset = 0
): Promise<UserWardrobeItem[]> {
  return api<UserWardrobeItem[]>(`/wardrobe/items?limit=${limit}&offset=${offset}`);
}

export async function saveGarmentToWardrobe(params: {
  garmentId: string;
  offerId?: string | null;
  tryonArtifactId?: string | null;
  userId?: string | null;
}): Promise<SaveWardrobeResponse> {
  return api<SaveWardrobeResponse>("/wardrobe/items", {
    method: "POST",
    body: JSON.stringify({
      garment_id: params.garmentId,
      offer_id: params.offerId ?? null,
      tryon_artifact_id: params.tryonArtifactId ?? null,
    }),
  });
}

export async function removeGarmentFromWardrobe(itemId: string): Promise<void> {
  return api<void>(`/wardrobe/items/${itemId}`, {
    method: "DELETE",
  });
}
