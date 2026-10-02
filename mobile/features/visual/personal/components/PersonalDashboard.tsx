import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Image } from "react-native";
import { PersonalDashboardTemplateSpecContract } from "../types";
import { PersonalSection } from "./PersonalSection";
import { SavedProductCard } from "./SavedProductCard";
import { SavedLookCard } from "./SavedLookCard";
import { RecentItem } from "./RecentItem";

interface PersonalDashboardProps {
  dashboard: PersonalDashboardTemplateSpecContract;
  onNavigate?: (screen: string, params?: Record<string, any>) => void;
  onRetryModule?: (moduleKey: string) => void;
  testID?: string;
}

export const PersonalDashboard: React.FC<PersonalDashboardProps> = ({
  dashboard,
  onNavigate,
  onRetryModule,
  testID = "personal-dashboard-view",
}) => {
  return (
    <ScrollView testID={testID} style={styles.container}>
      <View style={styles.welcomeBanner}>
        <Text style={styles.welcomeTitle}>{dashboard.welcome_title}</Text>
        <Text style={styles.welcomeSubtitle}>Your Curated Fashion Operating Space</Text>
      </View>

      {/* 1. Continue Exploring */}
      <PersonalSection
        title="Continue Exploring"
        state={dashboard.module_states["continue_exploring"]}
        testID="section-continue-exploring"
      >
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.horizontalScroll}>
          {dashboard.continue_exploring.map((item) => (
            <TouchableOpacity
              key={item.id}
              testID={`continue-card-${item.id}`}
              style={styles.continueCard}
              onPress={() => onNavigate && onNavigate(item.type, { id: item.id })}
              accessibilityRole="button"
              accessibilityLabel={`${item.title}, ${item.subtitle}`}
            >
              <View style={styles.continueImagePlaceholder}>
                <Text style={styles.continueBadge}>{item.type.toUpperCase()}</Text>
              </View>
              <Text style={styles.continueTitle} numberOfLines={1}>
                {item.title}
              </Text>
              <Text style={styles.continueSubtitle} numberOfLines={1}>
                {item.subtitle}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </PersonalSection>

      {/* 2. Your Saved Items */}
      <PersonalSection
        title="Your Saved Items"
        actionText="View All Saves"
        onActionPress={() => onNavigate && onNavigate("saved_products")}
        state={dashboard.module_states["saved_preview"]}
        testID="section-saved-items"
      >
        <View style={styles.savedPreviewGrid}>
          {dashboard.saved_preview.map((item) => (
            <View key={item.id} style={styles.savedPreviewCard} testID={`saved-preview-${item.id}`}>
              <Text style={styles.savedTypeBadge}>{item.type.toUpperCase()}</Text>
              <Text style={styles.savedTitle} numberOfLines={1}>
                {item.title}
              </Text>
              {item.brand && <Text style={styles.savedBrand}>{item.brand}</Text>}
              {item.price && <Text style={styles.savedPrice}>${item.price.toFixed(2)}</Text>}
            </View>
          ))}
        </View>
      </PersonalSection>

      {/* 3. Recommended For You */}
      <PersonalSection
        title="Recommended For You"
        state={dashboard.module_states["recommendations"]}
        errorMessage="Recommendations unavailable. General discovery remains active."
        onRetry={() => onRetryModule && onRetryModule("recommendations")}
        testID="section-recommendations"
      >
        {dashboard.recommended_products.length > 0 && (
          <View style={styles.productsRail}>
            {dashboard.recommended_products.map((p) => (
              <SavedProductCard key={p.id} product={p} onView={(id) => onNavigate && onNavigate("product", { id })} />
            ))}
          </View>
        )}
      </PersonalSection>

      {/* 4. Recently Viewed */}
      <PersonalSection
        title="Recently Viewed"
        actionText="View History"
        onActionPress={() => onNavigate && onNavigate("recently_viewed")}
        state={dashboard.module_states["recently_viewed"]}
        testID="section-recently-viewed"
      >
        {dashboard.recently_viewed.map((act) => (
          <RecentItem
            key={`${act.entity_id}-${act.timestamp}`}
            activity={act}
            onOpen={(id, type) => onNavigate && onNavigate(type, { id })}
          />
        ))}
      </PersonalSection>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F2F2F7",
  },
  welcomeBanner: {
    padding: 20,
    backgroundColor: "#FFFFFF",
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: "#E5E5EA",
  },
  welcomeTitle: {
    fontSize: 22,
    fontWeight: "700",
    color: "#1C1C1E",
    letterSpacing: -0.4,
    marginBottom: 4,
  },
  welcomeSubtitle: {
    fontSize: 13,
    color: "#8E8E93",
  },
  horizontalScroll: {
    paddingVertical: 8,
  },
  continueCard: {
    width: 140,
    marginRight: 12,
    backgroundColor: "#F2F2F7",
    borderRadius: 8,
    padding: 8,
  },
  continueImagePlaceholder: {
    height: 80,
    backgroundColor: "#E5E5EA",
    borderRadius: 6,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 8,
  },
  continueBadge: {
    fontSize: 9,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 0.5,
  },
  continueTitle: {
    fontSize: 12,
    fontWeight: "600",
    color: "#1C1C1E",
  },
  continueSubtitle: {
    fontSize: 11,
    color: "#636366",
    marginTop: 2,
  },
  savedPreviewGrid: {
    flexDirection: "row",
    gap: 8,
  },
  savedPreviewCard: {
    flex: 1,
    backgroundColor: "#F2F2F7",
    padding: 10,
    borderRadius: 6,
  },
  savedTypeBadge: {
    fontSize: 9,
    fontWeight: "700",
    color: "#5856D6",
    marginBottom: 4,
  },
  savedTitle: {
    fontSize: 12,
    fontWeight: "600",
    color: "#1C1C1E",
  },
  savedBrand: {
    fontSize: 10,
    color: "#8E8E93",
    marginTop: 2,
  },
  savedPrice: {
    fontSize: 11,
    fontWeight: "700",
    color: "#1C1C1E",
    marginTop: 4,
  },
  productsRail: {
    marginTop: 8,
  },
});
