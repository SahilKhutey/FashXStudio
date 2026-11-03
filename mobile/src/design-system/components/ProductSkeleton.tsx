import React from "react";
import { StyleSheet, View, type ViewStyle } from "react-native";
import { useDesignTokens } from "../useDesignTokens";

export type ProductSkeletonProps = {
  style?: ViewStyle;
};

export function ProductSkeleton({ style }: ProductSkeletonProps) {
  const { colors, radius, spacing } = useDesignTokens();

  return (
    <View
      style={[
        styles.card,
        {
          backgroundColor: colors.surface,
          borderColor: colors.border,
          borderRadius: radius.lg,
        },
        style,
      ]}
      accessibilityRole="none"
      accessibilityLabel="Loading product placeholder"
    >
      <View
        style={[
          styles.imageSkeleton,
          { backgroundColor: colors.skeleton },
        ]}
      />
      <View style={{ padding: spacing[3], gap: spacing[2] }}>
        <View
          style={[
            styles.lineShort,
            { backgroundColor: colors.skeleton, borderRadius: radius.sm },
          ]}
        />
        <View
          style={[
            styles.lineMedium,
            { backgroundColor: colors.skeleton, borderRadius: radius.sm },
          ]}
        />
        <View
          style={[
            styles.linePrice,
            { backgroundColor: colors.skeleton, borderRadius: radius.sm },
          ]}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    overflow: "hidden",
    borderWidth: 1,
  },
  imageSkeleton: {
    width: "100%",
    aspectRatio: 0.78,
  },
  lineShort: {
    width: "40%",
    height: 12,
  },
  lineMedium: {
    width: "80%",
    height: 16,
  },
  linePrice: {
    width: "50%",
    height: 18,
    marginTop: 4,
  },
});
