import React from "react";
import { View, StyleSheet } from "react-native";
import { PersonalDashboardTemplateSpecContract } from "../types";
import { PersonalDashboard } from "../components/PersonalDashboard";

interface PersonalDashboardTemplateProps {
  data: PersonalDashboardTemplateSpecContract;
  onNavigate?: (screen: string, params?: Record<string, any>) => void;
  onRetryModule?: (moduleKey: string) => void;
  testID?: string;
}

export const PersonalDashboardTemplate: React.FC<PersonalDashboardTemplateProps> = ({
  data,
  onNavigate,
  onRetryModule,
  testID = "personal-dashboard-pr02",
}) => {
  return (
    <View testID={testID} style={styles.container}>
      <PersonalDashboard
        dashboard={data}
        onNavigate={onNavigate}
        onRetryModule={onRetryModule}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});
