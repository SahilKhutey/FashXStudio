import React from "react";
import { View, StyleSheet, ScrollView } from "react-native";
import { RegionalPreferencesTemplateSpecContract, RegionalPreferencesContract } from "../types";
import { RegionalPreferences } from "../components/RegionalPreferences";

interface RegionalPreferencesTemplateProps {
  data: RegionalPreferencesTemplateSpecContract;
  onUpdateSettings: (newSettings: Partial<RegionalPreferencesContract>) => void;
  testID?: string;
}

export const RegionalPreferencesTemplate: React.FC<RegionalPreferencesTemplateProps> = ({
  data,
  onUpdateSettings,
  testID = "regional-preferences-pr10",
}) => {
  return (
    <ScrollView testID={testID} style={styles.container}>
      <RegionalPreferences
        settings={data.settings}
        availableCountries={data.available_countries}
        availableRegions={data.available_regions}
        onUpdateSettings={onUpdateSettings}
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
