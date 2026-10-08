import { apiRequest } from "./client";

export type CatalogImage = {
  id: string;
  image_type: string;
  url?: string | null;
  version: number;
};

export type CatalogOffer = {
  id: string;
  merchant_id: string;
  source_product_id: string;
  url: string;
  price_minor: number;
  currency: string;
  in_stock: boolean;
  selected: boolean;
};

export type CatalogDetail = {
  garment: {
    id: string;
    brand_id?: string | null;
    display_name: string;
    category: string;
    subcategory?: string | null;
    version: number;
  };
  images: CatalogImage[];
  offers: CatalogOffer[];
  enrichment?: Record<string, unknown> | null;
  selected_offer_id?: string | null;
};

export async function getCatalogDetail(productId: string, offerId?: string): Promise<CatalogDetail> {
  const query = offerId ? `?offer_id=${encodeURIComponent(offerId)}` : "";
  return apiRequest<CatalogDetail>(`/catalog/${encodeURIComponent(productId)}${query}`);
}

export async function saveCatalogItem(productId: string, offerId?: string): Promise<{
  wardrobe_item_id: string;
  garment_id: string;
  offer_id?: string | null;
  already_saved: boolean;
}> {
  return apiRequest(`/wardrobe/save/${encodeURIComponent(productId)}`, {
    method: "POST",
    body: JSON.stringify({ offer_id: offerId }),
  });
}

export async function rejectCatalogItem(productId: string): Promise<{ garment_id: string; rejected: boolean }> {
  return apiRequest(`/wardrobe/reject/${encodeURIComponent(productId)}`, {
    method: "POST",
  });
}
