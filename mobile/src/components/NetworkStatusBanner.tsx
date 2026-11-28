import React from "react";
import { Text, View, StyleSheet } from "react-native";
import { useNetworkStatus } from "../hooks/useNetworkStatus";

type Props = {
  forceOffline?: boolean;
};

export function NetworkStatusBanner({ forceOffline }: Props) {
  const { offline } = useNetworkStatus();
  const isOffline = forceOffline ?? offline;

  if (!isOffline) return null;

  return (
    <View
      style={styles.banner}
      accessibilityRole="alert"
      accessibilityLiveRegion="polite"
    >
      <Text style={styles.text}>
        You&apos;re offline. Some features may be unavailable.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    padding: 10,
    backgroundColor: "#7A3D00",
  },
  text: {
    color: "#FFFFFF",
    textAlign: "center",
    fontSize: 13,
    fontWeight: "600",
  },
});
