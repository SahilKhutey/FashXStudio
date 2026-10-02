import React from "react";
import { View, Text, Image, StyleSheet, ScrollView, SafeAreaView, TouchableOpacity } from "react-native";
import { FashionStoryDetailTemplateSpecContract } from "../types";

interface FashionStoryTemplateProps {
  spec: FashionStoryDetailTemplateSpecContract;
  onSelectLook?: (lookId: string) => void;
  onSelectProduct?: (productId: string) => void;
  testID?: string;
}

export const FashionStoryTemplate: React.FC<FashionStoryTemplateProps> = ({
  spec,
  onSelectLook,
  onSelectProduct,
  testID = "fashion-story-template",
}) => {
  return (
    <SafeAreaView testID={testID} style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Hero Media (Section 9.34) */}
        <View style={styles.heroContainer}>
          <Image
            source={{ uri: spec.hero_media_uri }}
            style={styles.heroImage}
            resizeMode="cover"
          />
          <View style={styles.categoryBadge}>
            <Text style={styles.categoryText}>{spec.category.toUpperCase()}</Text>
          </View>
        </View>

        {/* Story Metadata */}
        <View style={styles.headerContainer}>
          <Text style={styles.titleText}>{spec.title}</Text>
          <Text style={styles.subtitleText}>{spec.subtitle}</Text>
          <View style={styles.authorRow}>
            <Text style={styles.authorText}>By {spec.author}</Text>
            <Text style={styles.dateText}> • {spec.published_date}</Text>
          </View>
        </View>

        {/* Main Editorial Content */}
        <View style={styles.bodyContainer}>
          <Text style={styles.bodyText}>{spec.content_markdown}</Text>
        </View>

        {/* Related Styled Looks */}
        {spec.related_looks && spec.related_looks.length > 0 && (
          <View style={styles.relatedSection}>
            <Text style={styles.relatedHeading}>Featured Styled Looks</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.railContent}>
              {spec.related_looks.map((look) => (
                <TouchableOpacity
                  key={look.id}
                  testID={`${testID}-look-${look.id}`}
                  onPress={() => onSelectLook && onSelectLook(look.id)}
                  style={styles.lookCard}
                  accessibilityRole="button"
                >
                  <Image source={{ uri: look.primary_media_uri }} style={styles.lookImage} resizeMode="cover" />
                  <Text style={styles.lookTitle} numberOfLines={2}>{look.title}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}

        {/* Related Products */}
        {spec.related_products && spec.related_products.length > 0 && (
          <View style={styles.relatedSection}>
            <Text style={styles.relatedHeading}>Mentioned In This Story</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.railContent}>
              {spec.related_products.map((prod) => (
                <TouchableOpacity
                  key={prod.id}
                  testID={`${testID}-prod-${prod.id}`}
                  onPress={() => onSelectProduct && onSelectProduct(prod.id)}
                  style={styles.prodCard}
                  accessibilityRole="button"
                >
                  <Image source={{ uri: prod.primary_media_uri }} style={styles.prodImage} resizeMode="cover" />
                  <Text style={styles.prodTitle} numberOfLines={2}>{prod.title}</Text>
                  {prod.price && <Text style={styles.prodPrice}>₹{prod.price.amount.toLocaleString()}</Text>}
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
    backgroundColor: "#f5f5f5",
    position: "relative",
  },
  heroImage: {
    width: "100%",
    height: "100%",
  },
  categoryBadge: {
    position: "absolute",
    top: 14,
    left: 16,
    backgroundColor: "rgba(0,0,0,0.75)",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  categoryText: {
    color: "#ffffff",
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  headerContainer: {
    paddingHorizontal: 16,
    paddingVertical: 18,
  },
  titleText: {
    fontSize: 24,
    fontWeight: "800",
    color: "#111111",
    lineHeight: 32,
    marginBottom: 8,
  },
  subtitleText: {
    fontSize: 16,
    color: "#555555",
    lineHeight: 22,
    marginBottom: 12,
  },
  authorRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  authorText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#333333",
  },
  dateText: {
    fontSize: 13,
    color: "#777777",
  },
  bodyContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  bodyText: {
    fontSize: 15,
    color: "#333333",
    lineHeight: 24,
  },
  relatedSection: {
    marginTop: 20,
    borderTopWidth: 1,
    borderTopColor: "#eeeeee",
    paddingTop: 16,
  },
  relatedHeading: {
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
  lookCard: {
    width: 150,
  },
  lookImage: {
    width: 150,
    height: 200,
    borderRadius: 6,
    backgroundColor: "#f5f5f5",
  },
  lookTitle: {
    fontSize: 12,
    fontWeight: "600",
    color: "#111111",
    marginTop: 6,
  },
  prodCard: {
    width: 130,
  },
  prodImage: {
    width: 130,
    height: 170,
    borderRadius: 6,
    backgroundColor: "#f5f5f5",
  },
  prodTitle: {
    fontSize: 12,
    fontWeight: "600",
    color: "#111111",
    marginTop: 6,
  },
  prodPrice: {
    fontSize: 12,
    fontWeight: "700",
    color: "#111111",
    marginTop: 2,
  },
});
