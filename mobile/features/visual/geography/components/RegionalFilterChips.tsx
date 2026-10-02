import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from "react-native";

interface RegionalFilterChipsProps {
  selectedRegions: Array<{ id: string; name: string }>;
  onRemoveRegion?: (regionId: string) => void;
  onClearAll?: () => void;
  testID?: string;
}

export const RegionalFilterChips: React.FC<RegionalFilterChipsProps> = ({
  selectedRegions,
  onRemoveRegion,
  onClearAll,
  testID = "regional-filter-chips",
}) => {
  if (selectedRegions.length === 0) return null;

  return (
    <View testID={testID} style={styles.container}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.scroll}>
        {selectedRegions.map((reg) => (
          <TouchableOpacity
            key={reg.id}
            testID={`chip-remove-${reg.id}`}
            style={styles.chip}
            onPress={() => onRemoveRegion?.(reg.id)}
            accessibilityRole="button"
            accessibilityLabel={`Remove filter: ${reg.name}`}
          >
            <Text style={styles.chipText}>{reg.name}</Text>
            <Text style={styles.removeIcon}>✕</Text>
          </TouchableOpacity>
        ))}

        {selectedRegions.length > 1 && onClearAll && (
          <TouchableOpacity
            testID="clear-all-regions-btn"
            style={styles.clearBtn}
            onPress={onClearAll}
          >
            <Text style={styles.clearBtnText}>Clear All</Text>
          </TouchableOpacity>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingVertical: 8,
    backgroundColor: "#ffffff",
    borderBottomWidth: 1,
    borderBottomColor: "#f3f4f6",
  },
  scroll: {
    paddingHorizontal: 16,
    gap: 8,
    alignItems: "center",
  },
  chip: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#111111",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    gap: 6,
  },
  chipText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#ffffff",
  },
  removeIcon: {
    fontSize: 10,
    fontWeight: "700",
    color: "#d1d5db",
  },
  clearBtn: {
    paddingHorizontal: 8,
    paddingVertical: 6,
  },
  clearBtnText: {
    fontSize: 12,
    color: "#6b7280",
    fontWeight: "600",
  },
});
