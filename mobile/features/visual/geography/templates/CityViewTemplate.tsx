import React from "react";
import { View, Text, StyleSheet, ScrollView } from "react-native";
import { CityTemplateSpecContract } from "../types";
import { RegionBreadcrumb } from "../components/RegionBreadcrumb";
import { RegionalTrendCard } from "../components/RegionalTrendCard";
import { RegionCard } from "../components/RegionCard";

interface CityViewTemplateProps {
  data: CityTemplateSpecContract;
  onSelectCrumb?: (crumbId: string) => void;
  onPressTrend?: (trendId: string) => void;
  onPressRelatedCity?: (cityId: string) => void;
  testID?: string;
}

export const CityViewTemplate: React.FC<CityViewTemplateProps> = ({
  data,
  onSelectCrumb,
  onPressTrend,
  onPressRelatedCity,
  testID = "city-view-screen",
}) => {
  const { city, breadcrumbs, fashion_trends, related_cities } = data;

  return (
    <ScrollView
      testID={testID}
      style={styles.container}
      showsVerticalScrollIndicator={false}
      contentContainerStyle={styles.content}
    >
      <RegionBreadcrumb breadcrumbs={breadcrumbs} onSelectCrumb={onSelectCrumb} />

      <View style={styles.header}>
        <Text style={styles.cityTag}>URBAN FASHION CAPITAL</Text>
        <Text style={styles.title}>{city.name}</Text>
        {city.description && (
          <Text style={styles.description}>{city.description}</Text>
        )}
      </View>

      {/* Urban Trends */}
      {fashion_trends.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>LOCAL STREET MOVEMENTS</Text>
          {fashion_trends.map((tr) => (
            <RegionalTrendCard
              key={tr.id}
              trend={tr}
              onPressTrend={onPressTrend}
            />
          ))}
        </View>
      )}

      {/* Related Cities */}
      {related_cities.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>SIMILAR FASHION CITIES</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.rail}>
            {related_cities.map((rel) => (
              <RegionCard
                key={rel.id}
                region={rel}
                compact
                onPressRegion={onPressRelatedCity}
              />
            ))}
          </ScrollView>
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
  cityTag: {
    fontSize: 10,
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
