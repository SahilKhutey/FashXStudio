import type { ProductAvailability } from "../types";

export function availabilityMessage(state: ProductAvailability): string {
  switch (state) {
    case "in_stock":
      return "In stock";
    case "low_stock":
      return "Limited availability";
    case "out_of_stock":
      return "Currently out of stock";
    case "pre_order":
      return "Available for pre-order";
    case "stale":
      return "Availability needs to be refreshed";
    case "delisted":
      return "This merchant listing is no longer available";
    case "taken_down":
      return "This product has been removed";
    default:
      return "Availability not confirmed";
  }
}

export function canPurchase(state: ProductAvailability): boolean {
  return state === "in_stock" || state === "low_stock";
}
