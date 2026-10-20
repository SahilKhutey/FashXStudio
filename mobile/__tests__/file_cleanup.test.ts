import { cleanupFile, cleanupFiles } from "../src/lib/fileCleanup";
import { File } from "expo-file-system";

jest.mock("expo-file-system", () => {
  return {
    File: jest.fn().mockImplementation((path: string) => ({
      path,
      delete: jest.fn(),
    })),
  };
});

describe("File Cleanup Safety (Privacy & Storage Leak Prevention)", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("safely ignores null and undefined URIs", async () => {
    expect(await cleanupFile(null)).toBe(false);
    expect(await cleanupFile(undefined)).toBe(false);
    expect(await cleanupFile("")).toBe(false);
  });

  it("calls delete on File instance for provided URI", async () => {
    const res = await cleanupFile("file:///cache/raw_portrait_temp.jpg");
    expect(res).toBe(true);
    expect(File).toHaveBeenCalledWith("file:///cache/raw_portrait_temp.jpg");
  });

  it("cleans up a batch of raw and prepared URIs in finally flow", async () => {
    const uris = [
      "file:///cache/raw_capture.jpg",
      "file:///cache/manipulated_2048.jpg",
      null,
      undefined,
    ];
    await cleanupFiles(uris);
    expect(File).toHaveBeenCalledTimes(2);
    expect(File).toHaveBeenCalledWith("file:///cache/raw_capture.jpg");
    expect(File).toHaveBeenCalledWith("file:///cache/manipulated_2048.jpg");
  });

  it("handles delete throw gracefully without propagating error", async () => {
    (File as unknown as jest.Mock).mockImplementationOnce(() => ({
      delete: () => {
        throw new Error("File already removed or permission error");
      },
    }));

    // Should not throw
    await expect(cleanupFile("file:///cache/already_gone.jpg")).resolves.toBeDefined();
  });
});
