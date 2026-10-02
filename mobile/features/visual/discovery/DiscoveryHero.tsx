/**
 * DiscoveryHero Component — Phase 08 (Section 8.6).
 *
 * Immersive hero visual gateway with title, subtitle,
 * primary action trigger, and optional secondary action trigger.
 */

import React from "react";
import { ImageBackground, StyleSheet, Text, View } from "react-native";
import { defaultDesignTokens } from "../../tokens";
import { DiscoveryHero as DiscoveryHeroType } from "./types";
import { Button } from "../../components/Button";

export interface DiscoveryHeroProps {
  hero: DiscoveryHeroType;
  onPrimaryAction: (route: string) => void;
  onSecondaryAction?: (route: string) => void;
}

export const DiscoveryHero: React.FC<DiscoveryHeroProps> = ({
  hero,
  onPrimaryAction,
  onSecondaryAction,
}) => {
  return (
    <View style={styles.container}>
      <ImageBackground
        source={{ uri: hero.mediaUri }}
        style={styles.backgroundImage}
        imageStyle={styles.imageStyle}
        resizeMode="cover"
      >
        <View style={styles.overlay} />

        <View style={styles.content}>
          <Text style={styles.title}>{hero.title}</Text>
          <Text style={styles.subtitle}>{hero.subtitle}</Text>

          <View style={styles.actions}>
            <Button
              label={hero.primaryActionLabel}
              variant="primary"
              size="md"
              onPress={() => onPrimaryAction(hero.primaryActionRoute)}
            />
            {hero.secondaryActionLabel && hero.secondaryActionRoute ? (
              <Button
                label={hero.secondaryActionLabel}
                variant="outline"
                size="md"
                onPress={() => onSecondaryAction?.(hero.secondaryActionRoute!)}
              />
            ) : null}
          </View>
        </View>
      </ImageBackground>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: "100%",
    height: 380,
    borderRadius: 16,
    overflow: "hidden",
  },
  backgroundImage: {
    width: "100%",
    height: "100%",
    justifyContent: "flex-end",
  },
  imageStyle: {
    borderRadius: 16,
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(0, 0, 0, 0.45)",
    borderRadius: 16,
  },
  content: {
    padding: 20,
    gap: 8,
  },
  title: {
    fontSize: 26,
    fontWeight: "800",
    color: defaultDesignTokens.surfaces.surfaceLight,
    lineHeight: 32,
  },
  subtitle: {
    fontSize: 14,
    color: "rgba(255, 255, 255, 0.85)",
    lineHeight: 20,
    marginBottom: 8,
  },
  actions: {
    flexDirection: "row",
    gap: 12,
  },
});
