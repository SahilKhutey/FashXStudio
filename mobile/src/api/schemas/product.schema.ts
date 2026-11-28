import { z } from "zod";

export const AvailabilityStatusSchema = z.enum([
  "IN_STOCK",
  "OUT_OF_STOCK",
  "UNKNOWN",
  "DISCONTINUED",
  "DELISTED",
  "TAKEDOWN",
  "STALE",
]);

export const ProductSummarySchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  category: z.string(),
  price: z.number().nonnegative().nullable(),
  currency: z.string().length(3),
  availability: AvailabilityStatusSchema,
  imageUrl: z.string().url().nullable(),
});

export type ProductSummary = z.infer<typeof ProductSummarySchema>;
