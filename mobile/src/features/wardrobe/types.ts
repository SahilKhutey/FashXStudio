export type WardrobeItemType = "PRODUCT" | "VTO_RESULT";

export interface SavedLook {
  id: string;
  title: string;
  description?: string | null;
  item_count: number;
  cover_image_url?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SavedLooksResponse {
  looks: SavedLook[];
  next_cursor: string | null;
}

export interface CreateSavedLookRequest {
  title: string;
  description?: string;
  item_ids: string[];
}
