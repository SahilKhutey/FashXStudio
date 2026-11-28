import { useEffect } from "react";
import { BackHandler, Platform } from "react-native";

export function useAndroidBackHandler(
  enabled: boolean,
  onBack: () => boolean,
) {
  useEffect(() => {
    if (Platform.OS !== "android" || !enabled) {
      return;
    }

    const subscription = BackHandler.addEventListener(
      "hardwareBackPress",
      onBack,
    );

    return () => subscription.remove();
  }, [enabled, onBack]);
}
