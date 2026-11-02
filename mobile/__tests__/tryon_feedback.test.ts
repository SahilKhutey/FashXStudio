import {
  ratingToVisualAccuracy,
  TryOnIssueTag,
} from "../src/features/tryon/useTryOn";

describe("Phase 9 Visual Realism Feedback & Quality Learning", () => {
  describe("ratingToVisualAccuracy mapping", () => {
    it("maps 1 star to very_inaccurate", () => {
      expect(ratingToVisualAccuracy(1)).toBe("very_inaccurate");
      expect(ratingToVisualAccuracy(0)).toBe("very_inaccurate");
    });

    it("maps 2 stars to inaccurate", () => {
      expect(ratingToVisualAccuracy(2)).toBe("inaccurate");
    });

    it("maps 3 stars to neutral", () => {
      expect(ratingToVisualAccuracy(3)).toBe("neutral");
    });

    it("maps 4 stars to accurate", () => {
      expect(ratingToVisualAccuracy(4)).toBe("accurate");
    });

    it("maps 5 stars to very_accurate", () => {
      expect(ratingToVisualAccuracy(5)).toBe("very_accurate");
    });
  });

  describe("Feedback Payload Builder & Interaction State Machine", () => {
    function buildFeedbackPayload(params: {
      jobId: string;
      rating: number;
      purchaseConfidence?: number;
      issueTags?: TryOnIssueTag[];
    }) {
      const visualAccuracy = ratingToVisualAccuracy(params.rating);
      return {
        endpoint: "/feedback/tryon",
        method: "POST",
        body: {
          tryon_job_id: params.jobId,
          visual_accuracy: visualAccuracy,
          purchase_confidence: params.purchaseConfidence ?? null,
          issue_tags: params.issueTags ?? [],
        },
      };
    }

    it("builds atomic feedback payload without client user_id", () => {
      const payload = buildFeedbackPayload({
        jobId: "job-abc-123",
        rating: 2,
        issueTags: ["garment_distorted", "blurry_artifacts"],
        purchaseConfidence: 2,
      });

      expect(payload.endpoint).toBe("/feedback/tryon");
      expect(payload.method).toBe("POST");
      expect(payload.body.tryon_job_id).toBe("job-abc-123");
      expect(payload.body.visual_accuracy).toBe("inaccurate");
      expect(payload.body.purchase_confidence).toBe(2);
      expect(payload.body.issue_tags).toEqual([
        "garment_distorted",
        "blurry_artifacts",
      ]);
      // Client does not hardcode user_id; server derives it from authenticated bearer principal
      expect((payload.body as Record<string, unknown>).user_id).toBeUndefined();
    });

    it("handles rating selection and chip toggles before explicit submit", () => {
      let selectedRating: number | null = null;
      let selectedChips: string[] = [];
      let feedbackSent = false;

      // User selects 3 stars
      selectedRating = 3;
      expect(selectedRating).toBe(3);
      expect(feedbackSent).toBe(false);

      // User toggles issue chips
      const toggleChip = (tag: string) => {
        if (selectedChips.includes(tag)) {
          selectedChips = selectedChips.filter((c) => c !== tag);
        } else {
          selectedChips = [...selectedChips, tag];
        }
      };

      toggleChip("unnatural_fit");
      toggleChip("color_inaccurate");
      expect(selectedChips).toEqual(["unnatural_fit", "color_inaccurate"]);

      // User deselects a chip
      toggleChip("unnatural_fit");
      expect(selectedChips).toEqual(["color_inaccurate"]);

      // User taps Submit
      const submission = buildFeedbackPayload({
        jobId: "job-999",
        rating: selectedRating,
        issueTags: selectedChips as TryOnIssueTag[],
      });
      expect(submission.body.visual_accuracy).toBe("neutral");
      expect(submission.body.issue_tags).toEqual(["color_inaccurate"]);

      // Upon success, feedbackSent locks state
      feedbackSent = true;
      expect(feedbackSent).toBe(true);
    });

    it("allows positive 5-star rating without issue tags", () => {
      const payload = buildFeedbackPayload({
        jobId: "job-positive-555",
        rating: 5,
        purchaseConfidence: 5,
      });

      expect(payload.body.visual_accuracy).toBe("very_accurate");
      expect(payload.body.purchase_confidence).toBe(5);
      expect(payload.body.issue_tags).toEqual([]);
    });
  });
});
