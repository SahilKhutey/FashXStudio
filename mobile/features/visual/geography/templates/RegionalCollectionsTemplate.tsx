import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from "react-native";
import { RegionalCollectionsTemplateSpecContract } from "../types";

interface RegionalCollectionsTemplateProps {
  data: RegionalCollectionsTemplateSpecContract;
  onPressCollection?: (collectionId: string) => void;
  testID?: string;
}

export const RegionalCollectionsTemplate: React.FC<RegionalCollectionsTemplateProps> = ({
  data,
  onPressCollection,
  testID = "regional-collections-screen",
}) => {
  const { region, featured_collection, collections } = data;

  return (
    <ScrollView
      testID={testID}
      style={styles.container}
      showsVerticalScrollIndicator={false}
      contentContainerStyle={styles.content}
    >
      <View style={styles.header}>
        <Text style={styles.regionTag}>{region.name.toUpperCase()} CAPSULES</Text>
        <Text style={styles.title}>Regional Collections</Text>
        <Text style={styles.subtitle}>
          Curated fashion narratives and capsules from {region.name}
        </Text>
      </View>

      {/* Featured Capsule Banner */}
      {featured_collection && (
        <TouchableOpacity
          testID={`featured-collection-${featured_collection.id}`}
          style={styles.heroBanner}
          onPress={() => onPressCollection?.(featured_collection.id)}
          activeOpacity={0.9}
        >
          <View style={styles.heroImagePlaceholder}>
            <Text style={styles.heroBadge}>FEATURED CAPSULE</Text>
          </View>
          <View style={styles.heroBody}>
            <Text style={styles.heroTitle}>{featured_collection.title}</Text>
            {featured_collection.subtitle && (
              <Text style={styles.heroSubtitle}>{featured_collection.subtitle}</Text>
            )}
          </View>
        </TouchableOpacity>
      )}

      {/* Collections Grid / List */}
      {collections.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>ALL REGIONAL CAPSULES</Text>
          {collections.map((col) => (
            <TouchableOpacity
              key={col.id}
              testID={`collection-card-${col.id}`}
              style={styles.collectionCard}
              onPress={() => onPressCollection?.(col.id)}
              activeOpacity={0.85}
            >
              <View style={styles.cardImagePlaceholder}>
                <Text style={styles.cardMediaType}>{col.media_type.toUpperCase()}</Text>
              </View>
              <View style={styles.cardContent}>
                <Text style={styles.cardTitle}>{col.title}</Text>
                {col.subtitle && <Text style={styles.cardSubtitle}>{col.subtitle}</Text>}
                <Text style={styles.exploreLink}>EXPLORE CAPSULE →</Text>
              </View>
            </TouchableOpacity>
          ))}
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
  regionTag: {
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 1.2,
    color: "#8E8E93",
    marginBottom: 4,
  },
  title: {
    fontSize: 24,
    fontWeight: "700",
    color: "#1C1C1E",
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 13,
    color: "#636366",
    marginTop: 4,
  },
  heroBanner: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    overflow: "hidden",
    marginBottom: 24,
    elevation: 2,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 4,
  },
  heroImagePlaceholder: {
    height: 180,
    backgroundColor: "#2C2C2E",
    justifyContent: "flex-end",
    padding: 12,
  },
  heroBadge: {
    alignSelf: "flex-start",
    backgroundColor: "#FF9500",
    color: "#FFFFFF",
    fontSize: 10,
    fontWeight: "700",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    letterSpacing: 0.8,
  },
  heroBody: {
    padding: 16,
  },
  heroTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#1C1C1E",
    marginBottom: 4,
  },
  heroSubtitle: {
    fontSize: 13,
    color: "#636366",
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 1.2,
    marginBottom: 12,
  },
  collectionCard: {
    flexDirection: "row",
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    marginBottom: 12,
    overflow: "hidden",
  },
  cardImagePlaceholder: {
    width: 100,
    height: 100,
    backgroundColor: "#F2F2F7",
    justifyContent: "center",
    alignItems: "center",
  },
  cardMediaType: {
    fontSize: 10,
    fontWeight: "700",
    color: "#AEAEB2",
    letterSpacing: 0.8,
  },
  cardContent: {
    flex: 1,
    padding: 12,
    justifyContent: "center",
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: "600",
    color: "#1C1C1E",
    marginBottom: 4,
  },
  cardSubtitle: {
    fontSize: 12,
    color: "#636366",
    marginBottom: 8,
  },
  exploreLink: {
    fontSize: 11,
    fontWeight: "700",
    color: "#007AFF",
    letterSpacing: 0.5,
  },
});
