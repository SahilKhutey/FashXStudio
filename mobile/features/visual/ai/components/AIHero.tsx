import React from "react";
import { View, Text, StyleSheet } from "react-native";

interface AIHeroProps {
  title: string;
  subtitle: string;
  testID?: string;
}

export const AIHero: React.FC<AIHeroProps> = ({
  title,
  subtitle,
  testID = "ai-hero-component",
}) => {
  return (
    <View testID={testID} style={styles.container}>
      <View style={styles.badge}>
        <Text style={styles.badgeText}>INTELLIGENCE STUDIO</Text>
      </View>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.subtitle}>{subtitle}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingVertical: 20,
    paddingHorizontal: 16,
    backgroundColor: "#FFFFFF",
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: "#E5E5EA",
  },
  badge: {
    alignSelf: "flex-start",
    backgroundColor: "#F2F2F7",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    marginBottom: 8,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 1.1,
    color: "#5856D6",
  },
  title: {
    fontSize: 26,
    fontWeight: "700",
    color: "#1C1C1E",
    letterSpacing: -0.6,
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 14,
    color: "#636366",
    lineHeight: 20,
  },
});
