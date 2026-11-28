import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "../../api/errors";
import { fetchProductDetail, requestMerchantRedirect } from "./api";
import { useSaveToWardrobe } from "../wardrobe/hooks";

export const productDetailKey = (productId: string, offerId: string) =>
  ["product-detail", productId, offerId] as const;

export function useProductDetail(productId?: string, offerId?: string) {
  return useQuery({
    queryKey: productDetailKey(productId ?? "", offerId ?? ""),
    queryFn: () => fetchProductDetail(productId!, offerId!),
    enabled: Boolean(productId && offerId),
    staleTime: 30_000,
    gcTime: 5 * 60_000,
    retry: (failureCount, error: unknown) => {
      if (
        error instanceof ApiError &&
        (error.status === 404 || error.status === 403)
      ) {
        return false;
      }
      return failureCount < 2;
    },
  });
}

export function useSaveProduct() {
  const save = useSaveToWardrobe();

  return useMutation({
    mutationFn: ({
      garmentId,
      offerId,
    }: {
      garmentId: string;
      offerId: string;
    }) => save.mutateAsync({ garmentId, offerId }),
  });
}

export function useMerchantRedirect() {
  return useMutation({
    mutationFn: requestMerchantRedirect,
  });
}

export function useRefreshProductDetail() {
  const client = useQueryClient();

  return (productId: string, offerId: string) =>
    client.invalidateQueries({
      queryKey: productDetailKey(productId, offerId),
    });
}
