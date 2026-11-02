import { api } from "../../../api/client";
import { createBuyClick } from "../commerceApi";

jest.mock("../../../api/client", () => ({
  api: jest.fn(),
}));

describe("createBuyClick", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("sends the selected garment and offer to the backend", async () => {
    const response = {
      buy_click_id: "click-123",
      redirect_url: "https://shop.example.com/item/1",
      tracking_id: "fashx_test",
    };

    (api as jest.Mock).mockResolvedValue(response);

    const result = await createBuyClick({
      garmentId: "garment-123",
      offerId: "offer-456",
    });

    expect(api).toHaveBeenCalledWith(
      "/commerce/buy-clicks",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          garment_id: "garment-123",
          offer_id: "offer-456",
        }),
      })
    );

    expect(result.redirect_url).toBe("https://shop.example.com/item/1");
  });
});
