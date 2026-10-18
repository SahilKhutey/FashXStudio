import { getStableCacheKey } from "../src/hooks/useSignedImage";
import { ratingToVisualAccuracy } from "../src/features/tryon/useTryOn";

describe("Stable Image Cache Key Generation", () => {
  it("strips temporary signed query parameters and tokens", () => {
    const signedUrl =
      "https://storage.googleapis.com/fashx-renders/tryon/123/result.png?token=exp123456&signature=abcde9876";
    expect(getStableCacheKey(signedUrl)).toBe(
      "https://storage.googleapis.com/fashx-renders/tryon/123/result.png"
    );
  });

  it("strips url fragments", () => {
    const url = "https://cdn.example.com/garment1.jpg#preview";
    expect(getStableCacheKey(url)).toBe("https://cdn.example.com/garment1.jpg");
  });

  it("prefers explicit custom cache key when provided", () => {
    const signedUrl = "https://cdn.example.com/img.jpg?sig=xyz";
    expect(getStableCacheKey(signedUrl, "garment:custom-uuid")).toBe(
      "garment:custom-uuid"
    );
  });

  it("handles null or undefined gracefully", () => {
    expect(getStableCacheKey(null)).toBeNull();
    expect(getStableCacheKey(undefined)).toBeNull();
  });
});

describe("Visual Accuracy Rating Mapping", () => {
  it("maps 1-5 rating correctly to backend enum values", () => {
    expect(ratingToVisualAccuracy(1)).toBe("very_inaccurate");
    expect(ratingToVisualAccuracy(2)).toBe("inaccurate");
    expect(ratingToVisualAccuracy(3)).toBe("neutral");
    expect(ratingToVisualAccuracy(4)).toBe("accurate");
    expect(ratingToVisualAccuracy(5)).toBe("very_accurate");
  });

  it("handles edge rating values safely", () => {
    expect(ratingToVisualAccuracy(0)).toBe("very_inaccurate");
    expect(ratingToVisualAccuracy(6)).toBe("very_accurate");
  });
});

describe("Try-on Polling Exponential Backoff and Ceiling", () => {
  function getRefetchInterval(options: {
    isFocused: boolean;
    status: string;
    elapsedSeconds: number;
    pollCount: number;
  }): number | false {
    if (!options.isFocused) return false;
    if (
      options.status === "completed" ||
      options.status === "failed" ||
      options.status === "cancelled"
    ) {
      return false;
    }
    if (options.elapsedSeconds >= 600) {
      return false;
    }
    return Math.min(1000 * Math.pow(2, options.pollCount), 5000);
  }

  it("calculates exponential backoff capped at 5000ms", () => {
    expect(
      getRefetchInterval({ isFocused: true, status: "processing", elapsedSeconds: 0, pollCount: 0 })
    ).toBe(1000);
    expect(
      getRefetchInterval({ isFocused: true, status: "processing", elapsedSeconds: 2, pollCount: 1 })
    ).toBe(2000);
    expect(
      getRefetchInterval({ isFocused: true, status: "processing", elapsedSeconds: 4, pollCount: 2 })
    ).toBe(4000);
    expect(
      getRefetchInterval({ isFocused: true, status: "processing", elapsedSeconds: 8, pollCount: 3 })
    ).toBe(5000);
    expect(
      getRefetchInterval({ isFocused: true, status: "processing", elapsedSeconds: 15, pollCount: 4 })
    ).toBe(5000);
  });

  it("stops polling when screen is unfocused", () => {
    expect(
      getRefetchInterval({ isFocused: false, status: "processing", elapsedSeconds: 10, pollCount: 2 })
    ).toBe(false);
  });

  it("stops polling at the 10-minute (600s) ceiling", () => {
    expect(
      getRefetchInterval({ isFocused: true, status: "processing", elapsedSeconds: 599, pollCount: 10 })
    ).toBe(5000);
    expect(
      getRefetchInterval({ isFocused: true, status: "processing", elapsedSeconds: 600, pollCount: 10 })
    ).toBe(false);
    expect(
      getRefetchInterval({ isFocused: true, status: "processing", elapsedSeconds: 650, pollCount: 10 })
    ).toBe(false);
  });

  it("stops polling when job is in a terminal state", () => {
    expect(
      getRefetchInterval({ isFocused: true, status: "completed", elapsedSeconds: 10, pollCount: 2 })
    ).toBe(false);
    expect(
      getRefetchInterval({ isFocused: true, status: "failed", elapsedSeconds: 10, pollCount: 2 })
    ).toBe(false);
  });
});

describe("Signal 5-second Undo Timer and AppState Backgrounding", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("does not trigger callback if undone within 5 seconds", () => {
    const flushMock = jest.fn();
    let timerId: any = null;

    const startSignal = () => {
      timerId = setTimeout(flushMock, 5000);
    };

    const undoSignal = () => {
      if (timerId) {
        clearTimeout(timerId);
        timerId = null;
      }
    };

    startSignal();
    jest.advanceTimersByTime(2000);
    undoSignal();
    jest.advanceTimersByTime(4000);

    expect(flushMock).not.toHaveBeenCalled();
  });

  it("triggers callback when full 5 seconds elapse without undo", () => {
    const flushMock = jest.fn();

    setTimeout(flushMock, 5000);
    jest.advanceTimersByTime(4999);
    expect(flushMock).not.toHaveBeenCalled();

    jest.advanceTimersByTime(1);
    expect(flushMock).toHaveBeenCalledTimes(1);
  });

  it("immediately flushes pending signal when app moves to background", () => {
    const flushMock = jest.fn();
    let timerId: any = null;
    let pending: { garmentId: string; action: string } | null = null;

    const startSignal = (garmentId: string, action: string) => {
      pending = { garmentId, action };
      timerId = setTimeout(() => {
        if (pending) {
          flushMock(pending);
          pending = null;
        }
      }, 5000);
    };

    const onAppStateChange = (state: string) => {
      if (state === "background" || state === "inactive") {
        if (timerId) {
          clearTimeout(timerId);
          timerId = null;
        }
        if (pending) {
          flushMock(pending);
          pending = null;
        }
      }
    };

    startSignal("garment-999", "not_interested");
    expect(flushMock).not.toHaveBeenCalled();

    // App transitions to background after 1.5 seconds
    jest.advanceTimersByTime(1500);
    onAppStateChange("background");

    expect(flushMock).toHaveBeenCalledTimes(1);
    expect(flushMock).toHaveBeenCalledWith({
      garmentId: "garment-999",
      action: "not_interested",
    });

    // Advance remainder of 5000ms - callback must not be invoked again
    jest.advanceTimersByTime(5000);
    expect(flushMock).toHaveBeenCalledTimes(1);
  });
});

describe("Onboarding Gating and Routing Architecture", () => {
  function computeTargetRoute(
    hasSession: boolean,
    onboarding: { complete: boolean; missing: string[] } | null,
    currentSegments: string[]
  ): string | null {
    const inAuthGroup = currentSegments[0] === "(auth)";
    const inOnboardingGroup = currentSegments[0] === "onboarding";

    if (!hasSession && !inAuthGroup) {
      return "/(auth)/sign-in";
    }
    if (hasSession && inAuthGroup) {
      return "/(tabs)/feed";
    }
    if (hasSession && onboarding) {
      if (!onboarding.complete) {
        const missing = onboarding.missing || [];
        if (missing.includes("consent") && currentSegments[1] !== "consent") {
          return "/onboarding/consent";
        }
        if (
          missing.includes("profile") &&
          currentSegments[1] !== "profile" &&
          !missing.includes("consent")
        ) {
          return "/onboarding/profile";
        }
        if (
          missing.includes("style_quiz") &&
          currentSegments[1] !== "quiz" &&
          !missing.includes("consent") &&
          !missing.includes("profile")
        ) {
          return "/onboarding/quiz";
        }
        if (
          missing.includes("photo") &&
          currentSegments[1] !== "capture" &&
          !missing.includes("consent") &&
          !missing.includes("profile") &&
          !missing.includes("style_quiz")
        ) {
          return "/onboarding/capture";
        }
      } else if (inOnboardingGroup) {
        return "/(tabs)/feed";
      }
    }
    return null;
  }

  it("prevents unconsented user from reaching feed and redirects to /onboarding/consent", () => {
    const target = computeTargetRoute(
      true,
      { complete: false, missing: ["consent", "profile", "style_quiz", "photo"] },
      ["(tabs)", "feed"]
    );
    expect(target).toBe("/onboarding/consent");
  });

  it("redirects user missing profile to /onboarding/profile", () => {
    const target = computeTargetRoute(
      true,
      { complete: false, missing: ["profile", "style_quiz", "photo"] },
      ["(tabs)", "feed"]
    );
    expect(target).toBe("/onboarding/profile");
  });

  it("redirects user missing style quiz to /onboarding/quiz", () => {
    const target = computeTargetRoute(
      true,
      { complete: false, missing: ["style_quiz", "photo"] },
      ["(tabs)", "feed"]
    );
    expect(target).toBe("/onboarding/quiz");
  });

  it("redirects user missing photo to /onboarding/capture", () => {
    const target = computeTargetRoute(
      true,
      { complete: false, missing: ["photo"] },
      ["(tabs)", "feed"]
    );
    expect(target).toBe("/onboarding/capture");
  });

  it("redirects completed onboarding users attempting to visit onboarding back to feed", () => {
    const target = computeTargetRoute(
      true,
      { complete: true, missing: [] },
      ["onboarding", "consent"]
    );
    expect(target).toBe("/(tabs)/feed");
  });

  it("allows completed user to remain on feed", () => {
    const target = computeTargetRoute(
      true,
      { complete: true, missing: [] },
      ["(tabs)", "feed"]
    );
    expect(target).toBeNull();
  });
});

describe("Impression Batching Queue", () => {
  it("deduplicates seen garments in a session", () => {
    const seen = new Set<string>();
    const queue: string[] = [];

    const record = (id: string) => {
      if (!id || seen.has(id)) return;
      seen.add(id);
      queue.push(id);
    };

    record("garment-1");
    record("garment-2");
    record("garment-1"); // Duplicate

    expect(queue).toEqual(["garment-1", "garment-2"]);
    expect(seen.size).toBe(2);
  });
});
