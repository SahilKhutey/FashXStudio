import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { RecommendationPreferencesContract } from "../types";
import { PreferenceSwitch } from "./PreferenceSwitch";

interface RecommendationPreferencesProps {
  settings: RecommendationPreferencesContract;
  transparencyExplanation: string;
  onUpdateSettings: (newSettings: Partial<RecommendationPreferencesContract>) => void;
  onResetPersonalization?: () => void;
  testID?: string;
}

export const RecommendationPreferences: React.FC<RecommendationPreferencesProps> = ({
  settings,
  transparencyExplanation,
  onUpdateSettings,
  onResetPersonalization,
  testID = "recommendation-preferences",
}) => {
  return (
    <View testID={testID} style={styles.container}>
      <Text style={styles.header}>RECOMMENDATION TUNING</Text>

      <PreferenceSwitch
        testID="pref-personalized-rec"
        label="Personalized Recommendations"
        description="Deliver algorithmic curation tailored to your profile and wardrobe choices."
        value={settings.personalized_recommendations}
        onValueChange={(val) => onUpdateSettings({ personalized_recommendations: val })}
      />

      <PreferenceSwitch
        testID="pref-style-pref"
        label="Use Style Preferences"
        description="Filter and score products using your selected aesthetic categories and silhouettes."
        value={settings.use_style_preferences}
        onValueChange={(val) => onUpdateSettings({ use_style_preferences: val })}
      />

      <PreferenceSwitch
        testID="pref-regional-ctx"
        label="Use Regional Context"
        description="Incorporate local climate and regional trend momentum from your selected discovery city."
        value={settings.use_regional_context}
        onValueChange={(val) => onUpdateSettings({ use_regional_context: val })}
      />

      <View style={styles.transparencyBox} testID="rec-transparency-box">
        <Text style={styles.transparencyTitle}>RECOMMENDATION TRANSPARENCY</Text>
        <Text style={styles.transparencyBody}>{transparencyExplanation}</Text>
      </View>

      {onResetPersonalization && (
        <View style={styles.resetContainer}>
          <Text style={styles.resetNotice}>
            Resetting personalization clears all inferred browsing activity and resets algorithmic weights.
          </Text>
          <TouchableOpacity
            testID="reset-personalization-button"
            style={styles.resetButton}
            onPress={onResetPersonalization}
            accessibilityRole="button"
            accessibilityLabel="Reset personalization"
          >
            <Text style={styles.resetButtonText}>Reset Personalization Signals</Text>
          </TouchableOpacity>
        </View>
      )}
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
  transparencyBox: {
    marginTop: 16,
    padding: 12,
    backgroundColor: "#F2F2F7",
    borderRadius: 6,
  },
  transparencyTitle: {
    fontSize: 10,
    fontWeight: "700",
    color: "#5856D6",
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  transparencyBody: {
    fontSize: 12,
    color: "#3A3A3C",
    lineHeight: 16,
  },
  resetContainer: {
    marginTop: 20,
    paddingTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderColor: "#E5E5EA",
  },
  resetNotice: {
    fontSize: 11,
    color: "#8E8E93",
    marginBottom: 10,
  },
  resetButton: {
    backgroundColor: "#FFF0F0",
    borderWidth: 1,
    borderColor: "#FFD6D6",
    paddingVertical: 10,
    borderRadius: 6,
    alignItems: "center",
  },
  resetButtonText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#D70015",
  },
});
