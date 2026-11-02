import {
  getTryOnPollInterval,
  isTerminalTryOnStatus,
} from "../src/features/tryon/polling";

describe("VTO polling", () => {
  it("continues polling queued jobs", () => {
    expect(getTryOnPollInterval(5_000, "queued")).toBe(3_000);
  });

  it("continues polling inference jobs", () => {
    expect(getTryOnPollInterval(30_000, "inference")).toBe(3_000);
  });

  it("slows polling for long-running jobs", () => {
    expect(getTryOnPollInterval(11 * 60 * 1000, "inference")).toBe(15_000);
  });

  it.each(["completed", "failed", "cancelled"] as const)(
    "stops polling for %s",
    (status) => {
      expect(isTerminalTryOnStatus(status)).toBe(true);
      expect(getTryOnPollInterval(5_000, status)).toBe(false);
    }
  );

  it("does not classify a non-terminal status as terminal", () => {
    expect(isTerminalTryOnStatus("quality_check")).toBe(false);
  });
});
