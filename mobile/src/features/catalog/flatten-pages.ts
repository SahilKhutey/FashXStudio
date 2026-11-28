import type { ProductSearchItem } from "./catalog.types";

/**
 * Deduplicates paginated search results by product + merchant listing identity
 * so two separate merchant offers for the same canonical product are preserved.
 */
export function flattenSearchPages(
  pages: Array<{ items: ProductSearchItem[] }>,
): ProductSearchItem[] {
  const listings = new Map<string, ProductSearchItem>();
  for (const page of pages) {
    for (const item of page.items) {
      const key = `${item.product_id}:${item.merchant_product_id}`;
      if (!listings.has(key)) {
        listings.set(key, item);
      }
    }
  }
  return Array.from(listings.values());
}
