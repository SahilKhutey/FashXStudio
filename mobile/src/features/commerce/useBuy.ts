import { useMutation } from "@tanstack/react-query";
import * as Linking from "expo-linking";
import * as WebBrowser from "expo-web-browser";
import { createBuyClick, type CreateBuyClickRequest } from "./buyClickApi";
import { isSafeRetailerRedirect } from "../../lib/safeRedirect";

export function useBuy() {
  return useMutation({
    mutationFn: async (payload: CreateBuyClickRequest) => {
      const result = await createBuyClick(payload);
      if (!result?.redirect_url || !isSafeRetailerRedirect(result.redirect_url)) {
        throw new Error("The retailer destination could not be verified.");
      }
      return result;
    },
    onSuccess: async (result) => {
      const url = result.redirect_url;
      try {
        const canOpen = await Linking.canOpenURL(url);
        if (canOpen) {
          await Linking.openURL(url);
        } else {
          await WebBrowser.openBrowserAsync(url);
        }
      } catch {
        await WebBrowser.openBrowserAsync(url);
      }
    },
  });
}
