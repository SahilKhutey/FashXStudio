/**
 * FashXStudio — FilterBar Component (Phase 05 - L3 Composite)
 *
 * Faceting toolbar displaying active filter chips, filter tally,
 * clear all trigger, and filter trigger (Section 5.48 & 5.50).
 */

import React from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import {
  radiusScale,
  spacingScale,
  typeScale,
} from '../tokens/primitives';
import {
  lightSemanticBorders,
  lightSemanticContent,
} from '../tokens/semantic';
import { Chip } from './Chip';
import type { FilterBarProps } from './types';

export function FilterBar({
  activeChips,
  onRemoveChip,
  onClearAll,
  filterCount = 0,
  onOpenFilters,
  testID,
}: FilterBarProps) {
  return (
    <View style={styles.container} testID={testID}>
      {onOpenFilters && (
        <Pressable
          onPress={onOpenFilters}
          style={styles.filterButton}
          accessibilityRole="button"
          accessibilityLabel={`Filters${filterCount > 0 ? `, ${filterCount} active` : ''}`}
        >
          <Text style={styles.filterText}>Filters</Text>
          {filterCount > 0 && (
            <View style={styles.tallyBadge}>
              <Text style={styles.tallyText}>{filterCount}</Text>
            </View>
          )}
        </Pressable>
      )}

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {activeChips.map((chip) => (
          <Chip
            key={chip.id}
            label={chip.label}
            isSelected
            isRemovable
            onRemove={() => onRemoveChip(chip.id)}
          />
        ))}

        {activeChips.length > 1 && onClearAll && (
          <Pressable
            onPress={onClearAll}
            style={styles.clearAllButton}
            accessibilityRole="button"
            accessibilityLabel="Clear all active filters"
          >
            <Text style={styles.clearAllText}>Clear All</Text>
          </Pressable>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacingScale.space2,
    borderBottomWidth: 1,
    borderBottomColor: lightSemanticBorders.subtle,
    width: '100%',
  },
  filterButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacingScale.space3,
    paddingVertical: 6,
    borderRadius: radiusScale.sm,
    borderWidth: 1,
    borderColor: lightSemanticBorders.default,
    marginRight: spacingScale.space2,
    minHeight: 36,
  },
  filterText: {
    fontSize: typeScale.labelS.fontSize,
    fontWeight: '600',
    color: lightSemanticContent.primary,
  },
  tallyBadge: {
    backgroundColor: '#000',
    borderRadius: radiusScale.full,
    paddingHorizontal: 5,
    paddingVertical: 1,
    marginLeft: 6,
  },
  tallyText: {
    color: '#FFF',
    fontSize: 9,
    fontWeight: '700',
  },
  scrollContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacingScale.space2,
    paddingRight: spacingScale.space4,
  },
  clearAllButton: {
    paddingHorizontal: spacingScale.space2,
    minHeight: 36,
    justifyContent: 'center',
  },
  clearAllText: {
    fontSize: typeScale.labelS.fontSize,
    color: lightSemanticContent.tertiary,
    fontWeight: '600',
    textDecorationLine: 'underline',
  },
});
