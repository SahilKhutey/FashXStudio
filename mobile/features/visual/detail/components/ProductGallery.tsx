import React, { useState } from "react";
import {
  View,
  Text,
  Image,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Modal,
  Dimensions,
} from "react-native";
import { ProductGalleryContract } from "../types";

interface ProductGalleryProps {
  gallery: ProductGalleryContract;
  testID?: string;
}

const { width } = Dimensions.get("window");

export const ProductGallery: React.FC<ProductGalleryProps> = ({
  gallery,
  testID = "product-gallery",
}) => {
  const items = gallery.items || [];
  const [selectedIndex, setSelectedIndex] = useState(gallery.active_index || 0);
  const [isZoomOpen, setIsZoomOpen] = useState(false);

  if (items.length === 0) {
    return (
      <View testID={testID} style={styles.emptyContainer}>
        <Text style={styles.emptyText}>No product media available</Text>
      </View>
    );
  }

  const currentMedia = items[selectedIndex] || items[0];

  return (
    <View testID={testID} style={styles.container}>
      {/* Primary Image View with Tap to Zoom */}
      <TouchableOpacity
        testID={`${testID}-primary-touchable`}
        activeOpacity={0.9}
        onPress={() => gallery.zoom_enabled !== false && setIsZoomOpen(true)}
        style={styles.primaryImageWrapper}
        accessibilityRole="imagebutton"
        accessibilityLabel={`${currentMedia.alt_text || "Product image"}, tap to zoom`}
      >
        <Image
          source={{ uri: currentMedia.uri }}
          style={styles.primaryImage}
          resizeMode="cover"
        />
        {gallery.zoom_enabled !== false && (
          <View style={styles.zoomBadge}>
            <Text style={styles.zoomText}>🔍 Zoom</Text>
          </View>
        )}
      </TouchableOpacity>

      {/* Thumbnail Bar */}
      {items.length > 1 && (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.thumbnailRail}
          style={styles.thumbnailScrollView}
        >
          {items.map((item, idx) => {
            const isSelected = idx === selectedIndex;
            return (
              <TouchableOpacity
                key={item.id || `thumb-${idx}`}
                testID={`${testID}-thumb-${idx}`}
                onPress={() => setSelectedIndex(idx)}
                style={[
                  styles.thumbnailWrapper,
                  isSelected && styles.thumbnailSelected,
                ]}
                accessibilityRole="button"
                accessibilityLabel={`View image ${idx + 1} of ${items.length}`}
              >
                <Image
                  source={{ uri: item.uri }}
                  style={styles.thumbnailImage}
                  resizeMode="cover"
                />
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      )}

      {/* Fullscreen Zoom Modal (Section 9.8) */}
      <Modal
        visible={isZoomOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setIsZoomOpen(false)}
      >
        <View style={styles.modalBackdrop}>
          <TouchableOpacity
            testID={`${testID}-zoom-close`}
            onPress={() => setIsZoomOpen(false)}
            style={styles.closeButton}
            accessibilityRole="button"
            accessibilityLabel="Close image zoom"
          >
            <Text style={styles.closeButtonText}>✕ Close</Text>
          </TouchableOpacity>
          <Image
            source={{ uri: currentMedia.uri }}
            style={styles.zoomImage}
            resizeMode="contain"
          />
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: "100%",
    backgroundColor: "#ffffff",
  },
  emptyContainer: {
    height: 320,
    backgroundColor: "#f5f5f5",
    justifyContent: "center",
    alignItems: "center",
  },
  emptyText: {
    color: "#888888",
    fontSize: 14,
  },
  primaryImageWrapper: {
    width: "100%",
    aspectRatio: 3 / 4,
    backgroundColor: "#f7f7f7",
    position: "relative",
  },
  primaryImage: {
    width: "100%",
    height: "100%",
  },
  zoomBadge: {
    position: "absolute",
    bottom: 12,
    right: 12,
    backgroundColor: "rgba(0,0,0,0.65)",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  zoomText: {
    color: "#ffffff",
    fontSize: 12,
    fontWeight: "500",
  },
  thumbnailScrollView: {
    marginTop: 12,
  },
  thumbnailRail: {
    paddingHorizontal: 16,
    gap: 8,
  },
  thumbnailWrapper: {
    width: 60,
    height: 80,
    borderRadius: 4,
    borderWidth: 1.5,
    borderColor: "transparent",
    overflow: "hidden",
  },
  thumbnailSelected: {
    borderColor: "#111111",
  },
  thumbnailImage: {
    width: "100%",
    height: "100%",
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: "#000000",
    justifyContent: "center",
    alignItems: "center",
  },
  closeButton: {
    position: "absolute",
    top: 48,
    right: 20,
    zIndex: 10,
    backgroundColor: "rgba(255,255,255,0.2)",
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
  },
  closeButtonText: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "600",
  },
  zoomImage: {
    width: width,
    height: width * (4 / 3),
  },
});
