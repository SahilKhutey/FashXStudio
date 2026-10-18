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

describe("Try-on Polling Exponential Backoff", () => {
  function getBackoffMs(pollCount: number): number {
    return Math.min(1000 * Math.pow(2, pollCount), 5000);
  }

  it("calculates exponential backoff capped at 5000ms", () => {
    expect(getBackoffMs(0)).toBe(1000);
    expect(getBackoffMs(1)).toBe(2000);
    expect(getBackoffMs(2)).toBe(4000);
    expect(getBackoffMs(3)).toBe(5000);
    expect(getBackoffMs(4)).toBe(5000);
    expect(getBackoffMs(10)).toBe(5000);
  });
});

describe("Signal 5-second Undo Timer", () => {
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
