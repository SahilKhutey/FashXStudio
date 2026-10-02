import React from "react";
import { View, Text, StyleSheet, ScrollView } from "react-native";
import { StateTemplateSpecContract } from "../types";
import { RegionBreadcrumb } from "../components/RegionBreadcrumb";
import { RegionCard } from "../components/RegionCard";
import { RegionalTrendCard } from "../components/RegionalTrendCard";

interface StateViewTemplateProps {
  data: StateTemplateSpecContract;
  onSelectCrumb?: (crumbId: string) => void;
  onPressCity?: (cityId: string) => void;
  onPressTrend?: (trendId: string) => void;
  testID?: string;
}

export const StateViewTemplate: React.FC<StateViewTemplateProps> = ({
  data,
  onSelectCrumb,
  onPressCity,
  onPressTrend,
  testID = "state-view-screen",
}) => {
  const { state_region, country_region, breadcrumbs, cities, regional_trends } = data;

  return (
    <ScrollView
      testID={testID}
      style={styles.container}
      showsVerticalScrollIndicator={false}
      contentContainerStyle={styles.content}
    >
      <RegionBreadcrumb breadcrumbs={breadcrumbs} onSelectCrumb={onSelectCrumb} />

      <View style={styles.header}>
        <Text style={styles.stateTag}>
          {state_region.state_code ? `${state_region.state_code} • ` : ""}
          {country_region.name.toUpperCase()}
        </Text>
        <Text style={styles.title}>{state_region.name}</Text>
        {state_region.description && (
          <Text style={styles.description}>{state_region.description}</Text>
        )}
      </View>

      {/* Cities in State */}
      {cities.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>CITIES & FASHION CENTERS ({cities.length})</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.rail}>
            {cities.map((city) => (
              <RegionCard
                key={city.id}
                region={city}
                compact
                onPressRegion={onPressCity}
              />
            ))}
          </ScrollView>
        </View>
      )}

      {/* Regional Trends */}
      {regional_trends.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>STATE TEXTILE & STYLE TRENDS</Text>
          {regional_trends.map((tr) => (
            <RegionalTrendCard
              key={tr.id}
              trend={tr}
              onPressTrend={onPressTrend}
            />
          ))}
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  content: {
    paddingBottom: 40,
  },
  header: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#eeeeee",
  },
  stateTag: {
    fontSize: 11,
    fontWeight: "800",
    color: "#6b7280",
    letterSpacing: 1,
  },
  title: {
    fontSize: 24,
    fontWeight: "800",
    color: "#111111",
    marginTop: 2,
  },
  description: {
    fontSize: 13,
    color: "#4b5563",
    marginTop: 4,
    lineHeight: 18,
  },
  section: {
    marginTop: 20,
    paddingHorizontal: 16,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: "800",
    color: "#6b7280",
    letterSpacing: 1,
    marginBottom: 12,
  },
  rail: {
    gap: 12,
  },
});
