import React from "react";
import { Pressable, StyleSheet, View } from "react-native";
import { Image } from "expo-image";
import { AppText } from "./AppText";
import { Button } from "./Button";
import { useDesignTokens } from "../useDesignTokens";

export type ProductCardProps = {
  id: string;
  title: string;
  brand: string;
  imageUrl?: string | null;
  priceMinor: number;
  currency?: string;
  tryOnSupported?: boolean;
  saved?: boolean;
  saving?: boolean;
  onOpen: () => void;
  onSave: () => void;
  onTryOn?: () => void;
};

export function ProductCard({
  title,
  brand,
  imageUrl,
  priceMinor,
  currency = "INR",
  tryOnSupported = false,
  saved = false,
  saving = false,
  onOpen,
  onSave,
  onTryOn,
}: ProductCardProps) {
  const { colors, radius, spacing } = useDesignTokens();

  const price = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(priceMinor / 100);

  return (
    <View
      style={[
        styles.card,
        {
          backgroundColor: colors.surface,
          borderColor: colors.border,
          borderRadius: radius.lg,
        },
      ]}
    >
      <Pressable
        onPress={onOpen}
        accessibilityRole="button"
        accessibilityLabel={`View ${brand} ${title}`}
      >
        <View
          style={[
            styles.imageContainer,
            { backgroundColor: colors.surfaceSecondary },
          ]}
        >
          {imageUrl ? (
            <Image
              source={{ uri: imageUrl }}
              style={styles.image}
              contentFit="cover"
              transition={200}
            />
          ) : (
            <View style={styles.placeholder}>
              <AppText color="textMuted">Image unavailable</AppText>
            </View>
          )}

          {tryOnSupported && (
            <View
              style={[
                styles.badge,
                { backgroundColor: colors.brand },
              ]}
            >
              <AppText variant="caption" color="textOnBrand">
                TRY ON
              </AppText>
            </View>
          )}
        </View>
      </Pressable>

      <View style={{ padding: spacing[3] }}>
        <AppText
          variant="caption"
          color="textMuted"
          numberOfLines={1}
        >
          {brand.toUpperCase()}
        </AppText>

        <AppText variant="body" numberOfLines={2}>
          {title}
        </AppText>

        <AppText variant="heading3">
          {price}
        </AppText>

        <View style={styles.actions}>
          <View style={styles.action}>
            <Button
              title={saved ? "Saved" : "Save"}
              variant="outline"
              loading={saving}
              disabled={saved}
              onPress={onSave}
            />
          </View>

          {tryOnSupported && onTryOn && (
            <View style={styles.action}>
              <Button title="Try On" onPress={onTryOn} />
            </View>
          )}
        </View>
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
  imageContainer: {
    width: "100%",
    aspectRatio: 0.78,
    overflow: "hidden",
  },
  image: {
    width: "100%",
    height: "100%",
  },
  placeholder: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  badge: {
    position: "absolute",
    top: 10,
    left: 10,
    paddingHorizontal: 9,
    paddingVertical: 5,
    borderRadius: 6,
  },
  actions: {
    flexDirection: "row",
    gap: 8,
    marginTop: 12,
  },
  action: {
    flex: 1,
  },
});
