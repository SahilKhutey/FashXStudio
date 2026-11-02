import { api } from "../../api/client";

export interface BuyClickResponse {
  buy_click_id: string;
  redirect_url: string;
  tracking_id: string;
}

export interface CreateBuyClickParams {
  garmentId: string;
  offerId: string;
}

export async function createBuyClick(
  params: CreateBuyClickParams
): Promise<BuyClickResponse> {
  return api<BuyClickResponse>("/commerce/buy-clicks", {
    method: "POST",
    body: JSON.stringify({
      garment_id: params.garmentId,
      offer_id: params.offerId,
    }),
  });
}
