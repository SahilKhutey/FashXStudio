import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { PersonalState } from "../types";

interface SettingsSectionProps {
  title: string;
  hasUnsavedChanges?: boolean;
  saveState?: PersonalState;
  onSave?: () => void;
  onDiscard?: () => void;
  children: React.ReactNode;
  testID?: string;
}

export const SettingsSection: React.FC<SettingsSectionProps> = ({
  title,
  hasUnsavedChanges = false,
  saveState = "loaded",
  onSave,
  onDiscard,
  children,
  testID = "settings-section",
}) => {
  return (
    <View testID={testID} style={styles.container}>
      <View style={styles.headerRow}>
        <Text style={styles.title}>{title}</Text>
        {saveState === "saving" && (
          <Text testID="saving-indicator" style={styles.stateSaving}>
            Saving...
          </Text>
        )}
        {saveState === "saved" && (
          <Text testID="saved-indicator" style={styles.stateSaved}>
            Saved ✓
          </Text>
        )}
      </View>

      {hasUnsavedChanges && (
        <View testID="unsaved-changes-banner" style={styles.unsavedBanner}>
          <Text style={styles.unsavedText}>You have unsaved changes</Text>
          <View style={styles.bannerActions}>
            {onDiscard && (
              <TouchableOpacity
                testID="discard-changes-btn"
                style={styles.discardBtn}
                onPress={onDiscard}
                accessibilityRole="button"
                accessibilityLabel="Discard changes"
              >
                <Text style={styles.discardText}>Discard</Text>
              </TouchableOpacity>
            )}
            {onSave && (
              <TouchableOpacity
                testID="save-changes-btn"
                style={styles.saveBtn}
                onPress={onSave}
                accessibilityRole="button"
                accessibilityLabel="Save changes"
              >
                <Text style={styles.saveText}>Save Changes</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>
      )}

      <View style={styles.body}>{children}</View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    padding: 16,
    marginVertical: 8,
  },
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  title: {
    fontSize: 17,
    fontWeight: "700",
    color: "#1C1C1E",
  },
  stateSaving: {
    fontSize: 12,
    color: "#8E8E93",
    fontWeight: "500",
  },
  stateSaved: {
    fontSize: 12,
    color: "#34C759",
    fontWeight: "600",
  },
  unsavedBanner: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "#FFF8E6",
    borderWidth: 1,
    borderColor: "#FFE082",
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
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
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: "#C7C7CC",
  },
  discardText: {
    fontSize: 11,
    fontWeight: "600",
    color: "#636366",
  },
  saveBtn: {
    backgroundColor: "#1C1C1E",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 4,
  },
  saveText: {
    color: "#FFFFFF",
    fontSize: 11,
    fontWeight: "600",
  },
  body: {
    paddingTop: 4,
  },
});
