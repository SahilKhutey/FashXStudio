import React, { useState } from "react";
import { Dimensions, FlatList, StyleSheet, Text, View } from "react-native";
import { Image } from "expo-image";
import type { ProductImage } from "../types";

const SCREEN_WIDTH = Dimensions.get("window").width;

export function ProductGallery({ images }: { images: ProductImage[] }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const sorted = [...images].sort((a, b) => a.position - b.position);

  if (!sorted.length) {
    return (
      <View style={styles.fallback}>
        <Text style={styles.fallbackText}>Product image unavailable</Text>
      </View>
    );
  }

  return (
    <View>
      <FlatList
        data={sorted}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        keyExtractor={(item) => item.id}
        onMomentumScrollEnd={(event) => {
          const index = Math.round(
            event.nativeEvent.contentOffset.x / SCREEN_WIDTH,
          );
          setActiveIndex(index);
        }}
        renderItem={({ item }) => (
          <Image
            source={{ uri: item.url }}
            accessibilityLabel={item.alt_text}
            contentFit="contain"
            transition={150}
            style={styles.image}
          />
        )}
      />
      <Text style={styles.counter}>
        {activeIndex + 1} / {sorted.length}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  fallback: {
    width: SCREEN_WIDTH,
    height: SCREEN_WIDTH * 1.1,
    backgroundColor: "#ECECEC",
    alignItems: "center",
    justifyContent: "center",
  },
  fallbackText: { color: "#6B7280", fontSize: 13 },
  image: {
    width: SCREEN_WIDTH,
    height: SCREEN_WIDTH * 1.1,
    backgroundColor: "#F5F5F5",
  },
  counter: {
    textAlign: "center",
    padding: 8,
    fontSize: 12,
    color: "#6B7280",
  },
});
