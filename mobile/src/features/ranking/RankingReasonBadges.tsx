import React from "react";
import { StyleSheet, Text, View } from "react-native";

interface RankingReasonBadgesProps {
  reasonLabels: string[];
  selectedSizeAvailable?: boolean;
  isSponsored?: boolean;
}

export function RankingReasonBadges({
  reasonLabels,
  selectedSizeAvailable = false,
  isSponsored = false,
}: RankingReasonBadgesProps) {
  if (!reasonLabels.length && !isSponsored && !selectedSizeAvailable) {
    return null;
  }

  return (
    <View style={styles.container} accessibilityRole="summary">
      {isSponsored ? (
        <View style={[styles.badge, styles.sponsoredBadge]}>
          <Text style={styles.badgeText}>Sponsored</Text>
        </View>
      ) : null}
      {selectedSizeAvailable ? (
        <View style={[styles.badge, styles.sizeBadge]}>
          <Text style={styles.badgeText}>Selected size available</Text>
        </View>
      ) : null}
      {reasonLabels.map((label) => (
        <View key={label} style={styles.badge}>
          <Text style={styles.badgeText}>{label}</Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
    marginTop: 6,
  },
  badge: {
    backgroundColor: "#F2F4F7",
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  sizeBadge: {
    backgroundColor: "#E8F5E9",
  },
  sponsoredBadge: {
    backgroundColor: "#FFF8E1",
  },
  badgeText: {
    fontSize: 12,
    color: "#1F2937",
  },
});
