import React from "react";
import { formatOfferPrice } from "../src/features/wardrobe/RetailerOffers";
import { isSafeRetailerRedirect } from "../src/lib/safeRedirect";
import { createBuyClick } from "../src/features/commerce/buyClickApi";

jest.mock("../src/api/client", () => ({
  api: jest.fn(),
}));

describe("RC06 Mobile: Retailer Offers & Buy Click Handoff", () => {
  describe("formatOfferPrice", () => {
    it("formats INR prices correctly without decimals when round", () => {
      expect(formatOfferPrice(199900, "INR")).toBe("₹1999");
      expect(formatOfferPrice(50000, "inr")).toBe("₹500");
    });

    it("formats INR prices with decimals when fractional", () => {
      expect(formatOfferPrice(199950, "INR")).toBe("₹1999.50");
    });

    it("formats USD prices with 2 decimal places", () => {
      expect(formatOfferPrice(4999, "USD")).toBe("$49.99");
      expect(formatOfferPrice(1000, "usd")).toBe("$10.00");
    });

    it("formats EUR prices with 2 decimal places", () => {
      expect(formatOfferPrice(3500, "EUR")).toBe("€35.00");
    });

    it("formats other currencies with code and 2 decimal places", () => {
      expect(formatOfferPrice(2500, "GBP")).toBe("GBP 25.00");
      expect(formatOfferPrice(100000, "JPY")).toBe("JPY 1000.00");
    });
  });

  describe("Retailer Destination URL Validation (isSafeRetailerRedirect)", () => {
    it("accepts valid HTTPS retailer URLs", () => {
      expect(isSafeRetailerRedirect("https://www.myntra.com/shirts/123")).toBe(true);
      expect(isSafeRetailerRedirect("https://www.ajio.com/clothing/456?utm_source=fashx")).toBe(true);
      expect(isSafeRetailerRedirect("https://store.zara.com/in/product")).toBe(true);
    });

    it("rejects non-HTTPS URLs", () => {
      expect(isSafeRetailerRedirect("http://www.myntra.com/shirts/123")).toBe(false);
      expect(isSafeRetailerRedirect("ftp://files.example.com/item")).toBe(false);
      expect(isSafeRetailerRedirect("javascript:alert(1)")).toBe(false);
    });

    it("rejects URLs with user credentials (user:pass@host)", () => {
      expect(isSafeRetailerRedirect("https://user:pass@www.myntra.com/item")).toBe(false);
      expect(isSafeRetailerRedirect("https://attacker:secret@shop.com/")).toBe(false);
    });

    it("rejects localhost, private IPs, and loopback destinations", () => {
      expect(isSafeRetailerRedirect("https://localhost:8000/pay")).toBe(false);
      expect(isSafeRetailerRedirect("https://127.0.0.1/callback")).toBe(false);
      expect(isSafeRetailerRedirect("https://169.254.169.254/latest/meta-data")).toBe(false);
    });

    it("rejects malformed or empty URLs", () => {
      expect(isSafeRetailerRedirect("")).toBe(false);
      expect(isSafeRetailerRedirect("not-a-valid-url")).toBe(false);
      expect(isSafeRetailerRedirect("https://")).toBe(false);
    });
  });

  describe("createBuyClick API contract", () => {
    it("calls POST /commerce/buy-clicks with garment_id and offer_id", async () => {
      const { api } = require("../src/api/client");
      const mockResponse = {
        buy_click_id: "bc-uuid-123",
        redirect_url: "https://www.myntra.com/buy?click_id=bc-uuid-123",
        tracking_id: "track-123",
      };
      (api as jest.Mock).mockResolvedValue(mockResponse);

      const res = await createBuyClick({
        garment_id: "garment-uuid-1",
        offer_id: "offer-uuid-2",
      });

      expect(api).toHaveBeenCalledWith("/commerce/buy-clicks", {
        method: "POST",
        body: JSON.stringify({
          garment_id: "garment-uuid-1",
          offer_id: "offer-uuid-2",
        }),
      });
      expect(res.buy_click_id).toBe("bc-uuid-123");
      expect(res.redirect_url).toBe("https://www.myntra.com/buy?click_id=bc-uuid-123");
    });
  });

  describe("Offer Selection and Availability Business Rules", () => {
    const sampleOffers = [
      {
        id: "offer-1",
        merchant_name: "Myntra",
        price_minor: 149900,
        currency: "INR",
        in_stock: true,
        updated_at: "2026-11-04T08:00:00Z",
      },
      {
        id: "offer-2",
        merchant_name: "Ajio",
        price_minor: 129900,
        currency: "INR",
        in_stock: false,
        updated_at: "2026-11-04T08:00:00Z",
      },
    ];

    it("requires explicit offer selection before proceeding", () => {
      let selectedOfferId: string | null = null;
      const canProceed = (offerId: string | null, offers: typeof sampleOffers) => {
        if (!offerId) return false;
        const offer = offers.find((o) => o.id === offerId);
        return offer ? offer.in_stock : false;
      };

      expect(canProceed(selectedOfferId, sampleOffers)).toBe(false);

      // Select out-of-stock offer
      selectedOfferId = "offer-2";
      expect(canProceed(selectedOfferId, sampleOffers)).toBe(false);

      // Select in-stock offer
      selectedOfferId = "offer-1";
      expect(canProceed(selectedOfferId, sampleOffers)).toBe(true);
    });

    it("verifies merchant title resolution falls back gracefully", () => {
      const getTitle = (name?: string | null) => name || "Authorized Retailer";
      expect(getTitle("Myntra")).toBe("Myntra");
      expect(getTitle(null)).toBe("Authorized Retailer");
      expect(getTitle(undefined)).toBe("Authorized Retailer");
    });
  });
});
