import React, { useState } from "react";
import { View, Text, StyleSheet, TextInput, ScrollView, TouchableOpacity } from "react-native";
import { RegionalExplorerTemplateSpecContract } from "../types";
import { RegionBreadcrumb } from "../components/RegionBreadcrumb";

interface RegionalExplorerTemplateProps {
  data: RegionalExplorerTemplateSpecContract;
  onSelectRegion?: (regionId: string) => void;
  onSelectCrumb?: (crumbId: string) => void;
  onSearchChange?: (query: string) => void;
  testID?: string;
}

export const RegionalExplorerTemplate: React.FC<RegionalExplorerTemplateProps> = ({
  data,
  onSelectRegion,
  onSelectCrumb,
  onSearchChange,
  testID = "regional-explorer-screen",
}) => {
  const [query, setQuery] = useState(data.active_search_query);

  const handleQueryChange = (text: string) => {
    setQuery(text);
    onSearchChange?.(text);
  };

  return (
    <View testID={testID} style={styles.container}>
      {/* Search Bar */}
      <View style={styles.searchHeader}>
        <View style={styles.searchBox}>
          <Text style={styles.searchIcon}>🔍</Text>
          <TextInput
            testID="explorer-search-input"
            style={styles.searchInput}
            placeholder="Search continents, countries, cities..."
            value={query}
            onChangeText={handleQueryChange}
            placeholderTextColor="#9ca3af"
          />
          {query.length > 0 && (
            <TouchableOpacity onPress={() => handleQueryChange("")}>
              <Text style={styles.clearBtn}>✕</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Breadcrumbs Trail */}
      <RegionBreadcrumb
        breadcrumbs={data.breadcrumbs}
        onSelectCrumb={onSelectCrumb}
      />

      {/* Parent Header if Drilled Down */}
      {data.parent_region && (
        <View style={styles.parentBanner}>
          <Text style={styles.parentType}>
            {data.parent_region.type.toUpperCase()}
          </Text>
          <Text style={styles.parentTitle}>{data.parent_region.name}</Text>
          {data.parent_region.description && (
            <Text style={styles.parentDesc}>{data.parent_region.description}</Text>
          )}
        </View>
      )}

      {/* Regions Hierarchy List */}
      <ScrollView
        style={styles.list}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.subheading}>
          {data.parent_region
            ? `SUB-REGIONS & CITIES (${data.regions.length})`
            : `SUPPORTED COUNTRIES (${data.regions.length})`}
        </Text>

        {data.regions.length === 0 ? (
          <View style={styles.emptyView}>
            <Text style={styles.emptyTitle}>No Regions Found</Text>
            <Text style={styles.emptySubtitle}>
              Try searching for a different fashion capital, country, or state.
            </Text>
          </View>
        ) : (
          data.regions.map((reg) => (
            <TouchableOpacity
              key={reg.id}
              testID={`explorer-item-${reg.id}`}
              style={styles.regionRow}
              onPress={() => onSelectRegion?.(reg.id)}
              accessibilityRole="button"
              accessibilityLabel={`View ${reg.name}, ${reg.type}`}
            >
              <View style={styles.rowDetails}>
                <Text style={styles.regionName}>{reg.name}</Text>
                <Text style={styles.regionMeta}>
                  {reg.type.toUpperCase()} • {reg.products_count} Products •{" "}
                  {reg.trends_count} Trends
                </Text>
              </View>
              <Text style={styles.chevron}>→</Text>
            </TouchableOpacity>
          ))
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  searchHeader: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#eeeeee",
  },
  searchBox: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#f3f4f6",
    borderRadius: 8,
    paddingHorizontal: 10,
    height: 42,
  },
  searchIcon: {
    fontSize: 14,
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 14,
    color: "#111111",
    paddingVertical: 0,
  },
  clearBtn: {
    fontSize: 14,
    color: "#9ca3af",
    padding: 4,
  },
  parentBanner: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    backgroundColor: "#f9fafb",
    borderBottomWidth: 1,
    borderBottomColor: "#f3f4f6",
  },
  parentType: {
    fontSize: 10,
    fontWeight: "700",
    color: "#6b7280",
    letterSpacing: 0.8,
  },
  parentTitle: {
    fontSize: 20,
    fontWeight: "800",
    color: "#111111",
    marginTop: 2,
  },
  parentDesc: {
    fontSize: 12,
    color: "#4b5563",
    marginTop: 4,
    lineHeight: 16,
  },
  list: {
    flex: 1,
  },
  listContent: {
    padding: 16,
    paddingBottom: 40,
  },
  subheading: {
    fontSize: 11,
    fontWeight: "800",
    color: "#6b7280",
    letterSpacing: 1,
    marginBottom: 10,
  },
  regionRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: "#f3f4f6",
  },
  rowDetails: {
    flex: 1,
  },
  regionName: {
    fontSize: 16,
    fontWeight: "700",
    color: "#111111",
  },
  regionMeta: {
    fontSize: 12,
    color: "#6b7280",
    marginTop: 2,
  },
  chevron: {
    fontSize: 18,
    color: "#9ca3af",
    marginLeft: 8,
  },
  emptyView: {
    paddingVertical: 48,
    alignItems: "center",
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#111111",
  },
  emptySubtitle: {
    fontSize: 13,
    color: "#6b7280",
    marginTop: 4,
    textAlign: "center",
    maxWidth: 240,
  },
});
