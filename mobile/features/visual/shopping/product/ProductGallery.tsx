/**
 * ProductGallery Component — Phase 07 (Section 7.24).
 *
 * Renders primary product media in standard 3:4 portrait ratio
 * with interactive thumbnail strip selector.
 */

import React, { useState } from "react";
import { Image, ScrollView, StyleSheet, TouchableOpacity, View } from "react-native";
import { defaultDesignTokens } from "../../tokens";

export interface ProductGalleryProps {
  mediaGallery: string[];
}

export const ProductGallery: React.FC<ProductGalleryProps> = ({ mediaGallery }) => {
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const activeUri = mediaGallery[selectedIndex] || mediaGallery[0];

  return (
    <View style={styles.container}>
      {/* Primary 3:4 media view */}
      <View style={styles.primaryImageContainer}>
        {activeUri ? (
          <Image
            source={{ uri: activeUri }}
            style={styles.primaryImage}
            resizeMode="cover"
            accessibilityLabel={`Product view image ${selectedIndex + 1}`}
          />
        ) : (
          <View style={styles.placeholder} />
        )}
      </View>

      {/* Thumbnail Strip */}
      {mediaGallery.length > 1 ? (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.thumbnailStrip}
        >
          {mediaGallery.map((uri, index) => {
            const isSelected = index === selectedIndex;
            return (
              <TouchableOpacity
                key={`${uri}-${index}`}
                accessibilityLabel={`View image thumbnail ${index + 1}`}
                onPress={() => setSelectedIndex(index)}
                style={[styles.thumbnailButton, isSelected && styles.thumbnailSelected]}
              >
                <Image source={{ uri }} style={styles.thumbnailImage} resizeMode="cover" />
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    gap: 12,
  },
  primaryImageContainer: {
    width: "100%",
    aspectRatio: 3 / 4,
    borderRadius: 12,
    overflow: "hidden",
    backgroundColor: defaultDesignTokens.neutral.neutral100,
  },
  primaryImage: {
    width: "100%",
    height: "100%",
  },
  placeholder: {
    flex: 1,
    backgroundColor: defaultDesignTokens.neutral.neutral200,
  },
  thumbnailStrip: {
    flexDirection: "row",
    gap: 8,
    paddingVertical: 4,
  },
  thumbnailButton: {
    width: 60,
    height: 80,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: "transparent",
    overflow: "hidden",
  },
  thumbnailSelected: {
    borderColor: defaultDesignTokens.brand.primary,
  },
  thumbnailImage: {
    width: "100%",
    height: "100%",
  },
});
