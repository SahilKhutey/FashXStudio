export type RouteDecision =
  | { type: "wait" }
  | { type: "stay" }
  | { type: "replace"; href: string };

export type RoutePolicyInput = {
  authLoading: boolean;
  configLoading: boolean;
  hasSession: boolean;
  segments: string[];
  onboarding?: {
    complete: boolean;
    missing: string[];
  } | null;
};

export function getRouteDecision(
  input: RoutePolicyInput,
): RouteDecision {
  const {
    authLoading,
    configLoading,
    hasSession,
    segments,
    onboarding,
  } = input;

  if (authLoading || configLoading) {
    return { type: "wait" };
  }

  const root = segments[0];
  const subroute = segments[1];

  const inAuth = root === "(auth)";
  const inOnboarding = root === "onboarding";

  if (!hasSession) {
    return inAuth
      ? { type: "stay" }
      : { type: "replace", href: "/(auth)/sign-in" };
  }

  if (inAuth) {
    return { type: "replace", href: "/(tabs)/feed" };
  }

  if (onboarding && !onboarding.complete) {
    const missing = new Set(onboarding.missing);

    const requiredRoute = missing.has("consent")
      ? "/onboarding/consent"
      : missing.has("profile")
        ? "/onboarding/profile"
        : missing.has("style_quiz")
          ? "/onboarding/quiz"
          : missing.has("photo")
            ? "/onboarding/capture"
            : null;

    if (requiredRoute) {
      const requiredSegment = requiredRoute.split("/").at(-1);
      if (subroute !== requiredSegment) {
        return { type: "replace", href: requiredRoute };
      }

      return { type: "stay" };
    }
  }

  if (onboarding?.complete && inOnboarding) {
    return { type: "replace", href: "/(tabs)/feed" };
  }

  return { type: "stay" };
}
