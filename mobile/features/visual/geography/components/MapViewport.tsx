import React, { useState } from "react";
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from "react-native";
import { GeographyLayerType, MapViewModelContract } from "../types";

interface MapViewportProps {
  mapView: MapViewModelContract;
  onSelectMarker?: (regionId: string) => void;
  onToggleLayer?: (layer: GeographyLayerType) => void;
  onZoomIn?: () => void;
  onZoomOut?: () => void;
  onResetView?: () => void;
  onSwitchToListMode?: () => void;
  testID?: string;
}

export const MapViewport: React.FC<MapViewportProps> = ({
  mapView,
  onSelectMarker,
  onToggleLayer,
  onZoomIn,
  onZoomOut,
  onResetView,
  onSwitchToListMode,
  testID = "fashion-map-viewport",
}) => {
  const [activeLayers, setActiveLayers] = useState<GeographyLayerType[]>(mapView.active_layers);

  const toggleLayer = (layer: GeographyLayerType) => {
    const updated = activeLayers.includes(layer)
      ? activeLayers.filter((l) => l !== layer)
      : [...activeLayers, layer];
    setActiveLayers(updated);
    onToggleLayer?.(layer);
  };

  const allLayers: GeographyLayerType[] = ["regions", "trends", "collections", "products"];

  return (
    <View testID={testID} style={styles.container}>
      {/* Map Surface Simulator */}
      <View style={styles.mapCanvas}>
        {/* Geographic Grid Pattern Representation */}
        <View style={styles.gridOverlay}>
          <Text style={styles.coordinateLabel}>
            Lat: {mapView.viewport.center_latitude.toFixed(2)}° • Lon:{" "}
            {mapView.viewport.center_longitude.toFixed(2)}° • Zoom:{" "}
            {mapView.viewport.zoom_level}x
          </Text>
        </View>

        {/* Render Markers */}
        <View style={styles.markersContainer}>
          {mapView.markers.map((marker) => {
            const isSelected = marker.region_id === mapView.selected_region_id;
            return (
              <TouchableOpacity
                key={marker.id}
                testID={`map-marker-${marker.region_id}`}
                activeOpacity={0.8}
                onPress={() => onSelectMarker?.(marker.region_id)}
                style={[
                  styles.markerPin,
                  isSelected && styles.selectedMarkerPin,
                  marker.category === "trend" && styles.trendMarkerPin,
                ]}
                accessibilityRole="button"
                accessibilityLabel={`Map marker: ${marker.title}, contains ${marker.item_count} fashion items`}
              >
                <Text
                  style={[
                    styles.markerText,
                    isSelected && styles.selectedMarkerText,
                  ]}
                  numberOfLines={1}
                >
                  📍 {marker.title}
                </Text>
              </TouchableOpacity>
            );
          })}

          {/* Render Clusters */}
          {mapView.clusters.map((cluster) => (
            <View
              key={cluster.cluster_id}
              testID={`map-cluster-${cluster.cluster_id}`}
              style={styles.clusterBadge}
              accessibilityLabel={`Cluster containing ${cluster.count} regions`}
            >
              <Text style={styles.clusterCount}>+{cluster.count}</Text>
            </View>
          ))}
        </View>

        {/* Map Control Buttons: Zoom & Reset */}
        <View style={styles.controlsRow}>
          <TouchableOpacity
            testID="map-zoom-in-btn"
            style={styles.controlBtn}
            onPress={onZoomIn}
            accessibilityLabel="Zoom In"
          >
            <Text style={styles.controlBtnText}>＋</Text>
          </TouchableOpacity>
          <TouchableOpacity
            testID="map-zoom-out-btn"
            style={styles.controlBtn}
            onPress={onZoomOut}
            accessibilityLabel="Zoom Out"
          >
            <Text style={styles.controlBtnText}>−</Text>
          </TouchableOpacity>
          <TouchableOpacity
            testID="map-reset-btn"
            style={styles.controlBtn}
            onPress={onResetView}
            accessibilityLabel="Reset View"
          >
            <Text style={styles.controlBtnText}>⟲</Text>
          </TouchableOpacity>
        </View>

        {/* Accessibility List Switcher Trigger */}
        {onSwitchToListMode && (
          <TouchableOpacity
            testID="switch-to-list-mode-btn"
            style={styles.listModeBtn}
            onPress={onSwitchToListMode}
            accessibilityRole="button"
            accessibilityLabel="Switch to accessible list view"
          >
            <Text style={styles.listModeBtnText}>📋 List View</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Layer Controls Bar */}
      <View style={styles.layersBar}>
        <Text style={styles.layersTitle}>LAYERS:</Text>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.layersScroll}
        >
          {allLayers.map((layer) => {
            const isEnabled = activeLayers.includes(layer);
            return (
              <TouchableOpacity
                key={layer}
                testID={`layer-toggle-${layer}`}
                onPress={() => toggleLayer(layer)}
                style={[styles.layerChip, isEnabled && styles.activeLayerChip]}
                accessibilityRole="checkbox"
                accessibilityState={{ checked: isEnabled }}
              >
                <Text
                  style={[
                    styles.layerChipText,
                    isEnabled && styles.activeLayerChipText,
                  ]}
                >
                  {isEnabled ? "☑" : "☐"} {layer.toUpperCase()}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#ffffff",
    overflow: "hidden",
  },
  mapCanvas: {
    height: 320,
    backgroundColor: "#e8eff5",
    position: "relative",
    justifyContent: "space-between",
    padding: 12,
  },
  gridOverlay: {
    backgroundColor: "rgba(255, 255, 255, 0.75)",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    alignSelf: "flex-start",
  },
  coordinateLabel: {
    fontSize: 10,
    color: "#6b7280",
    fontWeight: "600",
  },
  markersContainer: {
    flex: 1,
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 16,
  },
  markerPin: {
    backgroundColor: "#ffffff",
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#d1d5db",
    shadowColor: "#000",
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  selectedMarkerPin: {
    backgroundColor: "#111111",
    borderColor: "#111111",
  },
  trendMarkerPin: {
    borderColor: "#f59e0b",
  },
  markerText: {
    fontSize: 11,
    fontWeight: "700",
    color: "#111111",
  },
  selectedMarkerText: {
    color: "#ffffff",
  },
  clusterBadge: {
    backgroundColor: "#2563eb",
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 2,
    borderColor: "#ffffff",
  },
  clusterCount: {
    color: "#ffffff",
    fontSize: 11,
    fontWeight: "800",
  },
  controlsRow: {
    position: "absolute",
    right: 12,
    bottom: 12,
    gap: 6,
  },
  controlBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: "#ffffff",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#e5e7eb",
    shadowColor: "#000",
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  controlBtnText: {
    fontSize: 16,
    fontWeight: "700",
    color: "#111111",
  },
  listModeBtn: {
    position: "absolute",
    left: 12,
    bottom: 12,
    backgroundColor: "#ffffff",
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#e5e7eb",
  },
  listModeBtnText: {
    fontSize: 11,
    fontWeight: "700",
    color: "#111111",
  },
  layersBar: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: "#ffffff",
    borderTopWidth: 1,
    borderTopColor: "#f3f4f6",
  },
  layersTitle: {
    fontSize: 10,
    fontWeight: "800",
    color: "#9ca3af",
    marginRight: 8,
  },
  layersScroll: {
    gap: 8,
  },
  layerChip: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 14,
    backgroundColor: "#f9fafb",
    borderWidth: 1,
    borderColor: "#e5e7eb",
  },
  activeLayerChip: {
    backgroundColor: "#111111",
    borderColor: "#111111",
  },
  layerChipText: {
    fontSize: 11,
    fontWeight: "600",
    color: "#4b5563",
  },
  activeLayerChipText: {
    color: "#ffffff",
  },
});
