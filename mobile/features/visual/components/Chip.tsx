/**
 * FashXStudio — Chip Component (Phase 05 - L2 Core UI)
 *
 * Filter facet and attribute chip supporting selection toggle and
 * dismissible removal (Section 5.24).
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
  lightSemanticActions,
  lightSemanticBorders,
  lightSemanticContent,
  lightSemanticSurfaces,
} from '../tokens/semantic';
import type { ChipProps } from './types';

export function Chip({
  label,
  isSelected = false,
  isRemovable = false,
  onPress,
  onRemove,
  icon,
  testID,
}: ChipProps) {
  return (
    <Pressable
      onPress={onPress}
      style={[
        styles.chip,
        isSelected ? styles.chipSelected : styles.chipUnselected,
      ]}
      accessibilityRole="button"
      accessibilityState={{ selected: isSelected }}
      accessibilityLabel={label}
      testID={testID}
    >
      {icon && <Text style={styles.icon}>{icon}</Text>}

      <Text
        style={[
          styles.label,
          isSelected ? styles.labelSelected : styles.labelUnselected,
        ]}
        numberOfLines={1}
      >
        {label}
      </Text>

      {isRemovable && onRemove && (
        <Pressable
          onPress={onRemove}
          style={styles.removeTouch}
          accessibilityRole="button"
          accessibilityLabel={`Remove filter ${label}`}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        >
          <Text
            style={[
              styles.removeText,
              isSelected ? styles.labelSelected : styles.labelUnselected,
            ]}
          >
            ✕
          </Text>
        </Pressable>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacingScale.space3,
    paddingVertical: 6,
    borderRadius: radiusScale.full,
    borderWidth: 1,
    minHeight: 36,
  },
  chipUnselected: {
    backgroundColor: lightSemanticSurfaces.secondary,
    borderColor: lightSemanticBorders.default,
  },
  chipSelected: {
    backgroundColor: lightSemanticActions.primary,
    borderColor: lightSemanticActions.primary,
  },
  icon: {
    fontSize: 14,
    marginRight: 6,
  },
  label: {
    fontSize: typeScale.labelS.fontSize,
    lineHeight: typeScale.labelS.lineHeight,
  },
  labelUnselected: {
    color: lightSemanticContent.primary,
    fontWeight: '500',
  },
  labelSelected: {
    color: neutralPrimitives.neutral0,
    fontWeight: '700',
  },
  removeTouch: {
    marginLeft: 6,
    padding: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  removeText: {
    fontSize: 12,
    fontWeight: '700',
  },
});
