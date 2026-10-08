import { apiRequest } from "./client";

export type FeedProduct = {
  id: string;
  display_name: string;
  category: string;
  subcategory?: string | null;
  brand_id?: string | null;
  version: number;
  primary_image_key?: string | null;
  lowest_price_minor?: number | null;
  currency?: string | null;
  in_stock: boolean;
};

export type FeedItem = {
  product: FeedProduct;
  reasons: string[];
};

export type FeedResponse = {
  items: FeedItem[];
  next_cursor?: string | null;
};

export type FeedParams = {
  category?: string;
  subcategory?: string;
  priceMin?: number;
  priceMax?: number;
  limit?: number;
  cursor?: string;
};

export async function getFeed(params: FeedParams = {}): Promise<FeedResponse> {
  const query = new URLSearchParams();
  if (params.category) query.set("category", params.category);
  if (params.subcategory) query.set("subcategory", params.subcategory);
  if (params.priceMin !== undefined) query.set("price_min", String(params.priceMin));
  if (params.priceMax !== undefined) query.set("price_max", String(params.priceMax));
  query.set("limit", String(params.limit ?? 20));
  if (params.cursor) query.set("cursor", params.cursor);
  return apiRequest<FeedResponse>(`/feed/me?${query.toString()}`);
}
