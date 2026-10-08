import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getCatalogDetail, rejectCatalogItem, saveCatalogItem } from "../../api/catalog";

export function useProductDetail(productId: string, offerId?: string) {
  return useQuery({
    queryKey: ["catalog-detail", productId, offerId ?? null],
    queryFn: () => getCatalogDetail(productId, offerId),
    enabled: Boolean(productId),
    staleTime: 30_000,
  });
}

export function useCatalogActions(productId: string) {
  const queryClient = useQueryClient();
  const save = useMutation({
    mutationFn: (offerId?: string) => saveCatalogItem(productId, offerId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["catalog-detail", productId] });
    },
  });
  const reject = useMutation({
    mutationFn: () => rejectCatalogItem(productId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["feed"] });
    },
  });

  return { save, reject };
}
