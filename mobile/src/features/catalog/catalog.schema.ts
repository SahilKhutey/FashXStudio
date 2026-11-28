import { z } from "zod";

export const SearchBrandSchema = z.object({
  id: z.string().nullable().optional().default(null),
  name: z.string(),
});

export const SearchPriceSchema = z.object({
  amount: z.union([z.string(), z.number()]),
  currency: z.string().length(3),
  original_amount: z.union([z.string(), z.number()]).nullable().optional(),
});

export const ProductSearchItemSchema = z.object({
  product_id: z.string().min(1),
  merchant_product_id: z.string().min(1),
  title: z.string().min(1),
  brand: SearchBrandSchema,
  price: SearchPriceSchema,
  availability: z.string(),
  matched_attributes: z.array(z.string()).default([]),
  primary_image_url: z.string().url().nullable().optional().default(null),
  similarity_score: z.number().nullable().optional(),
});

export const ProductSearchResponseSchema = z.object({
  search_id: z.string(),
  query: z.string().nullable().optional().default(null),
  items: z.array(ProductSearchItemSchema),
  total: z.number().int().nonnegative().default(0),
  next_cursor: z.string().nullable().optional().default(null),
  applied_filters: z.record(z.string(), z.unknown()).default({}),
  suggestions: z.array(z.string()).default([]),
  facets: z.record(z.string(), z.unknown()).default({}),
  sort: z.string().default("relevance"),
});
