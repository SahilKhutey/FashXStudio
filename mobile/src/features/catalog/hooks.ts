import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";
import { components } from "../../api/schema";

export type CustomerGarmentDetailResponse =
  components["schemas"]["CustomerGarmentDetailResponse"];

export function useGarmentDetail(garmentId: string) {
  return useQuery<CustomerGarmentDetailResponse, Error>({
    queryKey: ["garment", garmentId],
    queryFn: async () => {
      return api<CustomerGarmentDetailResponse>(`/garments/${garmentId}`);
    },
    enabled: !!garmentId,
    staleTime: 5 * 60 * 1000,
  });
}
