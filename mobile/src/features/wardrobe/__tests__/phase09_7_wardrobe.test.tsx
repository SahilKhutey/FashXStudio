import React from "react";
import { api } from "../../../api/client";
import {
  createSavedLook,
  deleteSavedLook,
  getSavedLook,
  getSavedLooks,
} from "../api";
import { wardrobeKeys } from "../hooks";
import { EmptyCloset } from "../components/EmptyCloset";
import { EmptyLooks } from "../components/EmptyLooks";

jest.mock("../../../api/client", () => ({
  api: jest.fn(),
  apiClient: jest.fn(),
}));

// eslint-disable-next-line @typescript-eslint/no-require-imports
const TestRenderer = require("react-test-renderer") as {
  create: (element: React.ReactElement) => {
    toJSON: () => unknown;
  };
  act: (callback: () => void | Promise<void>) => Promise<void>;
};

describe("Phase 09.7 saved looks API & account-scoped keys", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("scopes wardrobeKeys by authenticated userId", () => {
    expect(wardrobeKeys.items("user-a")).toEqual([
      "account",
      "user-a",
      "wardrobe",
      "items",
    ]);
    expect(wardrobeKeys.looks("user-b")).toEqual([
      "account",
      "user-b",
      "wardrobe",
      "looks",
    ]);
  });

  it("calls saved-looks endpoints cleanly", async () => {
    (api as jest.Mock).mockResolvedValue({ looks: [], next_cursor: null });
    await getSavedLooks();
    expect(api).toHaveBeenCalledWith("/wardrobe/looks");

    (api as jest.Mock).mockResolvedValue({ id: "look-1", title: "Casual" });
    await createSavedLook({
      title: "Casual",
      description: "Day out",
      item_ids: ["item-1"],
    });
    expect(api).toHaveBeenCalledWith("/wardrobe/looks", {
      method: "POST",
      body: JSON.stringify({
        title: "Casual",
        description: "Day out",
        item_ids: ["item-1"],
      }),
    });

    await getSavedLook("look-1");
    expect(api).toHaveBeenCalledWith("/wardrobe/looks/look-1");

    await deleteSavedLook("look-1");
    expect(api).toHaveBeenCalledWith("/wardrobe/looks/look-1", {
      method: "DELETE",
    });
  });
});

describe("Phase 09.7 empty state components (WRD-EMPTY)", () => {
  it("renders distinct EmptyCloset and EmptyLooks states", async () => {
    let closetTree!: { toJSON: () => unknown };
    let looksTree!: { toJSON: () => unknown };

    await TestRenderer.act(async () => {
      closetTree = TestRenderer.create(<EmptyCloset onExplore={jest.fn()} />);
      looksTree = TestRenderer.create(<EmptyLooks onCreateLook={jest.fn()} />);
    });

    expect(JSON.stringify(closetTree.toJSON())).toContain("Your closet is empty");
    expect(JSON.stringify(looksTree.toJSON())).toContain("No saved looks yet");
  });
});
