import { rejectKey } from "../src/lib/qualityReasons";
import rejectReasonsJson from "../src/api/reject-reasons.json";

describe("Quality Rejection Reason Mapping", () => {
  it("maps every exported reject code to a localized capture.reject.<code_lower> key", () => {
    expect(rejectReasonsJson.length).toBeGreaterThan(0);
    for (const code of rejectReasonsJson) {
      const key = rejectKey(code);
      expect(key).toBe(`capture.reject.${code.toLowerCase()}`);
    }
  });

  it("maps descriptive validator phrases to specific reject keys", () => {
    expect(rejectKey("image is too dark")).toBe("capture.reject.too_dark");
    expect(rejectKey("harsh overexposed flash")).toBe("capture.reject.too_bright");
    expect(rejectKey("low contrast background")).toBe("capture.reject.low_contrast");
    expect(rejectKey("resolution below the required minimum")).toBe("capture.reject.resolution_too_low");
    expect(rejectKey("landscape mode not supported")).toBe("capture.reject.landscape_orientation");
    expect(rejectKey("multiple people detected")).toBe("capture.reject.multiple_people");
    expect(rejectKey("no person found")).toBe("capture.reject.person_not_detected");
    expect(rejectKey("face not visible")).toBe("capture.reject.face_not_visible");
    expect(rejectKey("pose is not upright")).toBe("capture.reject.pose_not_upright");
    expect(rejectKey("invalid file unreadable")).toBe("capture.reject.invalid_format");
  });

  it("falls back to capture.reject.generic on null, undefined, empty, or unknown strings", () => {
    expect(rejectKey(null)).toBe("capture.reject.generic");
    expect(rejectKey(undefined)).toBe("capture.reject.generic");
    expect(rejectKey("")).toBe("capture.reject.generic");
    expect(rejectKey("some_completely_unknown_failure_code_xyz")).toBe("capture.reject.generic");
  });
});
