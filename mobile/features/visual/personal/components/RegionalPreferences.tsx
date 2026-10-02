import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { RegionalPreferencesContract } from "../types";
import { PreferenceSwitch } from "./PreferenceSwitch";

interface RegionalPreferencesProps {
  settings: RegionalPreferencesContract;
  availableCountries: string[];
  availableRegions: string[];
  onUpdateSettings: (newSettings: Partial<RegionalPreferencesContract>) => void;
  testID?: string;
}

export const RegionalPreferences: React.FC<RegionalPreferencesProps> = ({
  settings,
  availableCountries,
  availableRegions,
  onUpdateSettings,
  testID = "regional-preferences",
}) => {
  return (
    <View testID={testID} style={styles.container}>
      <Text style={styles.header}>REGIONAL DISCOVERY & CONTEXT</Text>

      <View style={styles.disclaimerBox} testID="regional-disclaimer-box">
        <Text style={styles.disclaimerTitle}>GEOGRAPHY BOUNDARY</Text>
        <Text style={styles.disclaimerText}>{settings.disclaimer}</Text>
      </View>

      <PreferenceSwitch
        testID="pref-regional-discovery"
        label="Regional Discovery"
        description="Filter runway looks and street trends by your selected fashion capital."
        value={settings.regional_discovery_enabled}
        onValueChange={(val) => onUpdateSettings({ regional_discovery_enabled: val })}
      />

      <View style={styles.fieldSection}>
        <Text style={styles.fieldLabel}>PREFERRED FASHION CAPITAL</Text>
        <View style={styles.chipsRow}>
          {availableCountries.map((country) => {
            const isSelected = settings.preferred_country === country;
            return (
              <TouchableOpacity
                key={country}
                testID={`country-${country.toLowerCase().replace(/\s+/g, "-")}`}
                style={[styles.chip, isSelected ? styles.selectedChip : styles.unselectedChip]}
                onPress={() => onUpdateSettings({ preferred_country: country })}
                accessibilityRole="button"
                accessibilityLabel={`${country}, ${isSelected ? "selected" : "not selected"}`}
              >
                <Text
                  style={[
                    styles.chipText,
                    isSelected ? styles.selectedChipText : styles.unselectedChipText,
                  ]}
                >
                  {country}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      <View style={styles.infoRow}>
        <Text style={styles.infoKey}>Delivery Region:</Text>
        <Text style={styles.infoVal}>{settings.delivery_region}</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    marginVertical: 8,
  },
  header: {
    fontSize: 11,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  disclaimerBox: {
    padding: 10,
    backgroundColor: "#F2F2F7",
    borderRadius: 6,
    marginBottom: 12,
  },
  disclaimerTitle: {
    fontSize: 9,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 0.6,
    marginBottom: 2,
  },
  disclaimerText: {
    fontSize: 11,
    color: "#636366",
    lineHeight: 15,
  },
  fieldSection: {
    marginVertical: 12,
  },
  fieldLabel: {
    fontSize: 11,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  chipsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
  },
  selectedChip: {
    backgroundColor: "#1C1C1E",
    borderColor: "#1C1C1E",
  },
  unselectedChip: {
    backgroundColor: "#F2F2F7",
    borderColor: "#E5E5EA",
  },
  chipText: {
    fontSize: 12,
    fontWeight: "600",
  },
  selectedChipText: {
    color: "#FFFFFF",
  },
  unselectedChipText: {
    color: "#1C1C1E",
  },
  infoRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderColor: "#E5E5EA",
    marginTop: 8,
  },
  infoKey: {
    fontSize: 13,
    color: "#636366",
  },
  infoVal: {
    fontSize: 13,
    fontWeight: "600",
    color: "#1C1C1E",
  },
});
