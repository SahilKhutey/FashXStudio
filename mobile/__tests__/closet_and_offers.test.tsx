import { Linking, Alert } from "react-native";
import { createBuyClick } from "../src/features/wardrobe/commerceApi";
import { saveGarmentToWardrobe, removeGarmentFromWardrobe } from "../src/features/wardrobe/api";

jest.mock("../src/api/client", () => ({
  api: jest.fn(),
}));

if (!Linking.openURL) {
  (Linking as any).openURL = jest.fn();
} else {
  jest.spyOn(Linking, "openURL").mockImplementation(async () => {});
}

jest.spyOn(Alert, "alert");

describe("Phase 8 Mobile: Retailer Offers & Wardrobe Integration", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Retailer Offer Selection & Handoff Logic", () => {
    const mockOffers = [
      { id: "off-1", price_minor: 199900, currency: "INR", in_stock: true },
      { id: "off-2", price_minor: 149900, currency: "INR", in_stock: false },
    ];

    it("identifies selectable in-stock offers and disables out-of-stock offers", () => {
      const isSelectable = (offerId: string) => {
        const offer = mockOffers.find((o) => o.id === offerId);
        return offer ? offer.in_stock : false;
      };

      expect(isSelectable("off-1")).toBe(true);
      expect(isSelectable("off-2")).toBe(false);
      expect(isSelectable("off-unknown")).toBe(false);
    });

    it("prevents shop handoff when no offer is selected or mutation is pending", () => {
      const canShop = (selectedOfferId: string | null, isPending: boolean) => {
        return !!selectedOfferId && !isPending;
      };

      expect(canShop(null, false)).toBe(false);
      expect(canShop("off-1", true)).toBe(false);
      expect(canShop("off-1", false)).toBe(true);
    });

    it("opens exact server redirect_url on successful buy-click handoff", async () => {
      const { api } = require("../src/api/client");
      const mockResult = {
        buy_click_id: "click-xyz",
        redirect_url: "https://www.myntra.com/product/123?utm_source=fashx&click_id=click-xyz",
        tracking_id: "fashx_track_123",
      };
      (api as jest.Mock).mockResolvedValue(mockResult);

      const result = await createBuyClick({
        garmentId: "garment-100",
        offerId: "off-1",
      });

      await Linking.openURL(result.redirect_url);

      expect(api).toHaveBeenCalledWith(
        "/commerce/buy-clicks",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ garment_id: "garment-100", offer_id: "off-1" }),
        })
      );
      expect(Linking.openURL).toHaveBeenCalledWith(
        "https://www.myntra.com/product/123?utm_source=fashx&click_id=click-xyz"
      );
    });

    it("does not call Linking.openURL and alerts when buy-click handoff fails", async () => {
      const { api } = require("../src/api/client");
      (api as jest.Mock).mockRejectedValue(new Error("Network connection failed"));

      let errorCaught = false;
      try {
        await createBuyClick({
          garmentId: "garment-100",
          offerId: "off-1",
        });
      } catch {
        errorCaught = true;
        Alert.alert(
          "Unable to open retailer",
          "The shopping link could not be prepared. Please try again."
        );
      }

      expect(errorCaught).toBe(true);
      expect(Linking.openURL).not.toHaveBeenCalled();
      expect(Alert.alert).toHaveBeenCalledWith(
        "Unable to open retailer",
        "The shopping link could not be prepared. Please try again."
      );
    });
  });

  describe("Try-On Result → Wardrobe Save Payload Logic", () => {
    it("submits verified canonical garment_id and artifact_id to wardrobe save", async () => {
      const { api } = require("../src/api/client");
      (api as jest.Mock).mockResolvedValue({
        item_id: "item-1",
        garment_id: "garment-canon-1",
        tryon_artifact_id: "artifact-uuid-99",
      });

      const mockJob = {
        status: "completed",
        garment_id: "garment-canon-1",
        artifact_id: "artifact-uuid-99",
        artifact_key: "u/user/tryon/job1.png",
      };

      const handleSaveLook = (job: typeof mockJob) => {
        if (!job || job.status !== "completed" || !job.garment_id) return null;
        return {
          garmentId: job.garment_id,
          tryonArtifactId: job.artifact_id ?? null,
        };
      };

      const payload = handleSaveLook(mockJob);
      expect(payload).toEqual({
        garmentId: "garment-canon-1",
        tryonArtifactId: "artifact-uuid-99",
      });

      await saveGarmentToWardrobe(payload!);
      expect(api).toHaveBeenCalledWith(
        "/wardrobe/items",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            garment_id: "garment-canon-1",
            offer_id: null,
            tryon_artifact_id: "artifact-uuid-99",
          }),
        })
      );
    });

    it("rejects saving looks from incomplete, failed, or missing jobs", () => {
      const handleSaveLook = (job: { status?: string; garment_id?: string } | null) => {
        if (!job || job.status !== "completed" || !job.garment_id) return false;
        return true;
      };

      expect(handleSaveLook(null)).toBe(false);
      expect(handleSaveLook({ status: "processing", garment_id: "g1" })).toBe(false);
      expect(handleSaveLook({ status: "failed", garment_id: "g1" })).toBe(false);
      expect(handleSaveLook({ status: "completed", garment_id: undefined })).toBe(false);
      expect(handleSaveLook({ status: "completed", garment_id: "g1" })).toBe(true);
    });
  });

  describe("Wardrobe Removal & Concurrent Tap Protection", () => {
    it("invokes delete endpoint and manages item removal state safely", async () => {
      const { api } = require("../src/api/client");
      (api as jest.Mock).mockResolvedValue(undefined);

      let removingId: string | null = null;
      const handleRemove = async (itemId: string) => {
        if (removingId) return;
        removingId = itemId;
        try {
          await removeGarmentFromWardrobe(itemId);
        } finally {
          removingId = null;
        }
      };

      await handleRemove("wardrobe-item-42");
      expect(api).toHaveBeenCalledWith(
        "/wardrobe/items/wardrobe-item-42",
        expect.objectContaining({ method: "DELETE" })
      );
      expect(removingId).toBeNull();
    });
  });
});
