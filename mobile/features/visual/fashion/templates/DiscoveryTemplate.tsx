/**
 * FashXStudio — DiscoveryTemplate Component (Phase 06 - Content Template)
 *
 * Mixed-content discovery surface coordinating Featured Story,
 * Trending topics, Curated Collections, AI Recommendations, and Brands (Section 6.40).
 */

import React from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import {
  spacingScale,
  typeScale,
} from '../../tokens/primitives';
import { lightSemanticContent } from '../../tokens/semantic';
import { BrandCard } from '../brand/BrandCard';
import { CollectionCard } from '../collection/CollectionCard';
import { StoryCard } from '../editorial/StoryCard';
import { RecommendationCard } from '../recommendation/RecommendationCard';
import { TrendCard } from '../trend/TrendCard';
import type {
  BrandItem,
  CollectionItem,
  FashionStory,
  RecommendationItem,
  TrendItem,
} from '../types';

export interface DiscoveryTemplateProps {
  featuredStory?: FashionStory;
  trendingItems?: TrendItem[];
  curatedCollections?: CollectionItem[];
  recommendedProducts?: RecommendationItem[];
  featuredBrands?: BrandItem[];
  onStoryPress?: (story: FashionStory) => void;
  onTrendPress?: (trend: TrendItem) => void;
  onCollectionPress?: (collection: CollectionItem) => void;
  onRecommendationPress?: (rec: RecommendationItem) => void;
  onBrandPress?: (brand: BrandItem) => void;
  testID?: string;
}

export function DiscoveryTemplate({
  featuredStory,
  trendingItems = [],
  curatedCollections = [],
  recommendedProducts = [],
  featuredBrands = [],
  onStoryPress,
  onTrendPress,
  onCollectionPress,
  onRecommendationPress,
  onBrandPress,
  testID,
}: DiscoveryTemplateProps) {
  return (
    <ScrollView style={styles.container} testID={testID}>
      {/* Featured Editorial Story */}
      {featuredStory && (
        <View style={styles.section}>
          <Text style={styles.sectionHeader}>Featured Story</Text>
          <StoryCard
            story={featuredStory}
            onPress={() => onStoryPress && onStoryPress(featuredStory)}
          />
        </View>
      )}

      {/* AI Recommendations */}
      {recommendedProducts.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionHeader}>Personalized for You</Text>
          {recommendedProducts.map((rec) => (
            <RecommendationCard
              key={rec.id}
              recommendation={rec}
              onPress={() => onRecommendationPress && onRecommendationPress(rec)}
            />
          ))}
        </View>
      )}

      {/* Trending Topics */}
      {trendingItems.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionHeader}>Trending Now</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.horizontalRow}>
            {trendingItems.map((trend) => (
              <View key={trend.id} style={styles.carouselItem}>
                <TrendCard
                  trend={trend}
                  onPress={() => onTrendPress && onTrendPress(trend)}
                />
              </View>
            ))}
          </ScrollView>
        </View>
      )}

      {/* Curated Collections */}
      {curatedCollections.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionHeader}>Curated Collections</Text>
          {curatedCollections.map((coll) => (
            <CollectionCard
              key={coll.id}
              collection={coll}
              onPress={() => onCollectionPress && onCollectionPress(coll)}
            />
          ))}
        </View>
      )}

      {/* Featured Brands */}
      {featuredBrands.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionHeader}>Featured Brands</Text>
          {featuredBrands.map((brand) => (
            <BrandCard
              key={brand.id}
              brand={brand}
              onPress={() => onBrandPress && onBrandPress(brand)}
            />
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: spacingScale.space4,
    paddingTop: spacingScale.space3,
  },
  section: {
    marginBottom: spacingScale.space6,
  },
  sectionHeader: {
    fontSize: typeScale.headingM.fontSize,
    lineHeight: typeScale.headingM.lineHeight,
    fontWeight: '700',
    color: lightSemanticContent.primary,
    marginBottom: spacingScale.space3,
  },
  horizontalRow: {
    flexDirection: 'row',
  },
  carouselItem: {
    width: 220,
    marginRight: spacingScale.space3,
  },
});
