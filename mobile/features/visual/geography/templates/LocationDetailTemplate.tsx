import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from "react-native";
import { LocationDetailTemplateSpecContract } from "../types";
import { RegionBreadcrumb } from "../components/RegionBreadcrumb";
import { MapViewport } from "../components/MapViewport";
import { RegionalTrendCard } from "../components/RegionalTrendCard";

interface LocationDetailTemplateProps {
  data: LocationDetailTemplateSpecContract;
  onSelectCrumb?: (crumbId: string) => void;
  onPressMarker?: (markerId: string) => void;
  onPressTrend?: (trendId: string) => void;
  onPressProduct?: (productId: string) => void;
  onPressLook?: (lookId: string) => void;
  testID?: string;
}

export const LocationDetailTemplate: React.FC<LocationDetailTemplateProps> = ({
  data,
  onSelectCrumb,
  onPressMarker,
  onPressTrend,
  onPressProduct,
  onPressLook,
  testID = "location-detail-screen",
}) => {
  const { location, breadcrumbs, map_view, trends, products, looks } = data;

  return (
    <ScrollView
      testID={testID}
      style={styles.container}
      showsVerticalScrollIndicator={false}
      contentContainerStyle={styles.content}
    >
      <RegionBreadcrumb breadcrumbs={breadcrumbs} onSelectCrumb={onSelectCrumb} />

      <View style={styles.header}>
        <View style={styles.typeBadge}>
          <Text style={styles.typeBadgeText}>{location.type.toUpperCase()}</Text>
        </View>
        <Text style={styles.title}>{location.name}</Text>
        {location.description && (
          <Text style={styles.description}>{location.description}</Text>
        )}
      </View>

      {/* Mini Location Map */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>GEOGRAPHIC CONTEXT</Text>
        <MapViewport
          mapView={map_view}
          height={220}
          onSelectMarker={onPressMarker}
        />
      </View>

      {/* Location Fashion Trends */}
      {trends.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>LOCATION TRENDS & CULTURE</Text>
          {trends.map((t) => (
            <RegionalTrendCard
              key={t.id}
              trend={t}
              onPressTrend={onPressTrend}
            />
          ))}
        </View>
      )}

      {/* Origin Products Rail */}
      {products.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>ORIGINATING PIECES ({products.length})</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.rail}>
            {products.map((item) => (
              <TouchableOpacity
                key={item.id}
                testID={`location-product-${item.id}`}
                style={styles.railCard}
                onPress={() => onPressProduct?.(item.id)}
                activeOpacity={0.85}
              >
                <View style={styles.railPlaceholder}>
                  <Text style={styles.railTag}>PROD</Text>
                </View>
                <Text style={styles.railTitle} numberOfLines={1}>{item.title}</Text>
                {item.subtitle && (
                  <Text style={styles.railSubtitle} numberOfLines={1}>{item.subtitle}</Text>
                )}
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}

      {/* Regional Looks Rail */}
      {looks.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>CURATED LOCAL LOOKS ({looks.length})</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.rail}>
            {looks.map((item) => (
              <TouchableOpacity
                key={item.id}
                testID={`location-look-${item.id}`}
                style={styles.railCard}
                onPress={() => onPressLook?.(item.id)}
                activeOpacity={0.85}
              >
                <View style={[styles.railPlaceholder, { backgroundColor: "#E5E5EA" }]}>
                  <Text style={styles.railTag}>LOOK</Text>
                </View>
                <Text style={styles.railTitle} numberOfLines={1}>{item.title}</Text>
                {item.subtitle && (
                  <Text style={styles.railSubtitle} numberOfLines={1}>{item.subtitle}</Text>
                )}
              </TouchableOpacity>
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
    backgroundColor: "#FDFDFD",
  },
  content: {
    padding: 16,
    paddingBottom: 40,
  },
  header: {
    marginBottom: 20,
  },
  typeBadge: {
    alignSelf: "flex-start",
    backgroundColor: "#E5E5EA",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
    marginBottom: 8,
  },
  typeBadgeText: {
    fontSize: 9,
    fontWeight: "700",
    color: "#48484A",
    letterSpacing: 0.8,
  },
  title: {
    fontSize: 26,
    fontWeight: "700",
    color: "#1C1C1E",
    letterSpacing: -0.6,
  },
  description: {
    fontSize: 14,
    color: "#48484A",
    lineHeight: 20,
    marginTop: 6,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 1.2,
    marginBottom: 12,
  },
  rail: {
    paddingVertical: 4,
  },
  railCard: {
    width: 140,
    marginRight: 12,
  },
  railPlaceholder: {
    height: 140,
    backgroundColor: "#F2F2F7",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 6,
  },
  railTag: {
    fontSize: 10,
    fontWeight: "700",
    color: "#8E8E93",
  },
  railTitle: {
    fontSize: 12,
    fontWeight: "600",
    color: "#1C1C1E",
  },
  railSubtitle: {
    fontSize: 10,
    color: "#8E8E93",
    marginTop: 2,
  },
});
