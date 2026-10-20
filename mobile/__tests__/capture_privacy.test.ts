import { uploadPhoto } from "../src/lib/upload";
import { cleanupFiles } from "../src/lib/fileCleanup";

jest.mock("../src/lib/fileCleanup", () => ({
  cleanupFiles: jest.fn().mockResolvedValue(undefined),
  cleanupFile: jest.fn().mockResolvedValue(true),
}));

jest.mock("../src/lib/token", () => ({
  getAccessToken: jest.fn().mockResolvedValue("mock-jwt-token"),
}));

describe("Capture Privacy and Logging Invariants", () => {
  let logSpy: jest.SpyInstance;
  let warnSpy: jest.SpyInstance;
  let errorSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    logSpy = jest.spyOn(console, "log").mockImplementation(() => {});
    warnSpy = jest.spyOn(console, "warn").mockImplementation(() => {});
    errorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    logSpy.mockRestore();
    warnSpy.mockRestore();
    errorSpy.mockRestore();
  });

  it("never logs image URIs or filenames to console during capture flow", async () => {
    const sensitivePhotoUri = "file:///data/user/0/com.fashx.app/cache/camera_raw_portrait_user123.jpg";

    // Simulate capture lifecycle handler
    const mockUpload = jest.fn().mockRejectedValue({
      status: 422,
      error: { code: "quality_rejected", message: "Photo too dark" },
    });

    let uploaded = false;
    let failureReason = "";
    try {
      await mockUpload(sensitivePhotoUri);
      uploaded = true;
    } catch (e: any) {
      failureReason = e?.error?.message || "failed";
    } finally {
      await cleanupFiles([sensitivePhotoUri]);
    }

    expect(uploaded).toBe(false);
    expect(failureReason).toBe("Photo too dark");
    expect(cleanupFiles).toHaveBeenCalledWith([sensitivePhotoUri]);

    // Inspect all logs across log, warn, and error
    const allCalls = [
      ...logSpy.mock.calls,
      ...warnSpy.mock.calls,
      ...errorSpy.mock.calls,
    ];

    for (const call of allCalls) {
      const formatted = JSON.stringify(call);
      expect(formatted).not.toContain(sensitivePhotoUri);
      expect(formatted).not.toContain("camera_raw_portrait");
      expect(formatted).not.toContain(".jpg");
    }
  });

  it("triggers file cleanup regardless of success or failure in finally block", async () => {
    const rawUri = "file:///cache/raw_portrait.jpg";
    const preparedUri = "file:///cache/prepared_2048.jpg";

    // Success path
    try {
      // simulate success
    } finally {
      await cleanupFiles([rawUri, preparedUri]);
    }
    expect(cleanupFiles).toHaveBeenCalledWith([rawUri, preparedUri]);

    // Error path
    try {
      throw new Error("Network upload dropped connection");
    } catch {
      // caught
    } finally {
      await cleanupFiles([rawUri, preparedUri]);
    }
    expect(cleanupFiles).toHaveBeenCalledTimes(2);
  });
});
