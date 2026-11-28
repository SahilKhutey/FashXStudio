import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  type StyleProp,
  type ImageStyle,
} from "react-native";
import { Image } from "expo-image";

type Props = {
  uri?: string | null;
  accessibilityLabel: string;
  style?: StyleProp<ImageStyle>;
  contentFit?: "cover" | "contain" | "fill";
};

export function ImageWithFallback({
  uri,
  accessibilityLabel,
  style,
  contentFit = "cover",
}: Props) {
  const [failedUri, setFailedUri] = useState<string | null>(null);
  const usableUri = uri && failedUri !== uri ? uri : null;

  return (
    <View style={styles.container}>
      {usableUri ? (
        <Image
          source={{ uri: usableUri }}
          style={[styles.image, style]}
          contentFit={contentFit}
          transition={150}
          cachePolicy="memory-disk"
          accessibilityLabel={accessibilityLabel}
          onError={() => setFailedUri(usableUri)}
        />
      ) : (
        <View
          style={styles.fallback}
          accessible
          accessibilityRole="image"
          accessibilityLabel={`${accessibilityLabel}. Image unavailable.`}
        >
          <Text style={styles.fallbackText}>Image unavailable</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { overflow: "hidden" },
  image: { width: "100%", height: "100%" },
  fallback: {
    minHeight: 120,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#E5E7EB",
  },
  fallbackText: { color: "#4B5563", fontSize: 12 },
});
