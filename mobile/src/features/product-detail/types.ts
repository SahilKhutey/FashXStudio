export type ProductAvailability =
  | "in_stock"
  | "low_stock"
  | "out_of_stock"
  | "pre_order"
  | "unknown"
  | "stale"
  | "delisted"
  | "taken_down";

export type AttributeSource =
  | "merchant"
  | "source_feed"
  | "ai_enriched"
  | "platform_verified";

export interface ProductImage {
  id: string;
  url: string;
  alt_text: string;
  position: number;
  is_primary: boolean;
}

export interface ProductVariant {
  id: string;
  size_label: string;
  color_label?: string | null;
  availability: ProductAvailability;
}

export interface ProductAttribute {
  key: string;
  label: string;
  value: string;
  source: AttributeSource;
  confidence?: number | null;
}

export interface ProductDetail {
  product_id: string;
  garment_id: string;
  merchant_product_id: string;
  offer_id: string;
  title: string;
  description?: string | null;
  brand: {
    id: string | null;
    name: string | null;
  };
  merchant: {
    id: string;
    name: string;
    website: string | null;
  };
  price: {
    amount_minor: number;
    currency: string;
    original_amount_minor?: number | null;
    last_verified_at?: string | null;
  };
  availability: ProductAvailability;
  availability_checked_at?: string | null;
  images: ProductImage[];
  variants: ProductVariant[];
  attributes: ProductAttribute[];
  size_chart: {
    available: boolean;
    chart_id?: string | null;
    chart_revision?: number | null;
    basis?: "body" | "garment" | null;
    source_name?: string | null;
  };
  permissions: {
    display_allowed: boolean;
    vto_allowed: boolean;
    redirect_allowed: boolean;
  };
  listing: {
    product_url_status: "valid" | "expired" | "unknown";
    last_seen_at?: string | null;
    last_verified_at?: string | null;
  };
  saved: boolean;
}

export interface MerchantRedirectResponse {
  redirect_url: string;
  expires_at?: string | null;
}
