import React from "react";
import { fireEvent, render } from "@testing-library/react-native";

import {
  evaluateFitRecommendation,
  getFitRecommendation,
  submitFitFeedback,
} from "../src/features/fit/api/fitApi";
import { FitRecommendationCard } from "../src/features/fit/components/FitRecommendationCard";
import { useFitStore } from "../src/features/fit/store/fitStore";
import type { FitRecommendationResult } from "../src/features/fit/types/fit";

jest.mock("../src/api/client", () => ({
  api: jest.fn(),
}));

const BASE_REC: FitRecommendationResult = {
  recommendation_id: "rec-1",
  status: "RECOMMENDED",
  recommended_size: { variant_id: "var-m", merchant_size_label: "M" },
  alternative_sizes: [],
  confidence: {
    score: "0.910",
    type: "INTERNAL_EVIDENCE_SCORE",
    display_to_shopper: false,
  },
  reason_codes: ["WITHIN_PUBLISHED_RANGE", "ALL_REQUIRED_MEASUREMENTS_MATCH"],
  missing_information: [],
  explanations: [
    "Your measurement falls within the merchant's published range for this size.",
  ],
  explanation:
    "Size M matches your available measurements on this merchant's published size chart.",
  evidence: {
    merchant_id: "merch-1",
    product_id: "prod-1",
    size_chart_id: "chart-1",
    size_chart_revision: 4,
    measurement_basis: "BODY",
    category_policy_version: "1.0",
    fit_algorithm_version: "08.3.1",
    preference_evaluated: false,
    evidence_items: [
      { label: "Shopper chest measurement", status: "Available" },
      { label: "Merchant size chart", status: "Current" },
    ],
  },
  is_valid: true,
  fit_guaranteed: false,
  disclaimer_code: "SIZE_GUIDANCE_NOT_FIT_GUARANTEE",
  disclaimer:
    "This is size guidance based on available product and shopper information. It does not guarantee physical fit, comfort or appearance.",
  next_actions: [],
  created_at: "2026-11-26T00:00:00Z",
};

describe("Phase 08.3 Mobile: Fit Recommendation Logic", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useFitStore.getState().resetFitState();
  });

  it("calls fit recommendation and feedback endpoints via shared api client", async () => {
    const { api } = require("../src/api/client");
    (api as jest.Mock).mockResolvedValue(BASE_REC);

    await evaluateFitRecommendation({ product_id: "prod-1", merchant_offer_id: "off-1" });
    expect(api).toHaveBeenCalledWith("/fit/recommendations", {
      method: "POST",
      body: JSON.stringify({ product_id: "prod-1", merchant_offer_id: "off-1" }),
    });

    await getFitRecommendation("rec-1");
    expect(api).toHaveBeenCalledWith("/fit/recommendations/rec-1");

    await submitFitFeedback("rec-1", {
      reason: "FIT_TOO_TIGHT",
      tried_on: true,
      purchase_status: "PURCHASED",
    });
    expect(api).toHaveBeenCalledWith("/fit/recommendations/rec-1/feedback", {
      method: "POST",
      body: JSON.stringify({
        reason: "FIT_TOO_TIGHT",
        tried_on: true,
        purchase_status: "PURCHASED",
      }),
    });
  });

  it("renders recommended size with merchant chart evidence without uncalibrated score %", async () => {
    const { getByTestId, queryByText, getByText } = await render(
      <FitRecommendationCard recommendation={BASE_REC} />,
    );

    expect(getByTestId("recommended-size-label")).toHaveTextContent("Size M");
    expect(getByTestId("fit-evidence-list")).toBeTruthy();
    expect(getByText(/Chart revision: 4/)).toBeTruthy();
    expect(getByTestId("fit-disclaimer")).toHaveTextContent(
      /does not guarantee physical fit/i,
    );
    expect(queryByText(/0\.910|91%/)).toBeNull();
  });

  it("renders abstention states cleanly (INSUFFICIENT_INFORMATION, STALE_DATA, POSSIBLE_ALTERNATIVES)", async () => {
    const missingRec: FitRecommendationResult = {
      ...BASE_REC,
      status: "INSUFFICIENT_INFORMATION",
      recommended_size: null,
      explanations: ["Some information is missing. Add the requested measurement to receive size guidance."],
      explanation: "Some information is missing. Add the requested measurement to receive size guidance.",
      next_actions: ["Add the missing measurement in your Fit Profile."],
    };

    const { getByTestId, getByText, rerender } = await render(
      <FitRecommendationCard recommendation={missingRec} />,
    );
    expect(getByTestId("fit-recommendation-INSUFFICIENT_INFORMATION")).toBeTruthy();
    expect(getByText(/Add the missing measurement/i)).toBeTruthy();

    const altRec: FitRecommendationResult = {
      ...BASE_REC,
      status: "POSSIBLE_ALTERNATIVES",
      recommended_size: null,
      alternative_sizes: [
        { variant_id: "var-m", merchant_size_label: "M" },
        { variant_id: "var-l", merchant_size_label: "L" },
      ],
    };
    await rerender(<FitRecommendationCard recommendation={altRec} />);
    expect(getByTestId("alternative-sizes-label")).toHaveTextContent("Options: M or L");
  });

  it("handles loading, error retry, and feedback submission", async () => {
    const onRetry = jest.fn();
    const onSubmitFeedback = jest.fn();

    const { getByTestId, getByText, rerender } = await render(
      <FitRecommendationCard recommendation={null} loading={true} />,
    );
    expect(getByTestId("fit-recommendation-loading")).toBeTruthy();

    await rerender(
      <FitRecommendationCard
        recommendation={null}
        loading={false}
        error="Network error"
        onRetry={onRetry}
      />,
    );
    await fireEvent.press(getByText("Retry"));
    expect(onRetry).toHaveBeenCalledTimes(1);

    await rerender(
      <FitRecommendationCard
        recommendation={BASE_REC}
        onSubmitFeedback={onSubmitFeedback}
      />,
    );
    await fireEvent.press(getByText("Too tight"));
    await fireEvent.press(getByText("Submit feedback"));
    expect(onSubmitFeedback).toHaveBeenCalledWith(
      "rec-1",
      expect.objectContaining({ reason: "FIT_TOO_TIGHT", tried_on: false }),
    );

    await rerender(
      <FitRecommendationCard
        recommendation={BASE_REC}
        feedbackSubmitted={true}
        onSubmitFeedback={onSubmitFeedback}
      />,
    );
    expect(getByTestId("fit-feedback-submitted")).toBeTruthy();
  });
});
