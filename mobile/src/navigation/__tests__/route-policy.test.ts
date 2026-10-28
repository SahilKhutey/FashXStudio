import { getRouteDecision } from "../route-policy";

describe("getRouteDecision", () => {
  it("waits until authentication and config have loaded", () => {
    expect(
      getRouteDecision({
        authLoading: true,
        configLoading: false,
        hasSession: false,
        segments: [],
      }),
    ).toEqual({ type: "wait" });

    expect(
      getRouteDecision({
        authLoading: false,
        configLoading: true,
        hasSession: false,
        segments: [],
      }),
    ).toEqual({ type: "wait" });
  });

  it("redirects unauthenticated users to sign-in", () => {
    expect(
      getRouteDecision({
        authLoading: false,
        configLoading: false,
        hasSession: false,
        segments: ["(tabs)", "feed"],
      }),
    ).toEqual({
      type: "replace",
      href: "/(auth)/sign-in",
    });
  });

  it("keeps unauthenticated users on auth routes", () => {
    expect(
      getRouteDecision({
        authLoading: false,
        configLoading: false,
        hasSession: false,
        segments: ["(auth)", "sign-in"],
      }),
    ).toEqual({ type: "stay" });
  });

  it("redirects signed-in users away from auth routes", () => {
    expect(
      getRouteDecision({
        authLoading: false,
        configLoading: false,
        hasSession: true,
        segments: ["(auth)", "sign-in"],
      }),
    ).toEqual({
      type: "replace",
      href: "/(tabs)/feed",
    });
  });

  it("sends a user missing consent to the consent screen", () => {
    expect(
      getRouteDecision({
        authLoading: false,
        configLoading: false,
        hasSession: true,
        segments: ["(tabs)", "feed"],
        onboarding: {
          complete: false,
          missing: ["consent", "profile"],
        },
      }),
    ).toEqual({
      type: "replace",
      href: "/onboarding/consent",
    });
  });

  it("keeps a user on the required onboarding step", () => {
    expect(
      getRouteDecision({
        authLoading: false,
        configLoading: false,
        hasSession: true,
        segments: ["onboarding", "profile"],
        onboarding: {
          complete: false,
          missing: ["profile"],
        },
      }),
    ).toEqual({ type: "stay" });
  });

  it("routes missing style_quiz to quiz screen", () => {
    expect(
      getRouteDecision({
        authLoading: false,
        configLoading: false,
        hasSession: true,
        segments: ["(tabs)", "feed"],
        onboarding: {
          complete: false,
          missing: ["style_quiz"],
        },
      }),
    ).toEqual({
      type: "replace",
      href: "/onboarding/quiz",
    });
  });

  it("routes missing photo to capture screen", () => {
    expect(
      getRouteDecision({
        authLoading: false,
        configLoading: false,
        hasSession: true,
        segments: ["(tabs)", "feed"],
        onboarding: {
          complete: false,
          missing: ["photo"],
        },
      }),
    ).toEqual({
      type: "replace",
      href: "/onboarding/capture",
    });
  });

  it("sends completed users out of onboarding", () => {
    expect(
      getRouteDecision({
        authLoading: false,
        configLoading: false,
        hasSession: true,
        segments: ["onboarding", "profile"],
        onboarding: {
          complete: true,
          missing: [],
        },
      }),
    ).toEqual({
      type: "replace",
      href: "/(tabs)/feed",
    });
  });

  it("allows completed user to remain on main tabs", () => {
    expect(
      getRouteDecision({
        authLoading: false,
        configLoading: false,
        hasSession: true,
        segments: ["(tabs)", "feed"],
        onboarding: {
          complete: true,
          missing: [],
        },
      }),
    ).toEqual({ type: "stay" });
  });
});
