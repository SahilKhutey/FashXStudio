import React, { useState } from "react";
import { View, Text, StyleSheet } from "react-native";
import { Image } from "expo-image";

type Props = {
  url: string | null | undefined;
  alt: string;
  aspectRatio?: number;
};

export function ProductImage({ url, alt, aspectRatio = 0.78 }: Props) {
  const [failed, setFailed] = useState(false);

  if (!url || failed) {
    return (
      <View style={[styles.fallback, { aspectRatio }]}>
        <Text style={styles.fallbackText}>Image unavailable</Text>
      </View>
    );
  }

  return (
    <Image
      source={{ uri: url }}
      accessibilityLabel={alt}
      contentFit="cover"
      onError={() => setFailed(true)}
      style={[styles.image, { aspectRatio }]}
    />
  );
}

const styles = StyleSheet.create({
  image: {
    width: "100%",
    borderRadius: 10,
    backgroundColor: "#F3F4F6",
  },
  fallback: {
    width: "100%",
    backgroundColor: "#F3F4F6",
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  fallbackText: {
    fontSize: 11,
    color: "#6B7280",
  },
});
