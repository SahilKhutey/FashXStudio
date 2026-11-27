import { apiClient } from "../../api/client";
import type { FeedbackEventPayload, ReactionState } from "./eventTypes";

export function createFeedbackEventId(): string {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }
  const hex = () => Math.floor(Math.random() * 0xffffffff).toString(16).padStart(8, "0");
  return `${hex()}-${hex().slice(0, 4)}-4${hex().slice(0, 3)}-8${hex().slice(0, 3)}-${hex()}${hex().slice(0, 4)}`;
}

export async function setProductReaction(
  productId: string,
  reaction: ReactionState,
  idempotencyKey = createFeedbackEventId(),
): Promise<{ product_id: string; reaction: ReactionState; status: string }> {
  return apiClient(`/api/v1/products/${encodeURIComponent(productId)}/reaction`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reaction, idempotency_key: idempotencyKey }),
  });
}

export async function saveProduct(
  productId: string,
  merchantOfferId?: string,
  idempotencyKey = createFeedbackEventId(),
): Promise<{ product_id: string; is_saved: boolean }> {
  return apiClient(`/api/v1/products/${encodeURIComponent(productId)}/saved`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      idempotency_key: idempotencyKey,
      merchant_offer_id: merchantOfferId ?? null,
    }),
  });
}

export async function unsaveProduct(
  productId: string,
): Promise<{ product_id: string; is_saved: boolean }> {
  return apiClient(`/api/v1/products/${encodeURIComponent(productId)}/saved`, {
    method: "DELETE",
  });
}

export async function submitFeedbackEvent(
  event: FeedbackEventPayload,
): Promise<{ event_id: string; status: string; deduplicated: boolean }> {
  return apiClient("/api/v1/feedback/events", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(event),
  });
}
