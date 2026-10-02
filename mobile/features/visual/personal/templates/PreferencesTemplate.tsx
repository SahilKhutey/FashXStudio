import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from "react-native";
import { PreferencesTemplateSpecContract, ExplicitPreferencesContract } from "../types";
import { PreferenceGroup } from "../components/PreferenceGroup";
import { PreferenceSelector } from "../components/PreferenceSelector";

interface PreferencesTemplateProps {
  data: PreferencesTemplateSpecContract;
  onToggleStyle?: (style: string) => void;
  onToggleCategory?: (category: string) => void;
  onToggleColor?: (color: string) => void;
  onToggleFit?: (fit: string) => void;
  onToggleMaterial?: (material: string) => void;
  onToggleContext?: (context: string) => void;
  onSaveChanges?: () => void;
  onDiscardChanges?: () => void;
  testID?: string;
}

export const PreferencesTemplate: React.FC<PreferencesTemplateProps> = ({
  data,
  onToggleStyle,
  onToggleCategory,
  onToggleColor,
  onToggleFit,
  onToggleMaterial,
  onToggleContext,
  onSaveChanges,
  onDiscardChanges,
  testID = "preferences-pr08",
}) => {
  return (
    <ScrollView testID={testID} style={styles.container}>
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Text style={styles.title}>Preferences</Text>
          {data.state === "saved" && (
            <Text testID="saved-confirmation" style={styles.savedBadge}>
              Saved ✓
            </Text>
          )}
          {data.state === "saving" && (
            <Text testID="saving-confirmation" style={styles.savingBadge}>
              Saving...
            </Text>
          )}
        </View>
        <Text style={styles.subtitle}>
          Explicit wardrobe and silhouette criteria governing recommendations and styling.
        </Text>
      </View>

      {/* Unsaved Changes Banner */}
      {data.has_unsaved_changes && (
        <View testID="pref-unsaved-banner" style={styles.unsavedBanner}>
          <Text style={styles.unsavedText}>Unsaved preference changes</Text>
          <View style={styles.bannerActions}>
            {onDiscardChanges && (
              <TouchableOpacity
                testID="pref-discard-btn"
                style={styles.discardBtn}
                onPress={onDiscardChanges}
                accessibilityRole="button"
                accessibilityLabel="Discard preference changes"
              >
                <Text style={styles.discardText}>Discard</Text>
              </TouchableOpacity>
            )}
            {onSaveChanges && (
              <TouchableOpacity
                testID="pref-save-btn"
                style={styles.saveBtn}
                onPress={onSaveChanges}
                accessibilityRole="button"
                accessibilityLabel="Save preference changes"
              >
                <Text style={styles.saveText}>Save</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>
      )}

      {/* Explicit Preferred Styles */}
      <PreferenceGroup
        title="Preferred Styles"
        subtitle="Aesthetic sensibilities prioritized in your feeds and outfit proposals."
        testID="pref-group-styles"
      >
        <PreferenceSelector
          options={data.available_styles}
          selectedOptions={data.explicit_preferences.styles}
          onToggleOption={onToggleStyle || (() => {})}
          testID="selector-styles"
        />
      </PreferenceGroup>

      {/* Wardrobe Categories */}
      <PreferenceGroup
        title="Focus Categories"
        subtitle="Garment categories you wear and explore most frequently."
        testID="pref-group-categories"
      >
        <PreferenceSelector
          options={data.available_categories}
          selectedOptions={data.explicit_preferences.categories}
          onToggleOption={onToggleCategory || (() => {})}
          testID="selector-categories"
        />
      </PreferenceGroup>

      {/* Color Palette */}
      <PreferenceGroup
        title="Color Palettes"
        subtitle="Foundational hues and tonal harmonies you prefer."
        testID="pref-group-colors"
      >
        <PreferenceSelector
          options={data.available_colors}
          selectedOptions={data.explicit_preferences.colors}
          onToggleOption={onToggleColor || (() => {})}
          testID="selector-colors"
        />
      </PreferenceGroup>

      {/* Fits & Silhouettes */}
      <PreferenceGroup
        title="Preferred Fits & Silhouettes"
        subtitle="Structural cuts aligning with your authentic proportions."
        testID="pref-group-fits"
      >
        <PreferenceSelector
          options={data.available_fits}
          selectedOptions={data.explicit_preferences.fits}
          onToggleOption={onToggleFit || (() => {})}
          testID="selector-fits"
        />
      </PreferenceGroup>

      {/* Inferred Preferences Box (Strictly Separate per Section 13.4, 13.5) */}
      <View style={styles.inferredCard} testID="inferred-preferences-card">
        <Text style={styles.inferredHeader}>SYSTEM OBSERVATIONS (INFERRED)</Text>
        <Text style={styles.inferredNotice}>
          {data.inferred_preferences.observation_notice}
        </Text>
        <View style={styles.inferredRow}>
          <Text style={styles.inferredKey}>Frequent Styles:</Text>
          <Text style={styles.inferredVal}>
            {data.inferred_preferences.frequently_viewed_styles.join(", ") || "None"}
          </Text>
        </View>
        <View style={styles.inferredRow}>
          <Text style={styles.inferredKey}>Frequent Categories:</Text>
          <Text style={styles.inferredVal}>
            {data.inferred_preferences.frequently_viewed_categories.join(", ") || "None"}
          </Text>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F2F2F7",
    padding: 16,
  },
  header: {
    marginBottom: 12,
  },
  titleRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 4,
  },
  title: {
    fontSize: 22,
    fontWeight: "700",
    color: "#1C1C1E",
    letterSpacing: -0.4,
  },
  savedBadge: {
    fontSize: 12,
    fontWeight: "700",
    color: "#34C759",
  },
  savingBadge: {
    fontSize: 12,
    fontWeight: "600",
    color: "#8E8E93",
  },
  subtitle: {
    fontSize: 13,
    color: "#636366",
    lineHeight: 18,
  },
  unsavedBanner: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "#FFF8E6",
    borderWidth: 1,
    borderColor: "#FFE082",
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  unsavedText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#B25E00",
  },
  bannerActions: {
    flexDirection: "row",
    gap: 8,
  },
  discardBtn: {
    borderWidth: 1,
    borderColor: "#C7C7CC",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 4,
  },
  discardText: {
    fontSize: 11,
    fontWeight: "600",
    color: "#636366",
  },
  saveBtn: {
    backgroundColor: "#1C1C1E",
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 4,
  },
  saveText: {
    color: "#FFFFFF",
    fontSize: 11,
    fontWeight: "600",
  },
  inferredCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    padding: 16,
    marginVertical: 12,
    marginBottom: 32,
  },
  inferredHeader: {
    fontSize: 10,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  inferredNotice: {
    fontSize: 11,
    color: "#8E8E93",
    lineHeight: 15,
    marginBottom: 12,
  },
  inferredRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 6,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderColor: "#E5E5EA",
  },
  inferredKey: {
    fontSize: 12,
    color: "#636366",
  },
  inferredVal: {
    fontSize: 12,
    fontWeight: "600",
    color: "#1C1C1E",
  },
});
