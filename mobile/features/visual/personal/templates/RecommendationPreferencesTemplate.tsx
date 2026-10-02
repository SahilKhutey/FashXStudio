import React from "react";
import { View, StyleSheet, ScrollView } from "react-native";
import { RecommendationPreferencesTemplateSpecContract, RecommendationPreferencesContract } from "../types";
import { RecommendationPreferences } from "../components/RecommendationPreferences";

interface RecommendationPreferencesTemplateProps {
  data: RecommendationPreferencesTemplateSpecContract;
  onUpdateSettings: (newSettings: Partial<RecommendationPreferencesContract>) => void;
  onResetPersonalization?: () => void;
  testID?: string;
}

export const RecommendationPreferencesTemplate: React.FC<RecommendationPreferencesTemplateProps> = ({
  data,
  onUpdateSettings,
  onResetPersonalization,
  testID = "recommendation-preferences-pr09",
}) => {
  return (
    <ScrollView testID={testID} style={styles.container}>
      <RecommendationPreferences
        settings={data.settings}
        transparencyExplanation={data.transparency_explanation}
        onUpdateSettings={onUpdateSettings}
        onResetPersonalization={onResetPersonalization}
      />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F2F2F7",
    padding: 16,
  },
});
