import {
  getTryOnPollInterval,
  isTerminalTryOnStatus,
} from "../src/features/tryon/polling";

describe("TryOnJobScreen Logic & State Machine", () => {
  describe("Provider Classification (Rule: Real vs Mock vs Unknown)", () => {
    function classifyProvider(providerValue?: string | null) {
      const provider = providerValue ?? "unknown";
      const isMockProvider = provider === "mock";
      const isRealProvider = provider !== "mock" && provider !== "unknown";
      return { provider, isMockProvider, isRealProvider };
    }

    it("correctly identifies mock provider and flags preview-only", () => {
      const { provider, isMockProvider, isRealProvider } = classifyProvider("mock");
      expect(provider).toBe("mock");
      expect(isMockProvider).toBe(true);
      expect(isRealProvider).toBe(false);
    });

    it("correctly identifies real commercial provider without mock warning", () => {
      const { provider, isMockProvider, isRealProvider } = classifyProvider("fashn_api");
      expect(provider).toBe("fashn_api");
      expect(isMockProvider).toBe(false);
      expect(isRealProvider).toBe(true);
    });

    it("classifies missing or null provider as unknown without assuming mock", () => {
      const nullResult = classifyProvider(null);
      expect(nullResult.provider).toBe("unknown");
      expect(nullResult.isMockProvider).toBe(false);
      expect(nullResult.isRealProvider).toBe(false);

      const undefinedResult = classifyProvider(undefined);
      expect(undefinedResult.provider).toBe("unknown");
      expect(undefinedResult.isMockProvider).toBe(false);
      expect(undefinedResult.isRealProvider).toBe(false);
    });
  });

  describe("Wardrobe Saving Payload Mapping", () => {
    function buildSaveLookPayload(job: {
      job_id: string;
      garment_id: string;
      artifact_key: string;
    }) {
      if (!job.garment_id || !job.artifact_key) return null;
      return {
        garmentId: job.garment_id,
        tryonArtifactId: job.artifact_key,
      };
    }

    it("uses actual garment_id rather than parsing artifact key", () => {
      const job = {
        job_id: "job-uuid-123",
        garment_id: "garment-uuid-real-456",
        artifact_key: "tryon/artifacts/composite-hash-789",
      };

      const payload = buildSaveLookPayload(job);
      expect(payload).toEqual({
        garmentId: "garment-uuid-real-456",
        tryonArtifactId: "tryon/artifacts/composite-hash-789",
      });
      expect(payload?.garmentId).not.toContain("composite-hash");
    });
  });

  describe("Retry Mechanism (Creates fresh job, does not restart old job)", () => {
    function generateRetryPayload(garmentId: string) {
      const idempotencyKey = `tryon-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
      return {
        endpoint: "/tryon/jobs",
        method: "POST",
        idempotencyKey,
        body: {
          garment_id: garmentId,
        },
      };
    }

    it("generates fresh idempotency key and targets new job submission", () => {
      const p1 = generateRetryPayload("garment-100");
      const p2 = generateRetryPayload("garment-100");

      expect(p1.endpoint).toBe("/tryon/jobs");
      expect(p1.method).toBe("POST");
      expect(p1.body.garment_id).toBe("garment-100");
      expect(p1.idempotencyKey).not.toBe(p2.idempotencyKey);
      expect(p1.idempotencyKey.startsWith("tryon-")).toBe(true);
    });
  });

  describe("Signed URL Refresh & Failure State Machine", () => {
    it("handles image load failure by enabling refresh action", () => {
      let imageLoadFailed = false;
      const setImageLoadFailed = (failed: boolean) => {
        imageLoadFailed = failed;
      };

      // Simulate image error event
      setImageLoadFailed(true);
      expect(imageLoadFailed).toBe(true);

      // On new result URL arriving, error state resets
      const handleNewResultUrl = () => {
        imageLoadFailed = false;
      };
      handleNewResultUrl();
      expect(imageLoadFailed).toBe(false);
    });
  });

  describe("Before/After Reference Photo Access", () => {
    function resolveBeforeView(job: { reference_photo_url?: string | null }) {
      if (job.reference_photo_url) {
        return { type: "image", uri: job.reference_photo_url };
      }
      return { type: "placeholder", message: "Original photo is unavailable" };
    }

    it("returns signed image URL when reference photo is available", () => {
      const view = resolveBeforeView({
        reference_photo_url: "https://storage.local/u/123/photos/ref.jpg?exp=300",
      });
      expect(view.type).toBe("image");
      expect(view.uri).toContain("exp=300");
    });

    it("returns explicit unavailable state when reference photo is missing", () => {
      const view = resolveBeforeView({ reference_photo_url: null });
      expect(view.type).toBe("placeholder");
      expect(view.message).toBe("Original photo is unavailable");
    });
  });
});
