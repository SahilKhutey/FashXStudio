import { useEffect } from "react";
import { BackHandler } from "react-native";
import { Stack, usePathname } from "expo-router";

export default function OnboardingLayout() {
  const path = usePathname();
  useEffect(() => {
    // True swallows back on consent screen (fail-closed, cannot bypass consent via hardware back)
    const sub = BackHandler.addEventListener("hardwareBackPress", () => path.endsWith("/consent"));
    return () => sub.remove();
  }, [path]);

  return <Stack screenOptions={{ headerShown: false, gestureEnabled: false }} />;
}
