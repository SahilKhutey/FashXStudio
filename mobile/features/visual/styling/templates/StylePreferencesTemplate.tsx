import React, { useState } from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { StylePreferenceContract, StylePreferencesTemplateSpecContract } from "../types";
import { StylePreferenceSelector } from "../components/StylePreferenceSelector";

interface StylePreferencesTemplateProps {
  data: StylePreferencesTemplateSpecContract;
  onSavePreferences?: (updated: StylePreferenceContract) => void;
  testID?: string;
}

export const StylePreferencesTemplate: React.FC<StylePreferencesTemplateProps> = ({
  data,
  onSavePreferences,
  testID = "style-preferences-screen",
}) => {
  const [preferences, setPreferences] = useState<StylePreferenceContract>(data.preferences);

  const toggleItem = (list: string[], item: string) => {
    return list.includes(item) ? list.filter((i) => i !== item) : [...list, item];
  };

  const handleToggleStyle = (style: string) => {
    setPreferences((prev) => ({
      ...prev,
      preferred_styles: toggleItem(prev.preferred_styles, style),
    }));
  };

  const handleToggleFit = (fit: string) => {
    setPreferences((prev) => ({
      ...prev,
      preferred_fits: toggleItem(prev.preferred_fits, fit),
    }));
  };

  const handleToggleColor = (color: string) => {
    setPreferences((prev) => ({
      ...prev,
      preferred_colors: toggleItem(prev.preferred_colors, color),
    }));
  };

  const handleToggleMaterial = (mat: string) => {
    setPreferences((prev) => ({
      ...prev,
      preferred_materials: toggleItem(prev.preferred_materials, mat),
    }));
  };

  const handleChangeBudget = (tier: string) => {
    setPreferences((prev) => ({
      ...prev,
      budget_tier: tier,
    }));
  };

  return (
    <View testID={testID} style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Style Profile</Text>
        <Text style={styles.subtitle}>
          Personalize recommendations, fit parameters, and outfit suggestions
        </Text>
      </View>

      <StylePreferenceSelector
        preferences={preferences}
        availableStyles={data.available_styles}
        availableFits={data.available_fits}
        availableColors={data.available_colors}
        availableMaterials={data.available_materials}
        onToggleStyle={handleToggleStyle}
        onToggleFit={handleToggleFit}
        onToggleColor={handleToggleColor}
        onToggleMaterial={handleToggleMaterial}
        onChangeBudget={handleChangeBudget}
      />

      <View style={styles.footer}>
        <TouchableOpacity
          testID="save-preferences-btn"
          style={styles.saveBtn}
          onPress={() => onSavePreferences?.(preferences)}
        >
          <Text style={styles.saveBtnText}>Save Preferences</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#eeeeee",
  },
  title: {
    fontSize: 20,
    fontWeight: "800",
    color: "#111111",
  },
  subtitle: {
    fontSize: 12,
    color: "#6b7280",
    marginTop: 2,
  },
  footer: {
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: "#e5e7eb",
    backgroundColor: "#ffffff",
  },
  saveBtn: {
    backgroundColor: "#111111",
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: "center",
  },
  saveBtnText: {
    color: "#ffffff",
    fontSize: 13,
    fontWeight: "700",
  },
});
