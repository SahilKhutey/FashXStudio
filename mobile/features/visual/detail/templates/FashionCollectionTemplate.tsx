import React from "react";
import { View, Text, Image, StyleSheet, ScrollView, SafeAreaView, TouchableOpacity } from "react-native";
import { FashionCollectionDetailTemplateSpecContract } from "../types";

interface FashionCollectionTemplateProps {
  spec: FashionCollectionDetailTemplateSpecContract;
  onSelectLook?: (lookId: string) => void;
  onSelectProduct?: (productId: string) => void;
  testID?: string;
}

export const FashionCollectionTemplate: React.FC<FashionCollectionTemplateProps> = ({
  spec,
  onSelectLook,
  onSelectProduct,
  testID = "fashion-collection-template",
}) => {
  return (
    <SafeAreaView testID={testID} style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Collection Hero */}
        <View style={styles.heroContainer}>
          <Image source={{ uri: spec.hero_image_uri }} style={styles.heroImage} resizeMode="cover" />
          <View style={styles.seasonBadge}>
            <Text style={styles.seasonText}>{spec.season.toUpperCase()}</Text>
          </View>
        </View>

        {/* Identity & Curator */}
        <View style={styles.metaContainer}>
          <Text style={styles.titleText}>{spec.name}</Text>
          <Text style={styles.curatorText}>Curated by {spec.curator}</Text>
          <Text style={styles.descText}>{spec.description}</Text>
        </View>

        {/* Featured Looks Rail */}
        {spec.looks && spec.looks.length > 0 && (
          <View style={styles.sectionContainer}>
            <Text style={styles.sectionHeading}>Featured Styled Looks ({spec.looks.length})</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.railContent}>
              {spec.looks.map((look) => (
                <TouchableOpacity
                  key={look.id}
                  testID={`${testID}-look-${look.id}`}
                  onPress={() => onSelectLook && onSelectLook(look.id)}
                  style={styles.cardWrapper}
                  accessibilityRole="button"
                >
                  <Image source={{ uri: look.primary_media_uri }} style={styles.lookImage} resizeMode="cover" />
                  <Text style={styles.cardTitle} numberOfLines={2}>{look.title}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}

        {/* Products in Collection */}
        {spec.products && spec.products.length > 0 && (
          <View style={styles.sectionContainer}>
            <Text style={styles.sectionHeading}>Wardrobe Pieces ({spec.products.length})</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.railContent}>
              {spec.products.map((prod) => (
                <TouchableOpacity
                  key={prod.id}
                  testID={`${testID}-prod-${prod.id}`}
                  onPress={() => onSelectProduct && onSelectProduct(prod.id)}
                  style={styles.cardWrapper}
                  accessibilityRole="button"
                >
                  <Image source={{ uri: prod.primary_media_uri }} style={styles.prodImage} resizeMode="cover" />
                  <Text style={styles.cardTitle} numberOfLines={2}>{prod.title}</Text>
                  {prod.price && <Text style={styles.priceText}>₹{prod.price.amount.toLocaleString()}</Text>}
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  scrollContent: {
    paddingBottom: 40,
  },
  heroContainer: {
    width: "100%",
    aspectRatio: 16 / 9,
    backgroundColor: "#f0f0f0",
    position: "relative",
  },
  heroImage: {
    width: "100%",
    height: "100%",
  },
  seasonBadge: {
    position: "absolute",
    top: 14,
    left: 16,
    backgroundColor: "rgba(0,0,0,0.75)",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  seasonText: {
    color: "#ffffff",
    fontSize: 11,
    fontWeight: "700",
  },
  metaContainer: {
    padding: 16,
  },
  titleText: {
    fontSize: 22,
    fontWeight: "800",
    color: "#111111",
    marginBottom: 4,
  },
  curatorText: {
    fontSize: 13,
    color: "#666666",
    fontWeight: "500",
    marginBottom: 10,
  },
  descText: {
    fontSize: 14,
    color: "#444444",
    lineHeight: 20,
  },
  sectionContainer: {
    marginTop: 16,
    borderTopWidth: 1,
    borderTopColor: "#eeeeee",
    paddingTop: 16,
  },
  sectionHeading: {
    fontSize: 16,
    fontWeight: "700",
    color: "#111111",
    paddingHorizontal: 16,
    marginBottom: 12,
  },
  railContent: {
    paddingHorizontal: 16,
    gap: 12,
  },
  cardWrapper: {
    width: 140,
  },
  lookImage: {
    width: 140,
    height: 185,
    borderRadius: 6,
    backgroundColor: "#f5f5f5",
  },
  prodImage: {
    width: 140,
    height: 185,
    borderRadius: 6,
    backgroundColor: "#f5f5f5",
  },
  cardTitle: {
    fontSize: 12,
    fontWeight: "600",
    color: "#111111",
    marginTop: 6,
  },
  priceText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#111111",
    marginTop: 2,
  },
});
