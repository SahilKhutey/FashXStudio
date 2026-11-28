import React from "react";
import * as ImagePicker from "expo-image-picker";
import * as FileSystem from "expo-file-system";
import { requestGalleryAccess } from "../permissions";
import { validateLocalImage } from "../imageValidation";
import { mapTryOnErrorCode } from "../errors";
import { TRYON_DISCLAIMER } from "../constants";
import { PhotoInstructions } from "../components/PhotoInstructions";
import { PhotoPreview } from "../components/PhotoPreview";
import { VisualSimulationNotice } from "../components/VisualSimulationNotice";
import { cancelTryOnJob } from "../tryonApi";
import { api } from "../../../api/client";

jest.mock("../../../api/client", () => ({
  api: jest.fn(),
  apiClient: jest.fn(),
}));

jest.mock("expo-image-picker", () => ({
  requestMediaLibraryPermissionsAsync: jest.fn(),
  launchImageLibraryAsync: jest.fn(),
}));

jest.mock("expo-file-system", () => ({
  getInfoAsync: jest.fn(),
}));

// eslint-disable-next-line @typescript-eslint/no-require-imports
const TestRenderer = require("react-test-renderer") as {
  create: (element: React.ReactElement) => {
    toJSON: () => unknown;
  };
  act: (callback: () => void | Promise<void>) => Promise<void>;
};

describe("Phase 09.6 gallery permissions (CAM-PERM)", () => {
  it("handles granted and denied gallery permissions", async () => {
    jest
      .spyOn(ImagePicker, "requestMediaLibraryPermissionsAsync")
      .mockResolvedValueOnce({
        granted: true,
        canAskAgain: true,
        status: "granted",
        expires: "never",
      } as never)
      .mockResolvedValueOnce({
        granted: false,
        canAskAgain: false,
        status: "denied",
        expires: "never",
      } as never);

    const granted = await requestGalleryAccess();
    expect(granted.granted).toBe(true);

    const denied = await requestGalleryAccess();
    expect(denied.granted).toBe(false);
    expect(denied.canAskAgain).toBe(false);
  });
});

describe("Phase 09.6 local image validation & error mapping (CAM-IMG, CAM-ERR)", () => {
  it("rejects missing, empty, or oversized images", async () => {
    jest
      .spyOn(FileSystem, "getInfoAsync")
      .mockResolvedValueOnce({ exists: false } as never)
      .mockResolvedValueOnce({ exists: true, size: 0 } as never)
      .mockResolvedValueOnce({ exists: true, size: 12 * 1024 * 1024 } as never)
      .mockResolvedValueOnce({ exists: true, size: 1024 * 1024 } as never);

    await expect(validateLocalImage("file:///missing.jpg")).rejects.toThrow("IMAGE_NOT_FOUND");
    await expect(validateLocalImage("file:///empty.jpg")).rejects.toThrow("IMAGE_EMPTY");
    await expect(validateLocalImage("file:///huge.jpg")).rejects.toThrow("IMAGE_TOO_LARGE");

    const ok = await validateLocalImage("file:///valid.jpg");
    expect(ok.fileSizeBytes).toBe(1024 * 1024);
  });

  it("maps backend error codes to safe shopper messages", () => {
    expect(mapTryOnErrorCode("VTO_CONSENT_REQUIRED")).toContain("consent");
    expect(mapTryOnErrorCode("SUBMISSION_UNKNOWN")).toContain("checking the status");
    expect(mapTryOnErrorCode("UNKNOWN_CODE")).toContain("could not be completed");
  });
});

describe("Phase 09.6 UI components & cancellation (CAM-GUIDE, CAM-PREV, CAM-CAN, CAM-DIS)", () => {
  it("renders PhotoInstructions, VisualSimulationNotice, and PhotoPreview with mandatory disclaimer", async () => {
    let instrTree!: { toJSON: () => unknown };
    let noticeTree!: { toJSON: () => unknown };
    let previewTree!: { toJSON: () => unknown };

    await TestRenderer.act(async () => {
      instrTree = TestRenderer.create(<PhotoInstructions />);
      noticeTree = TestRenderer.create(<VisualSimulationNotice />);
      previewTree = TestRenderer.create(
        <PhotoPreview
          uri="file:///photo.jpg"
          onRetake={jest.fn()}
          onConfirm={jest.fn()}
        />,
      );
    });

    expect(JSON.stringify(instrTree.toJSON())).toContain("Prepare your photo");
    expect(JSON.stringify(noticeTree.toJSON())).toContain(TRYON_DISCLAIMER);
    expect(JSON.stringify(previewTree.toJSON())).toContain("Confirm & start try-on");
  });

  it("calls cancel endpoint cleanly", async () => {
    (api as jest.Mock).mockResolvedValue({ job_id: "job-1", status: "cancelled" });
    await cancelTryOnJob("job-1");
    expect(api).toHaveBeenCalledWith(
      "/tryon/jobs/job-1/cancel",
      { method: "POST", body: JSON.stringify({}) },
    );
  });
});
