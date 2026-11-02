import { useMutation } from "@tanstack/react-query";
import {
  createBuyClick,
  type CreateBuyClickParams,
} from "./commerceApi";

export function useCreateBuyClick() {
  return useMutation({
    mutationFn: (params: CreateBuyClickParams) =>
      createBuyClick(params),
    retry: false,
  });
}
