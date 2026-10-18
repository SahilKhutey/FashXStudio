import * as WebBrowser from "expo-web-browser";
import { useMutation } from "@tanstack/react-query";
import { api } from "../../api/client";

export const useBuy = () =>
  useMutation({
    mutationFn: (garmentId: string) =>
      api<{ redirect_url: string }>("/commerce/buy-clicks", {
        method: "POST",
        body: JSON.stringify({ garment_id: garmentId }),
      }),
    onSuccess: (r) => {
      if (r?.redirect_url) {
        WebBrowser.openBrowserAsync(r.redirect_url);
      }
    },
  });
