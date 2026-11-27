import React from "react";
import { RankingReasonBadges } from "../src/features/ranking/RankingReasonBadges";
import { fetchPersonalizedRanking } from "../src/features/ranking/rankingApi";
import { apiClient } from "../src/api/client";

jest.mock("../src/api/client", () => ({
  apiClient: jest.fn(),
}));

const TestRenderer = require("react-test-renderer") as {
  create: (element: React.ReactElement) => { toJSON: () => unknown };
  act: (callback: () => void | Promise<void>) => Promise<void>;
};

describe("Phase 08.4 Personalized Ranking UI & API", () => {
  it("renders evidence-backed ranking reason labels without fit-guarantee claims", async () => {
    let tree!: { toJSON: () => unknown };
    await TestRenderer.act(async () => {
      tree = TestRenderer.create(
        <RankingReasonBadges
          reasonLabels={["Matches your selected category", "Matches your preferred style"]}
          selectedSizeAvailable={true}
          isSponsored={false}
        />,
      );
    });
    const textContent = JSON.stringify(tree.toJSON());
    expect(textContent).toContain("Matches your selected category");
    expect(textContent).toContain("Matches your preferred style");
    expect(textContent).toContain("Selected size available");
    expect(textContent.toLowerCase()).not.toContain("guaranteed fit");
  });

  it("posts ranking context to /api/v1/ranking/products", async () => {
    (apiClient as jest.Mock).mockResolvedValueOnce({
      request_id: "rk_1",
      ranking_version: "personalized-v1",
      config_version: "cfg-personalized-v1",
      taxonomy_version: "v1.0.0",
      cache_hit: false,
      results: [],
      pagination: { page: 1, page_size: 20, total_eligible: 0, has_more: false },
    });

    const resp = await fetchPersonalizedRanking({
      query: "casual shirts",
      category_id: "SHIRTS",
      selected_size: "M",
    });

    expect(apiClient).toHaveBeenCalledWith(
      "/api/v1/ranking/products",
      expect.objectContaining({ method: "POST" }),
    );
    expect(resp.ranking_version).toBe("personalized-v1");
  });
});
