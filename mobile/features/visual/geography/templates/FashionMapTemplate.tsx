import React, { useState } from "react";
import { View, Text, StyleSheet, TextInput, ScrollView, TouchableOpacity } from "react-native";
import { FashionMapTemplateSpecContract, GeographyLayerType, RegionContract } from "../types";
import { MapViewport } from "../components/MapViewport";
import { RegionSummaryPanel } from "../components/RegionSummaryPanel";
import { RegionCard } from "../components/RegionCard";

interface FashionMapTemplateProps {
  data: FashionMapTemplateSpecContract;
  onSelectRegion?: (regionId: string) => void;
  onExploreRegion?: (regionId: string) => void;
  onToggleLayer?: (layer: GeographyLayerType) => void;
  testID?: string;
}

export const FashionMapTemplate: React.FC<FashionMapTemplateProps> = ({
  data,
  onSelectRegion,
  onExploreRegion,
  onToggleLayer,
  testID = "fashion-map-screen",
}) => {
  const [isListView, setIsListView] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRegion, setSelectedRegion] = useState<RegionContract | null>(
    data.selected_region || null
  );

  const filteredRegions = data.supported_regions.filter((r) =>
    r.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSelectRegionId = (regionId: string) => {
    const found = data.supported_regions.find((r) => r.id === regionId);
    if (found) {
      setSelectedRegion(found);
    }
    onSelectRegion?.(regionId);
  };

  return (
    <View testID={testID} style={styles.container}>
      {/* Header with Search and Mode Switch */}
      <View style={styles.header}>
        <View style={styles.searchBox}>
          <Text style={styles.searchIcon}>🔍</Text>
          <TextInput
            testID="map-search-input"
            style={styles.searchInput}
            placeholder="Search country, state, city..."
            value={searchQuery}
            onChangeText={setSearchQuery}
            placeholderTextColor="#9ca3af"
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery("")}>
              <Text style={styles.clearSearch}>✕</Text>
            </TouchableOpacity>
          )}
        </View>

        <TouchableOpacity
          testID="toggle-map-list-mode-btn"
          style={styles.modeToggleBtn}
          onPress={() => setIsListView(!isListView)}
          accessibilityRole="button"
          accessibilityLabel={isListView ? "Switch to Map View" : "Switch to List View"}
        >
          <Text style={styles.modeToggleText}>{isListView ? "🗺️ Map" : "📋 List"}</Text>
        </TouchableOpacity>
      </View>

      {/* Main Content: Map or Accessible List */}
      <View style={styles.mainCanvas}>
        {isListView ? (
          <ScrollView
            testID="accessible-region-list"
            style={styles.listView}
            contentContainerStyle={styles.listContent}
            showsVerticalScrollIndicator={false}
          >
            <Text style={styles.listHeader}>
              SUPPORTED REGIONS ({filteredRegions.length})
            </Text>
            {filteredRegions.map((reg) => (
              <RegionCard
                key={reg.id}
                region={reg}
                onPressRegion={handleSelectRegionId}
              />
            ))}
          </ScrollView>
        ) : (
          <View style={styles.mapArea}>
            <MapViewport
              mapView={data.map_view}
              onSelectMarker={handleSelectRegionId}
              onToggleLayer={onToggleLayer}
              onSwitchToListMode={() => setIsListView(true)}
            />
          </View>
        )}
      </View>

      {/* Selected Region Summary Panel (Fixed Bottom Sheet) */}
      {selectedRegion && (
        <View style={styles.bottomSheetArea}>
          <RegionSummaryPanel
            region={selectedRegion}
            onExploreRegion={onExploreRegion}
            onClose={() => setSelectedRegion(null)}
          />
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#eeeeee",
    gap: 10,
    backgroundColor: "#ffffff",
  },
  searchBox: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#f3f4f6",
    borderRadius: 8,
    paddingHorizontal: 10,
    height: 40,
  },
  searchIcon: {
    fontSize: 14,
    marginRight: 6,
  },
  searchInput: {
    flex: 1,
    fontSize: 13,
    color: "#111111",
    paddingVertical: 0,
  },
  clearSearch: {
    fontSize: 12,
    color: "#9ca3af",
    padding: 4,
  },
  modeToggleBtn: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#e5e7eb",
    backgroundColor: "#ffffff",
  },
  modeToggleText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#111111",
  },
  mainCanvas: {
    flex: 1,
  },
  mapArea: {
    flex: 1,
  },
  listView: {
    flex: 1,
  },
  listContent: {
    padding: 16,
    paddingBottom: 80,
  },
  listHeader: {
    fontSize: 11,
    fontWeight: "800",
    color: "#6b7280",
    letterSpacing: 1,
    marginBottom: 12,
  },
  bottomSheetArea: {
    position: "absolute",
    left: 16,
    right: 16,
    bottom: 16,
  },
});
