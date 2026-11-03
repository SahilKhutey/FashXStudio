import * as WebBrowser from "expo-web-browser";
import { useMutation } from "@tanstack/react-query";
import { api } from "../../api/client";
import { isSafeRetailerRedirect } from "../../lib/safeRedirect";

export const useBuy = () =>
  useMutation({
    mutationFn: (garmentId: string) =>
      api<{ redirect_url: string }>("/commerce/buy-clicks", {
        method: "POST",
        body: JSON.stringify({ garment_id: garmentId }),
      }),
    onSuccess: (r) => {
      if (r?.redirect_url && isSafeRetailerRedirect(r.redirect_url)) {
        WebBrowser.openBrowserAsync(r.redirect_url);
      } else if (r?.redirect_url) {
        console.warn("Blocked potentially unsafe redirect URL:", r.redirect_url);
      }
    },
  });
