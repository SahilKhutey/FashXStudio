import React from "react";
import { ProductReactionControl } from "../src/features/feedback/ProductReactionControl";
import { SaveProductButton } from "../src/features/feedback/SaveProductButton";
import {
  setProductReaction,
  saveProduct,
  submitFeedbackEvent,
} from "../src/features/feedback/feedbackApi";
import { apiClient } from "../src/api/client";

jest.mock("../src/api/client", () => ({
  apiClient: jest.fn(),
}));

const TestRenderer = require("react-test-renderer") as {
  create: (element: React.ReactElement) => { toJSON: () => unknown };
  act: (callback: () => void | Promise<void>) => Promise<void>;
};

describe("Phase 08.5 Feedback Loop Mobile Components & API", () => {
  it("renders reaction and save controls cleanly", async () => {
    let tree!: { toJSON: () => unknown };
    await TestRenderer.act(async () => {
      tree = TestRenderer.create(
        <>
          <ProductReactionControl reaction="LIKE" onChange={jest.fn()} />
          <SaveProductButton isSaved={true} onToggle={jest.fn()} />
        </>,
      );
    });
    const json = JSON.stringify(tree.toJSON());
    expect(json).toContain("Liked");
    expect(json).toContain("Saved");
  });

  it("submits reaction, save, and feedback events with idempotency", async () => {
    (apiClient as jest.Mock).mockResolvedValue({ status: "RECORDED" });

    await setProductReaction("prod-1", "LIKE", "11111111-1111-4111-8111-111111111111");
    expect(apiClient).toHaveBeenCalledWith(
      "/api/v1/products/prod-1/reaction",
      expect.objectContaining({ method: "PUT" }),
    );

    await saveProduct("prod-1", "offer-1", "22222222-2222-4222-8222-222222222222");
    expect(apiClient).toHaveBeenCalledWith(
      "/api/v1/products/prod-1/saved",
      expect.objectContaining({ method: "PUT" }),
    );

    await submitFeedbackEvent({
      event_id: "33333333-3333-4333-8333-333333333333",
      event_type: "PRODUCT_IMPRESSION",
      subject_type: "PRODUCT",
      subject_id: "prod-1",
      occurred_at: "2026-11-27T09:40:00Z",
      schema_version: 1,
    });
    expect(apiClient).toHaveBeenCalledWith(
      "/api/v1/feedback/events",
      expect.objectContaining({ method: "POST" }),
    );
  });
});
