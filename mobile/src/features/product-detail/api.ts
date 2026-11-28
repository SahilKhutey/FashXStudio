import { api } from "../../api/client";
import type { MerchantRedirectResponse, ProductDetail } from "./types";

export async function fetchProductDetail(
  productId: string,
  offerId: string,
): Promise<ProductDetail> {
  const query = `?offer_id=${encodeURIComponent(offerId)}`;
  return api<ProductDetail>(
    `/catalog/products/${encodeURIComponent(productId)}/detail${query}`,
    { method: "GET" },
  );
}

export async function requestMerchantRedirect(
  offerId: string,
): Promise<MerchantRedirectResponse> {
  return api<MerchantRedirectResponse>(
    `/catalog/offers/${encodeURIComponent(offerId)}/redirect`,
    {
      method: "POST",
      body: JSON.stringify({}),
    },
  );
}

export async function fetchProductSizeChart(
  productId: string,
  offerId: string,
): Promise<unknown> {
  const query = `?offer_id=${encodeURIComponent(offerId)}`;
  return api(
    `/catalog/products/${encodeURIComponent(productId)}/size-chart${query}`,
    { method: "GET" },
  );
}
