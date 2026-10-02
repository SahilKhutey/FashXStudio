/**
 * ResponsiveCard — Content priority adaptive card component (Section 14.27 & 14.28).
 *
 * Implements the P0-P3 metadata pruning model across compact, adaptive, and expanded layouts.
 */

import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { useResponsive } from '../hooks/useResponsive';

interface ResponsiveCardProps {
  imageUrl: string;
  title: string;
  primaryActionLabel: string;
  onPrimaryAction: () => void;
  brand?: string;
  priceFormatted?: string;
  availability?: string;
  secondarySpecs?: Record<string, string>;
  tags?: string[];
}

export const ResponsiveCard: React.FC<ResponsiveCardProps> = ({
  imageUrl,
  title,
  primaryActionLabel,
  onPrimaryAction,
  brand,
  priceFormatted,
  availability,
  secondarySpecs,
  tags,
}) => {
  const { isCompact, isAdaptive, isExpanded } = useResponsive();

  // P0: Always rendered (Image, Title, Primary Action)
  // P1: Brand, Price, Availability
  // P2: Secondary specs (rendered in adaptive & expanded)
  // P3: Tags (rendered only in expanded)

  const showSpecs = (isAdaptive || isExpanded) && secondarySpecs && Object.keys(secondarySpecs).length > 0;
  const showTags = isExpanded && tags && tags.length > 0;

  return (
    <View style={styles.cardContainer}>
      <Image source={{ uri: imageUrl }} style={styles.cardImage} resizeMode="cover" />

      <View style={styles.cardBody}>
        {/* P1: Brand */}
        {brand && <Text style={styles.brandText}>{brand}</Text>}

        {/* P0: Title */}
        <Text style={styles.titleText} numberOfLines={2}>
          {title}
        </Text>

        {/* P1: Price & Availability */}
        <View style={styles.priceRow}>
          {priceFormatted && <Text style={styles.priceText}>{priceFormatted}</Text>}
          {availability && (
            <Text
              style={[
                styles.availText,
                availability.toLowerCase().includes('in stock')
                  ? styles.availInStock
                  : styles.availNotice,
              ]}
            >
              {availability}
            </Text>
          )}
        </View>

        {/* P2: Secondary Specs (Adaptive & Expanded) */}
        {showSpecs && secondarySpecs && (
          <View style={styles.specsContainer}>
            {Object.entries(secondarySpecs).map(([k, v]) => (
              <Text key={k} style={styles.specItem}>
                <Text style={styles.specLabel}>{k}: </Text>
                {v}
              </Text>
            ))}
          </View>
        )}

        {/* P3: Tags (Expanded only) */}
        {showTags && tags && (
          <View style={styles.tagsContainer}>
            {tags.map((tag) => (
              <View key={tag} style={styles.tagBadge}>
                <Text style={styles.tagText}>{tag}</Text>
              </View>
            ))}
          </View>
        )}

        {/* P0: Primary Action */}
        <TouchableOpacity
          onPress={onPrimaryAction}
          style={styles.actionButton}
          accessibilityRole="button"
          accessibilityLabel={primaryActionLabel}
        >
          <Text style={styles.actionText}>{primaryActionLabel}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  cardContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    overflow: 'hidden',
    width: '100%',
  },
  cardImage: {
    width: '100%',
    aspectRatio: 3 / 4,
    backgroundColor: '#F3F4F6',
  },
  cardBody: {
    padding: 16,
    gap: 8,
  },
  brandText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  titleText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#111827',
  },
  priceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  priceText: {
    fontSize: 16,
    fontWeight: '800',
    color: '#111827',
  },
  availText: {
    fontSize: 12,
    fontWeight: '600',
  },
  availInStock: {
    color: '#059669',
  },
  availNotice: {
    color: '#D97706',
  },
  specsContainer: {
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
    gap: 4,
  },
  specItem: {
    fontSize: 12,
    color: '#4B5563',
  },
  specLabel: {
    fontWeight: '600',
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    paddingTop: 6,
  },
  tagBadge: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  tagText: {
    fontSize: 11,
    color: '#374151',
  },
  actionButton: {
    backgroundColor: '#111827',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 8,
    minHeight: 44, // WCAG 2.1 AA touch target
  },
  actionText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
});
