import React, { useState } from "react";
import { useRouter } from "expo-router";
import { WelcomeScreen } from "../../src/features/onboarding/screens/WelcomeScreen";
import { ProductIntroScreen } from "../../src/features/onboarding/screens/ProductIntroScreen";

export default function OnboardingWelcomeRoute() {
  const router = useRouter();
  const [stage, setStage] = useState<"welcome" | "intro">("welcome");

  if (stage === "welcome") {
    return <WelcomeScreen onContinue={() => setStage("intro")} />;
  }

  return (
    <ProductIntroScreen
      onContinue={() => router.push("/onboarding/consent")}
      onSkip={() => router.push("/onboarding/consent")}
    />
  );
}
