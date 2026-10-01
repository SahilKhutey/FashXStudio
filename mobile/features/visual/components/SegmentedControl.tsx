/**
 * FashXStudio — SegmentedControl Component (Phase 05 - Level 2 Core UI)
 *
 * Inline toggle control for switching between filters or views.
 * Supports pill/rounded styles, icon indicators, badge counters,
 * and accessible tablist role. Consumes Phase 02 surface and motion tokens.
 */

import React from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import {
  neutralPrimitives,
  radiusScale,
  spacingScale,
  typeScale,
} from '../tokens/primitives';
import {
  lightSemanticContent,
  lightSemanticSurfaces,
} from '../tokens/semantic';
import type { SegmentedControlProps } from './types';

export function SegmentedControl({
  options,
  selectedId,
  onSelect,
  size = 'md',
  isFullWidth = true,
  testID,
}: SegmentedControlProps) {
  const isSm = size === 'sm';

  return (
    <View
      style={[
        styles.container,
        isFullWidth && styles.fullWidth,
        isSm ? styles.container_sm : styles.container_md,
      ]}
      accessibilityRole="tablist"
      testID={testID}
    >
      {options.map((option) => {
        const isSelected = option.id === selectedId;

        return (
          <Pressable
            key={option.id}
            onPress={() => onSelect(option.id)}
            style={[
              styles.segment,
              isSm ? styles.segment_sm : styles.segment_md,
              isSelected && styles.segmentSelected,
            ]}
            accessibilityRole="tab"
            accessibilityState={{ selected: isSelected }}
            accessibilityLabel={option.label}
          >
            {option.icon && (
              <Text
                style={[
                  styles.icon,
                  {
                    color: isSelected
                      ? lightSemanticContent.primary
                      : lightSemanticContent.tertiary,
                  },
                ]}
              >
                {option.icon}
              </Text>
            )}

            <Text
              style={[
                styles.label,
                isSm ? styles.label_sm : styles.label_md,
                isSelected ? styles.labelSelected : styles.labelUnselected,
              ]}
              numberOfLines={1}
            >
              {option.label}
            </Text>

            {option.badge && (
              <View
                style={[
                  styles.badge,
                  isSelected ? styles.badgeSelected : styles.badgeUnselected,
                ]}
              >
                <Text
                  style={[
                    styles.badgeText,
                    isSelected
                      ? styles.badgeTextSelected
                      : styles.badgeTextUnselected,
                  ]}
                >
                  {option.badge}
                </Text>
              </View>
            )}
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    backgroundColor: lightSemanticSurfaces.secondary,
    borderRadius: radiusScale.md,
    padding: 3,
  },
  fullWidth: {
    width: '100%',
  },
  container_sm: {
    minHeight: 36,
  },
  container_md: {
    minHeight: 44, // WCAG touch target
  },
  segment: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radiusScale.sm,
  },
  segment_sm: {
    paddingVertical: 4,
    paddingHorizontal: spacingScale.space2,
  },
  segment_md: {
    paddingVertical: 8,
    paddingHorizontal: spacingScale.space3,
  },
  segmentSelected: {
    backgroundColor: lightSemanticSurfaces.primary,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 2,
    elevation: 2,
  },
  icon: {
    fontSize: 14,
    marginRight: 6,
  },
  label: {
    textAlign: 'center',
  },
  label_sm: {
    fontSize: typeScale.labelS.fontSize,
  },
  label_md: {
    fontSize: typeScale.labelM.fontSize,
  },
  labelSelected: {
    fontWeight: '700',
    color: lightSemanticContent.primary,
  },
  labelUnselected: {
    fontWeight: '500',
    color: lightSemanticContent.secondary,
  },
  badge: {
    marginLeft: 6,
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: radiusScale.full,
  },
  badgeSelected: {
    backgroundColor: neutralPrimitives.neutral900,
  },
  badgeUnselected: {
    backgroundColor: neutralPrimitives.neutral300,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '700',
  },
  badgeTextSelected: {
    color: neutralPrimitives.neutral0,
  },
  badgeTextUnselected: {
    color: neutralPrimitives.neutral700,
  },
});
