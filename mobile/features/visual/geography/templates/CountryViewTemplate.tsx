import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Image } from "react-native";
import { CountryTemplateSpecContract } from "../types";
import { RegionBreadcrumb } from "../components/RegionBreadcrumb";
import { RegionCard } from "../components/RegionCard";
import { RegionalTrendCard } from "../components/RegionalTrendCard";

interface CountryViewTemplateProps {
  data: CountryTemplateSpecContract;
  onSelectCrumb?: (crumbId: string) => void;
  onPressState?: (stateId: string) => void;
  onPressTrend?: (trendId: string) => void;
  onPressProduct?: (productId: string) => void;
  onPressLook?: (lookId: string) => void;
  testID?: string;
}

export const CountryViewTemplate: React.FC<CountryViewTemplateProps> = ({
  data,
  onSelectCrumb,
  onPressState,
  onPressTrend,
  onPressProduct,
  onPressLook,
  testID = "country-view-screen",
}) => {
  const { country, breadcrumbs, states_or_provinces, regional_trends } = data;

  return (
    <ScrollView
      testID={testID}
      style={styles.container}
      showsVerticalScrollIndicator={false}
      contentContainerStyle={styles.content}
    >
      <RegionBreadcrumb breadcrumbs={breadcrumbs} onSelectCrumb={onSelectCrumb} />

      {/* Country Hero Header */}
      {country.hero_image_uri && (
        <Image
          source={{ uri: country.hero_image_uri }}
          style={styles.heroImage}
          resizeMode="cover"
        />
      )}

      <View style={styles.header}>
        <Text style={styles.countryCode}>{country.country_code || "REGION"}</Text>
        <Text style={styles.title}>{country.name}</Text>
        {country.description && (
          <Text style={styles.description}>{country.description}</Text>
        )}
      </View>

      {/* States / Provinces Rail */}
      {states_or_provinces.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            STATES & PROVINCES ({states_or_provinces.length})
          </Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.rail}>
            {states_or_provinces.map((st) => (
              <RegionCard
                key={st.id}
                region={st}
                compact
                onPressRegion={onPressState}
              />
            ))}
          </ScrollView>
        </View>
      )}

      {/* Regional Trends */}
      {regional_trends.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>FASHION MOVEMENTS & TRENDS</Text>
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
  heroImage: {
    width: "100%",
    height: 180,
    backgroundColor: "#f3f4f6",
  },
  header: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#eeeeee",
  },
  countryCode: {
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
    marginTop: 6,
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
