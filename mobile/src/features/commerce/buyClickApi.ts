import { api } from "../../api/client";

export type CreateBuyClickRequest = {
  garment_id: string;
  offer_id: string;
  user_id?: string;
};

export type CreateBuyClickResponse = {
  buy_click_id: string;
  redirect_url: string;
  tracking_id: string;
};

export async function createBuyClick(
  payload: CreateBuyClickRequest
): Promise<CreateBuyClickResponse> {
  return api<CreateBuyClickResponse>("/commerce/buy-clicks", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
