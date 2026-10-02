import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Image } from "react-native";
import { StyleHomeTemplateSpecContract } from "../types";
import { SavedLookCard } from "../components/SavedLookCard";

interface StyleHomeTemplateProps {
  data: StyleHomeTemplateSpecContract;
  onPressFeatured?: (contentId: string) => void;
  onPressStyle?: (styleId: string) => void;
  onPressLook?: (lookId: string) => void;
  onCreateNewOutfit?: () => void;
  onOpenSavedLook?: (lookId: string) => void;
  testID?: string;
}

export const StyleHomeTemplate: React.FC<StyleHomeTemplateProps> = ({
  data,
  onPressFeatured,
  onPressStyle,
  onPressLook,
  onCreateNewOutfit,
  onOpenSavedLook,
  testID = "style-home-screen",
}) => {
  return (
    <ScrollView
      testID={testID}
      style={styles.container}
      showsVerticalScrollIndicator={false}
      contentContainerStyle={styles.content}
    >
      {/* Top Banner / Create CTA */}
      <View style={styles.topCtaBanner}>
        <View style={styles.ctaTextContainer}>
          <Text style={styles.ctaTitle}>Interactive Styling Studio</Text>
          <Text style={styles.ctaSubtitle}>Mix, match, and curate your custom looks</Text>
        </View>
        <TouchableOpacity
          testID="create-outfit-cta"
          style={styles.ctaButton}
          onPress={onCreateNewOutfit}
        >
          <Text style={styles.ctaButtonText}>+ New Outfit</Text>
        </TouchableOpacity>
      </View>

      {/* Featured Style Hero */}
      <View style={styles.section}>
        <Text style={styles.sectionHeader}>FEATURED AESTHETIC</Text>
        <TouchableOpacity
          testID="featured-style-hero"
          activeOpacity={0.9}
          onPress={() => onPressFeatured?.(data.featured_style.id)}
          style={styles.heroCard}
        >
          {data.featured_style.media?.[0]?.uri && (
            <Image
              source={{ uri: data.featured_style.media[0].uri }}
              style={styles.heroImage}
              resizeMode="cover"
            />
          )}
          <View style={styles.heroOverlay}>
            <Text style={styles.heroTitle}>{data.featured_style.title}</Text>
            {data.featured_style.subtitle && (
              <Text style={styles.heroSubtitle}>{data.featured_style.subtitle}</Text>
            )}
          </View>
        </TouchableOpacity>
      </View>

      {/* Popular Styles Rail */}
      {data.popular_styles.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionHeader}>TRENDING STYLES</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.railContent}>
            {data.popular_styles.map((style) => (
              <TouchableOpacity
                key={style.id}
                testID={`style-card-${style.id}`}
                activeOpacity={0.8}
                onPress={() => onPressStyle?.(style.id)}
                style={styles.styleThumbCard}
              >
                {style.media?.[0]?.uri && (
                  <Image
                    source={{ uri: style.media[0].uri }}
                    style={styles.styleThumbImage}
                    resizeMode="cover"
                  />
                )}
                <Text style={styles.styleThumbTitle} numberOfLines={1}>
                  {style.title}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}

      {/* Recommended Looks Rail */}
      {data.recommended_looks.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionHeader}>CURATED LOOKS FOR YOU</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.railContent}>
            {data.recommended_looks.map((look) => (
              <TouchableOpacity
                key={look.id}
                testID={`look-card-${look.id}`}
                activeOpacity={0.8}
                onPress={() => onPressLook?.(look.id)}
                style={styles.lookCard}
              >
                {look.media?.[0]?.uri && (
                  <Image
                    source={{ uri: look.media[0].uri }}
                    style={styles.lookImage}
                    resizeMode="cover"
                  />
                )}
                <View style={styles.lookInfo}>
                  <Text style={styles.lookTitle} numberOfLines={1}>
                    {look.title}
                  </Text>
                  {look.subtitle && (
                    <Text style={styles.lookSubtitle} numberOfLines={1}>
                      {look.subtitle}
                    </Text>
                  )}
                </View>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}

      {/* Saved Looks Preview */}
      {data.saved_looks_preview.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionHeader}>YOUR RECENT SAVED LOOKS</Text>
          {data.saved_looks_preview.map((savedLook) => (
            <SavedLookCard
              key={savedLook.id}
              look={savedLook}
              onPressLook={onOpenSavedLook}
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
  topCtaBanner: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "#111111",
    padding: 16,
  },
  ctaTextContainer: {
    flex: 1,
    marginRight: 12,
  },
  ctaTitle: {
    color: "#ffffff",
    fontSize: 16,
    fontWeight: "700",
  },
  ctaSubtitle: {
    color: "#aaaaaa",
    fontSize: 12,
    marginTop: 2,
  },
  ctaButton: {
    backgroundColor: "#ffffff",
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 6,
  },
  ctaButtonText: {
    color: "#111111",
    fontSize: 13,
    fontWeight: "700",
  },
  section: {
    marginTop: 20,
    paddingHorizontal: 16,
  },
  sectionHeader: {
    fontSize: 12,
    fontWeight: "800",
    color: "#6b7280",
    letterSpacing: 1,
    marginBottom: 12,
  },
  heroCard: {
    borderRadius: 12,
    overflow: "hidden",
    height: 220,
    backgroundColor: "#1e1e1e",
    position: "relative",
  },
  heroImage: {
    width: "100%",
    height: "100%",
    opacity: 0.85,
  },
  heroOverlay: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    padding: 16,
    backgroundColor: "rgba(0, 0, 0, 0.4)",
  },
  heroTitle: {
    color: "#ffffff",
    fontSize: 22,
    fontWeight: "800",
  },
  heroSubtitle: {
    color: "#f3f4f6",
    fontSize: 13,
    marginTop: 4,
  },
  railContent: {
    gap: 12,
  },
  styleThumbCard: {
    width: 110,
    alignItems: "center",
  },
  styleThumbImage: {
    width: 110,
    height: 110,
    borderRadius: 55,
    backgroundColor: "#f3f4f6",
  },
  styleThumbTitle: {
    fontSize: 12,
    fontWeight: "600",
    color: "#111111",
    marginTop: 6,
    textAlign: "center",
  },
  lookCard: {
    width: 160,
    backgroundColor: "#ffffff",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#e5e7eb",
    overflow: "hidden",
  },
  lookImage: {
    width: 160,
    height: 180,
    backgroundColor: "#f3f4f6",
  },
  lookInfo: {
    padding: 8,
  },
  lookTitle: {
    fontSize: 13,
    fontWeight: "700",
    color: "#111111",
  },
  lookSubtitle: {
    fontSize: 11,
    color: "#6b7280",
    marginTop: 2,
  },
});
